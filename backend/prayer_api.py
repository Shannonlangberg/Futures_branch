# prayer_api.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Person, CareCase, PrayerLink, PrayerSubmission
from datetime import datetime
import logging
import sqlite3
import uuid

logger = logging.getLogger(__name__)

prayer_bp = Blueprint('prayer', __name__, url_prefix='/api/prayer')

def get_db_path():
    """Get the database path from Flask app config"""
    from flask import current_app
    import os
    try:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_path = db_uri.replace('sqlite:///', '').replace('sqlite:////', '')
        if not os.path.isabs(db_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            instance_path = os.path.join(backend_dir, 'instance', 'futures_link.db')
            db_path = instance_path if os.path.exists(instance_path) else os.path.join(backend_dir, 'futures_link.db')
        return db_path
    except Exception as e:
        logger.warning(f"Error getting db path: {e}, using fallback")
        return 'instance/futures_link.db'

def get_campus_pastor(campus):
    """Find the campus pastor for a given campus"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, email
            FROM users
            WHERE role = 'campus_pastor' 
            AND campus = ?
            AND active = 1
            LIMIT 1
        ''', (campus,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'email': row[3]
            }
        return None
    except Exception as e:
        logger.error(f"Error finding campus pastor for {campus}: {e}")
        return None

@prayer_bp.route('/requests', methods=['POST'])
def create_prayer_request():
    """Create a new prayer request - logs to Heartbeat care signals and routes to campus pastor"""
    try:
        logger.info(f"Prayer request endpoint called")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        email = data.get('email')
        person_id = data.get('person_id')  # NEW: Accept person_id from mobile app
        request_text = data.get('request')
        campus = data.get('campus', 'paradise')  # Get campus from request, default to paradise
        
        logger.info(f"📥 PRAYER REQUEST RECEIVED:")
        logger.info(f"   - Email: {email}")
        logger.info(f"   - Person ID: {person_id}")
        logger.info(f"   - Campus: {campus}")
        logger.info(f"   - Request length: {len(request_text) if request_text else 0} chars")
        
        if not email or not request_text:
            logger.warning(f"Missing email or request text")
            return jsonify({'error': 'Email and request text required'}), 400
        
        # Find person - CRITICAL: If person_id provided, USE IT and don't fall back to email
        person = None
        if person_id:
            # Use person_id directly if provided (most reliable - from logged-in user)
            logger.info(f"🔍 STEP 1: Looking up person by person_id: {person_id}")
            person = Person.query.filter_by(id=person_id, is_active=True).first()
            if person:
                logger.info(f"✅ FOUND PERSON BY ID: {person.full_name} ({person.id})")
                logger.info(f"   - Email: {person.email}")
                logger.info(f"   - Campus: {person.campus}")
                logger.info(f"   - Is Active: {person.is_active}")
                # Verify email matches (for debugging, but still use this person)
                if person.email and person.email.lower() != email.lower():
                    logger.warning(f"⚠️ Email mismatch: Person has '{person.email}' but request has '{email}'")
                    logger.warning(f"   Using Person {person.id} anyway (person_id takes priority)")
            else:
                logger.error(f"❌ Person ID {person_id} NOT FOUND in database!")
                logger.error(f"   This is a critical error - person_id should always exist after login")
                return jsonify({'error': f'Person record not found for ID: {person_id}. Please log out and log back in.'}), 404
        
        if not person:
            # Fallback: Look up by email AND campus to ensure we get the right person
            logger.info(f"Looking up person by email+campus: {email}, campus: {campus}")
            person = Person.query.filter_by(email=email, campus=campus, is_active=True).first()
            
            if not person:
                # Try without campus filter (in case campus changed)
                logger.info(f"Person not found with campus filter, trying without: {email}")
                person = Person.query.filter_by(email=email, is_active=True).first()
        
        if not person:
            # Auto-create person (like giving endpoint does)
            logger.info(f"Person not found, creating new person for: {email} at {campus}")
            try:
                import uuid
                person_id = f"user_{uuid.uuid4().hex[:12]}"
                name_from_email = email.split('@')[0].replace('.', ' ').title()
                
                person = Person(
                    id=person_id,
                    full_name=name_from_email,
                    email=email,
                    campus=campus,  # Use campus from request
                    is_active=True
                )
                db.session.add(person)
                db.session.flush()
                logger.info(f"✅ Created new person: {person.id} - {person.full_name} at {campus}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ Error creating person: {e}", exc_info=True)
                return jsonify({'error': 'Failed to create person record'}), 500
        else:
            # Update person's campus if it has changed (use campus from request, not person record)
            if person.campus != campus and campus and campus != 'paradise' and campus != 'all_campuses':
                logger.info(f"📝 Updating person {email} campus from '{person.campus}' to '{campus}'")
                person.campus = campus
                db.session.flush()
                logger.info(f"✅ Updated person campus to: {person.campus}")
        
        # CRITICAL: Use campus from request data (not person.campus) to ensure correct linking
        final_campus = campus if campus and campus != 'paradise' and campus != 'all_campuses' else (person.campus if person.campus != 'all_campuses' else 'copper_coast')
        
        # If person campus is wrong, fix it now
        if person.campus == 'all_campuses' and final_campus != 'all_campuses':
            logger.info(f"🔧 FIXING: Person campus is 'all_campuses', changing to '{final_campus}'")
            person.campus = final_campus
            db.session.flush()
        
        logger.info(f"📍 FINAL CAMPUS DECISION: request_campus={campus}, person.campus={person.campus}, using={final_campus}")
        
        # Find campus pastor for routing
        campus_pastor = None
        pastor_info = None
        if final_campus and final_campus != 'all_campuses':
            campus_pastor = get_campus_pastor(final_campus)
            if campus_pastor:
                pastor_info = f"Routed to {campus_pastor['full_name']} ({campus_pastor['email']}) - {final_campus} campus pastor"
                logger.info(f"Prayer request from {email} ({final_campus}) - {pastor_info}")
            else:
                logger.warning(f"No campus pastor found for {final_campus} campus")
        
        # Create BOTH PrayerSubmission (for Prayer & Praise page) AND CareCase (for Heartbeat)
        try:
            # Include routing info in details
            details_with_routing = request_text
            if pastor_info:
                details_with_routing += f"\n\n---\n{pastor_info}"
            
            # 1. Create PrayerSubmission record (for Prayer & Praise page) - USE FINAL_CAMPUS
            logger.info(f"Creating PrayerSubmission for {email} with campus: {final_campus}")
            prayer_submission = PrayerSubmission(
                person_id=person.id,
                email=email,
                name=person.full_name,
                submission_type='prayer',
                content=request_text,
                campus=final_campus,  # USE REQUEST CAMPUS, not person.campus
                source='app',
                status='approved',  # Auto-approve from app
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(prayer_submission)
            logger.info(f"PrayerSubmission added")
            
            # 2. Create CareCase record (for Heartbeat profile)
            logger.info(f"Creating CareCase for {email}")
            care_case = CareCase(
                person_id=person.id,
                type='prayer_request',
                status='open',
                priority='medium',
                summary=request_text[:500],  # First 500 chars as summary
                details=details_with_routing,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            logger.info(f"CareCase added")
            
            # Commit both records
            logger.info(f"Committing both PrayerSubmission and CareCase...")
            db.session.commit()
            logger.info(f"✅ COMMIT SUCCESSFUL!")
            logger.info(f"   - PrayerSubmission ID: {prayer_submission.id}, Campus: {prayer_submission.campus}")
            logger.info(f"   - CareCase ID: {care_case.id}, Person ID: {care_case.person_id}")
            logger.info(f"   - Person: {person.full_name} ({person.id}), Person Campus: {person.campus}")
            logger.info(f"   - Request Campus: {campus}, Final Campus Used: {final_campus}")
            
            response_message = 'Prayer request received'
            if pastor_info:
                response_message += f'. Your campus pastor has been notified.'
            
            return jsonify({
                'success': True,
                'message': response_message,
                'prayer_submission_id': prayer_submission.id,
                'care_case_id': care_case.id,
                'routed_to': campus_pastor['email'] if campus_pastor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating prayer records: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Failed to create prayer request'}), 500
        
    except Exception as e:
        logger.error(f"❌ FATAL: Error creating prayer request: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@prayer_bp.route('/praise', methods=['POST'])
def create_praise_report():
    """Create a new praise report - logs to Heartbeat care signals and routes to campus pastor"""
    try:
        logger.info(f"Praise report endpoint called")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        email = data.get('email')
        person_id = data.get('person_id')  # NEW: Accept person_id from mobile app
        report = data.get('report')
        campus = data.get('campus', 'paradise')  # Get campus from request, default to paradise
        
        logger.info(f"📥 PRAISE REPORT RECEIVED:")
        logger.info(f"   - Email: {email}")
        logger.info(f"   - Person ID: {person_id}")
        logger.info(f"   - Campus: {campus}")
        logger.info(f"   - Report length: {len(report) if report else 0} chars")
        
        if not email or not report:
            logger.warning(f"Missing email or report text")
            return jsonify({'error': 'Email and report text required'}), 400
        
        # Find person - CRITICAL: If person_id provided, USE IT and don't fall back to email
        person = None
        if person_id:
            # Use person_id directly if provided (most reliable - from logged-in user)
            logger.info(f"🔍 STEP 1: Looking up person by person_id: {person_id}")
            person = Person.query.filter_by(id=person_id, is_active=True).first()
            if person:
                logger.info(f"✅ FOUND PERSON BY ID: {person.full_name} ({person.id})")
                logger.info(f"   - Email: {person.email}")
                logger.info(f"   - Campus: {person.campus}")
                logger.info(f"   - Is Active: {person.is_active}")
                # Verify email matches (for debugging, but still use this person)
                if person.email and person.email.lower() != email.lower():
                    logger.warning(f"⚠️ Email mismatch: Person has '{person.email}' but request has '{email}'")
                    logger.warning(f"   Using Person {person.id} anyway (person_id takes priority)")
            else:
                logger.error(f"❌ Person ID {person_id} NOT FOUND in database!")
                logger.error(f"   This is a critical error - person_id should always exist after login")
                return jsonify({'error': f'Person record not found for ID: {person_id}. Please log out and log back in.'}), 404
        
        if not person:
            # Fallback: Look up by email AND campus to ensure we get the right person
            logger.info(f"Looking up person by email+campus: {email}, campus: {campus}")
            person = Person.query.filter_by(email=email, campus=campus, is_active=True).first()
            
            if not person:
                # Try without campus filter (in case campus changed)
                logger.info(f"Person not found with campus filter, trying without: {email}")
                person = Person.query.filter_by(email=email, is_active=True).first()
        
        if not person:
            # Auto-create person (like giving endpoint does)
            logger.info(f"Person not found, creating new person for: {email} at {campus}")
            try:
                import uuid
                person_id = f"user_{uuid.uuid4().hex[:12]}"
                name_from_email = email.split('@')[0].replace('.', ' ').title()
                
                person = Person(
                    id=person_id,
                    full_name=name_from_email,
                    email=email,
                    campus=campus,  # Use campus from request
                    is_active=True
                )
                db.session.add(person)
                db.session.flush()
                logger.info(f"✅ Created new person: {person.id} - {person.full_name} at {campus}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ Error creating person: {e}", exc_info=True)
                return jsonify({'error': 'Failed to create person record'}), 500
        else:
            # Update person's campus if it has changed (use campus from request, not person record)
            if person.campus != campus and campus and campus != 'paradise' and campus != 'all_campuses':
                logger.info(f"📝 Updating person {email} campus from '{person.campus}' to '{campus}'")
                person.campus = campus
                db.session.flush()
                logger.info(f"✅ Updated person campus to: {person.campus}")
        
        # CRITICAL: Use campus from request data (not person.campus) to ensure correct linking
        final_campus = campus if campus and campus != 'paradise' and campus != 'all_campuses' else (person.campus if person.campus != 'all_campuses' else 'copper_coast')
        
        # If person campus is wrong, fix it now
        if person.campus == 'all_campuses' and final_campus != 'all_campuses':
            logger.info(f"🔧 FIXING: Person campus is 'all_campuses', changing to '{final_campus}'")
            person.campus = final_campus
            db.session.flush()
        
        logger.info(f"📍 FINAL CAMPUS DECISION (praise): request_campus={campus}, person.campus={person.campus}, using={final_campus}")
        
        # Find campus pastor for routing
        campus_pastor = None
        pastor_info = None
        if final_campus and final_campus != 'all_campuses':
            campus_pastor = get_campus_pastor(final_campus)
            if campus_pastor:
                pastor_info = f"Routed to {campus_pastor['full_name']} ({campus_pastor['email']}) - {final_campus} campus pastor"
                logger.info(f"Praise report from {email} ({final_campus}) - {pastor_info}")
        
        # Create BOTH PrayerSubmission (for Prayer & Praise page) AND CareCase (for Heartbeat)
        try:
            # Include routing info in details
            details_with_routing = report
            if pastor_info:
                details_with_routing += f"\n\n---\n{pastor_info}"
            
            # 1. Create PrayerSubmission record (for Prayer & Praise page) - USE FINAL_CAMPUS
            logger.info(f"Creating PrayerSubmission (praise) for {email} with campus: {final_campus}")
            prayer_submission = PrayerSubmission(
                person_id=person.id,
                email=email,
                name=person.full_name,
                submission_type='praise',
                content=report,
                campus=final_campus,  # USE REQUEST CAMPUS, not person.campus
                source='app',
                status='approved',  # Auto-approve from app
                is_public=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(prayer_submission)
            logger.info(f"PrayerSubmission (praise) added")
            
            # 2. Create CareCase record (for Heartbeat profile)
            logger.info(f"Creating CareCase (praise) for {email}")
            care_case = CareCase(
                person_id=person.id,
                type='praise_report',
                status='open',
                priority='low',
                summary=report[:500],  # First 500 chars as summary
                details=details_with_routing,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            logger.info(f"CareCase (praise) added")
            
            # Commit both records
            logger.info(f"Committing both PrayerSubmission and CareCase (praise)...")
            db.session.commit()
            logger.info(f"✅ COMMIT SUCCESSFUL!")
            logger.info(f"   - PrayerSubmission ID: {prayer_submission.id}, Campus: {prayer_submission.campus}")
            logger.info(f"   - CareCase ID: {care_case.id}, Person ID: {care_case.person_id}")
            logger.info(f"   - Person: {person.full_name} ({person.id}), Person Campus: {person.campus}")
            logger.info(f"   - Request Campus: {campus}, Final Campus Used: {final_campus}")
            
            response_message = 'Praise report received'
            if pastor_info:
                response_message += '! Your campus pastor has been notified.'
            
            return jsonify({
                'success': True,
                'message': response_message,
                'prayer_submission_id': prayer_submission.id,
                'care_case_id': care_case.id,
                'routed_to': campus_pastor['email'] if campus_pastor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating praise records: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Failed to create praise report'}), 500
        
    except Exception as e:
        logger.error(f"❌ FATAL: Error creating praise report: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# GET PRAYER/PRAISE SUBMISSIONS
# ============================================================================

@prayer_bp.route('/submissions', methods=['GET'])
@login_required
def get_submissions():
    """Get all prayer requests and praise reports (from CareCase table)"""
    try:
        from flask_login import current_user
        if not current_user.has_permission('prayer_requests', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get all care cases that are prayer_request or praise_report
        care_cases = CareCase.query.filter(
            CareCase.type.in_(['prayer_request', 'praise_report'])
        ).order_by(CareCase.created_at.desc()).all()
        
        # Convert to dict and add person name
        submissions = []
        for case in care_cases:
            case_dict = case.to_dict()
            if case.person:
                case_dict['person_name'] = case.person.full_name
                case_dict['campus'] = case.person.campus
            submissions.append(case_dict)
        
        return jsonify({
            'submissions': submissions,
            'count': len(submissions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting prayer/praise submissions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@prayer_bp.route('/submissions/<int:case_id>/status', methods=['PUT'])
@login_required
def update_submission_status(case_id):
    """Update the status of a prayer/praise submission"""
    try:
        if not current_user.has_permission('prayer_requests', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status or new_status not in ['open', 'in_progress', 'closed']:
            return jsonify({'error': 'Invalid status. Must be: open, in_progress, or closed'}), 400
        
        care_case = CareCase.query.get(case_id)
        if not care_case:
            return jsonify({'error': 'Submission not found'}), 404
        
        # Check if this is a prayer/praise case
        if care_case.type not in ['prayer_request', 'praise_report']:
            return jsonify({'error': 'Not a prayer/praise submission'}), 400
        
        care_case.status = new_status
        care_case.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Updated submission {case_id} status to {new_status} by {current_user.username}")
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'case': care_case.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error updating submission status: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update status'}), 500


# ============================================================================
# PRAYER LINK MANAGEMENT (similar to Giving QR Codes)
# ============================================================================

@prayer_bp.route('/links', methods=['GET'])
@login_required
def get_prayer_links():
    """Get all prayer links (admin/pastor only)"""
    try:
        if not current_user.has_permission('prayer_requests', 'view'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        campus = request.args.get('campus')
        department = request.args.get('department')
        is_active = request.args.get('is_active', 'true')
        
        query = PrayerLink.query
        
        if campus and campus != 'all_campuses':
            query = query.filter_by(campus=campus)
        
        if department:
            query = query.filter_by(department=department)
        
        if is_active.lower() == 'true':
            query = query.filter_by(is_active=True)
        
        links = query.order_by(PrayerLink.created_at.desc()).all()
        
        return jsonify({
            'links': [link.to_dict() for link in links],
            'count': len(links)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting prayer links: {e}")
        return jsonify({'error': str(e)}), 500


@prayer_bp.route('/links', methods=['POST'])
@login_required
def create_prayer_link():
    """Create a new prayer/praise submission link"""
    try:
        if not current_user.has_permission('prayer_requests', 'create'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        link_type = data.get('link_type', 'both')  # 'prayer', 'praise', 'both'
        campus = data.get('campus')  # Optional filter
        department = data.get('department')  # Optional filter
        location = data.get('location', '')
        description = data.get('description', '')
        code_type = data.get('code_type', 'qr')  # 'qr', 'nfc', 'link'
        count = data.get('count', 1)  # Generate multiple at once
        
        if link_type not in ['prayer', 'praise', 'both']:
            return jsonify({'error': 'Invalid link_type. Must be: prayer, praise, or both'}), 400
        
        created_links = []
        
        for i in range(count):
            # Generate unique link ID
            if code_type == 'nfc':
                link_id = f"nfc_prayer_{uuid.uuid4().hex[:12]}"
            else:
                link_id = f"prayer_{uuid.uuid4().hex[:12]}"
            
            link = PrayerLink(
                link_id=link_id,
                link_type=link_type,
                campus=campus,
                department=department,
                location=location if count == 1 else f"{location} #{i+1}" if location else None,
                description=description,
                code_type=code_type,
                is_active=True,
                created_by=current_user.username
            )
            
            db.session.add(link)
            created_links.append(link)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {count} prayer link(s)',
            'links': [link.to_dict() for link in created_links]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating prayer link: {e}")
        return jsonify({'error': str(e)}), 500


@prayer_bp.route('/links/<int:link_id>', methods=['PUT'])
@login_required
def update_prayer_link(link_id):
    """Update a prayer link"""
    try:
        if not current_user.has_permission('prayer_requests', 'edit'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        link = PrayerLink.query.get(link_id)
        if not link:
            return jsonify({'error': 'Link not found'}), 404
        
        data = request.get_json()
        
        if 'location' in data:
            link.location = data['location']
        if 'description' in data:
            link.description = data['description']
        if 'is_active' in data:
            link.is_active = data['is_active']
        if 'campus' in data:
            link.campus = data['campus']
        if 'department' in data:
            link.department = data['department']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'link': link.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating prayer link: {e}")
        return jsonify({'error': str(e)}), 500


@prayer_bp.route('/links/<int:link_id>', methods=['DELETE'])
@login_required
def delete_prayer_link(link_id):
    """Delete (deactivate) a prayer link"""
    try:
        if not current_user.has_permission('prayer_requests', 'delete'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        link = PrayerLink.query.get(link_id)
        if not link:
            return jsonify({'error': 'Link not found'}), 404
        
        link.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Link deactivated'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting prayer link: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PUBLIC SUBMISSION ENDPOINTS (No Auth Required - for QR/NFC/Social Links)
# ============================================================================

@prayer_bp.route('/link/<link_id>', methods=['GET'])
def get_link_info(link_id):
    """
    Get information about a prayer link (public endpoint)
    Used when scanning QR/NFC or opening social media link
    """
    try:
        link = PrayerLink.query.filter_by(link_id=link_id, is_active=True).first()
        
        if not link:
            return jsonify({'error': 'Invalid or inactive link'}), 404
        
        # Update scan count
        link.scan_count += 1
        link.last_scan_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'link_type': link.link_type,
            'campus': link.campus,
            'department': link.department,
            'location': link.location,
            'description': link.description
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error getting link info: {e}")
        return jsonify({'error': str(e)}), 500


@prayer_bp.route('/link/<link_id>/submit', methods=['POST'])
def submit_via_link(link_id):
    """
    Submit prayer/praise via a public link (no auth required)
    Used for QR/NFC tap points, social media links, etc.
    """
    try:
        # Verify link exists and is active
        link = PrayerLink.query.filter_by(link_id=link_id, is_active=True).first()
        
        if not link:
            return jsonify({'error': 'Invalid or inactive link'}), 404
        
        data = request.get_json()
        
        # Required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        submission_type = data.get('type', 'prayer')  # 'prayer' or 'praise'
        text = data.get('text', '').strip()
        
        # Optional fields
        phone = data.get('phone', '').strip()
        campus = data.get('campus') or link.campus  # Use link's campus if not provided
        department = data.get('department') or link.department  # Use link's department if not provided
        
        if not name or not email or not text:
            return jsonify({'error': 'Name, email, and message required'}), 400
        
        if submission_type not in ['prayer', 'praise']:
            return jsonify({'error': 'Type must be prayer or praise'}), 400
        
        # Check if link allows this submission type
        if link.link_type != 'both' and link.link_type != submission_type:
            return jsonify({'error': f'This link only accepts {link.link_type} submissions'}), 400
        
        # Find or create person
        person = Person.query.filter_by(email=email, is_active=True).first()
        
        if not person:
            # Create new person
            try:
                person_id = f"user_{uuid.uuid4().hex[:12]}"
                person = Person(
                    id=person_id,
                    full_name=name,
                    email=email,
                    phone=phone if phone else None,
                    campus=campus or 'paradise',
                    department=department,
                    is_active=True
                )
                db.session.add(person)
                db.session.flush()
                logger.info(f"Created new person via prayer link: {person.id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating person: {e}")
                return jsonify({'error': 'Failed to create person record'}), 500
        else:
            # Update existing person if needed
            if campus and not person.campus:
                person.campus = campus
            if department and not person.department:
                person.department = department
            if phone and not person.phone:
                person.phone = phone
        
        # Find campus pastor for routing
        campus_pastor = None
        pastor_info = None
        if person.campus and person.campus != 'all_campuses':
            campus_pastor = get_campus_pastor(person.campus)
            if campus_pastor:
                pastor_info = f"Routed to {campus_pastor['full_name']} ({campus_pastor['email']}) - {person.campus} campus pastor"
        
        # Create care case
        try:
            details_with_routing = text
            
            # Add link context
            details_with_routing += f"\n\n---\nSubmitted via: {link.location or 'Prayer Link'}"
            if link.description:
                details_with_routing += f"\nLink: {link.description}"
            
            # Add routing info
            if pastor_info:
                details_with_routing += f"\n{pastor_info}"
            
            care_case = CareCase(
                person_id=person.id,
                type='prayer_request' if submission_type == 'prayer' else 'praise_report',
                status='open',
                priority='medium' if submission_type == 'prayer' else 'low',
                summary=text[:500],
                details=details_with_routing,
                created_by_person_id=person.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(care_case)
            
            # Update link submission count
            link.submission_count += 1
            
            db.session.commit()
            
            logger.info(f"{'Prayer' if submission_type == 'prayer' else 'Praise'} submitted via link {link_id} by {email}")
            
            response_message = f"{'Prayer request' if submission_type == 'prayer' else 'Praise report'} received"
            if pastor_info:
                response_message += '. Your campus pastor has been notified.'
            
            return jsonify({
                'success': True,
                'message': response_message,
                'id': care_case.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating care case from link: {e}")
            return jsonify({'error': 'Failed to submit request'}), 500
        
    except Exception as e:
        logger.error(f"Error submitting via link: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADMIN UTILITIES
# ============================================================================

@prayer_bp.route('/admin/check-person/<email>', methods=['GET'])
def check_person_by_email(email):
    """Diagnostic endpoint to check Person records and care cases - NO AUTH for debugging"""
    try:
        # Find all Person records with this email (including inactive)
        persons = Person.query.filter_by(email=email).all()
        
        result = {
            'email': email,
            'found_count': len(persons),
            'records': []
        }
        
        for person in persons:
            # Check all care cases (not just prayer requests)
            all_care_cases = CareCase.query.filter_by(person_id=person.id).all()
            prayer_cases = [c for c in all_care_cases if c.type == 'prayer_request']
            praise_cases = [c for c in all_care_cases if c.type == 'praise_report']
            open_cases = [c for c in all_care_cases if c.status in ['open', 'in_progress']]
            
            result['records'].append({
                'id': person.id,
                'full_name': person.full_name,
                'email': person.email,
                'campus': person.campus,
                'is_active': person.is_active,
                'created_at': person.created_at.isoformat() if person.created_at else None,
                'updated_at': person.updated_at.isoformat() if person.updated_at else None,
                'total_care_cases': len(all_care_cases),
                'prayer_cases_count': len(prayer_cases),
                'praise_cases_count': len(praise_cases),
                'open_cases_count': len(open_cases),
                'recent_prayers': [{
                    'id': p.id,
                    'type': p.type,
                    'status': p.status,
                    'person_id': p.person_id,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                    'summary': p.summary[:100] if p.summary else None
                } for p in prayer_cases[-5:]]  # Last 5
            })
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error checking person: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@prayer_bp.route('/admin/fix-campus', methods=['POST'])
def fix_user_campus():
    """Admin endpoint to update a user's campus - NO AUTH for debugging"""
    try:
        data = request.get_json()
        email = data.get('email')
        new_campus = data.get('campus')
        
        if not email or not new_campus:
            return jsonify({'error': 'Email and campus required'}), 400
        
        # Update ALL active person records with this email
        persons = Person.query.filter_by(email=email, is_active=True).all()
        if not persons:
            return jsonify({'error': 'No active person records found'}), 404
        
        updated = []
        for person in persons:
            old_campus = person.campus
            person.campus = new_campus
            person.updated_at = datetime.utcnow()
            updated.append({
                'id': person.id,
                'full_name': person.full_name,
                'old_campus': old_campus,
                'new_campus': new_campus
            })
        
        db.session.commit()
        
        logger.info(f"✅ Updated {len(updated)} person record(s) for {email} to campus {new_campus}")
        return jsonify({
            'success': True,
            'message': f'Updated {len(updated)} person record(s) to {new_campus}',
            'updated_records': updated
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error updating person campus: {e}", exc_info=True)
        return jsonify({'error': f'Failed to update campus: {str(e)}'}), 500
