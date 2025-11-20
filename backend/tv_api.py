"""
Pulse TV API

Endpoints for managing TV series, episodes, and tracking user progress.
Integrates with Heartbeat system for discipleship scoring.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from models import (
    db, TVSeries, TVEpisode, TVTag, TVUserEpisodeProgress, 
    TVEpisodeDiscipleshipLink, Person, DiscipleshipStep,
    tv_series_tags, tv_episode_tags
)
from sqlalchemy import func, text
from datetime import datetime, date
from heartbeat_engine import HeartbeatEngine
import logging
import os
import uuid
from PIL import Image

logger = logging.getLogger(__name__)

tv_bp = Blueprint('tv', __name__, url_prefix='/api/tv')

# Image upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'tv')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# PUBLIC ENDPOINTS (App Users)
# ============================================================================

@tv_bp.route('/series', methods=['GET'])
@login_required
def get_series():
    """Get all published series"""
    try:
        category_filter = request.args.get('category')
        audience_filter = request.args.get('audience')
        
        query = TVSeries.query.filter_by(is_published=True)
        
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        if audience_filter:
            query = query.filter_by(audience=audience_filter)
        
        series_list = query.order_by(TVSeries.created_at.desc()).all()
        
        return jsonify({
            'series': [s.to_dict() for s in series_list],
            'count': len(series_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting series: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/series/<int:series_id>', methods=['GET'])
@login_required
def get_series_detail(series_id):
    """Get a single series with episodes"""
    try:
        series = TVSeries.query.get(series_id)
        if not series or not series.is_published:
            return jsonify({'error': 'Series not found'}), 404
        
        return jsonify({
            'series': series.to_dict(include_episodes=True)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting series detail: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/episode/<int:episode_id>', methods=['GET'])
@login_required
def get_episode(episode_id):
    """Get a single episode"""
    try:
        episode = TVEpisode.query.get(episode_id)
        if not episode or not episode.is_published:
            return jsonify({'error': 'Episode not found'}), 404
        
        # Get current user's person_id if available
        person_id = getattr(current_user, 'id', None)
        
        return jsonify({
            'episode': episode.to_dict(include_progress=True, person_id=person_id)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting episode: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/episode/<int:episode_id>/progress', methods=['POST'])
@login_required
def update_episode_progress(episode_id):
    """Update user's progress watching an episode"""
    try:
        episode = TVEpisode.query.get(episode_id)
        if not episode or not episode.is_published:
            return jsonify({'error': 'Episode not found'}), 404
        
        person_id = getattr(current_user, 'id', None)
        if not person_id:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        position = data.get('position', 0)  # Position in seconds
        completed = data.get('completed', False)
        
        # Get or create progress record
        progress = TVUserEpisodeProgress.query.filter_by(
            person_id=person_id,
            episode_id=episode_id
        ).first()
        
        if not progress:
            progress = TVUserEpisodeProgress(
                person_id=person_id,
                episode_id=episode_id,
                started_at=datetime.utcnow(),
                last_position_seconds=position
            )
            db.session.add(progress)
        else:
            progress.last_position_seconds = position
            progress.updated_at = datetime.utcnow()
        
        # Handle completion
        if completed and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            
            # Trigger Heartbeat integration
            try:
                _handle_episode_completion(person_id, episode_id)
            except Exception as e:
                logger.warning(f"Failed to handle episode completion for heartbeat: {e}")
                # Don't fail the request if heartbeat update fails
        
        db.session.commit()
        
        return jsonify({
            'message': 'Progress updated successfully',
            'progress': progress.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating episode progress: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/most-watched', methods=['GET'])
@login_required
def get_most_watched():
    """
    Get most watched series/episodes based on actual watch data.
    
    Algorithm:
    1. Count unique viewers who completed episodes
    2. Weight recent completions more heavily (last 30 days = 2x, 7 days = 3x)
    3. Count partial watches (watched >50% of episode)
    4. Sort by total watch score
    5. Return top 12 series
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Get all completed episodes with their series
        completed_progress = db.session.query(
            TVUserEpisodeProgress.episode_id,
            TVEpisode.series_id,
            TVUserEpisodeProgress.completed_at,
            TVUserEpisodeProgress.completed
        ).join(
            TVEpisode, TVUserEpisodeProgress.episode_id == TVEpisode.id
        ).filter(
            TVEpisode.is_published == True,
            TVUserEpisodeProgress.completed == True
        ).all()
        
        # Get partial watches (>50% watched)
        partial_progress = db.session.query(
            TVUserEpisodeProgress.episode_id,
            TVEpisode.series_id,
            TVUserEpisodeProgress.last_position_seconds,
            TVEpisode.duration_seconds
        ).join(
            TVEpisode, TVUserEpisodeProgress.episode_id == TVEpisode.id
        ).filter(
            TVEpisode.is_published == True,
            TVUserEpisodeProgress.completed == False,
            TVEpisode.duration_seconds > 0
        ).all()
        
        # Calculate watch scores per series
        series_scores = {}
        
        # Process completed episodes
        for progress in completed_progress:
            series_id = progress.series_id
            if not series_id:
                continue
                
            if series_id not in series_scores:
                series_scores[series_id] = {
                    'completed_views': 0,
                    'recent_views': 0,
                    'very_recent_views': 0,
                    'partial_views': 0,
                    'total_score': 0
                }
            
            # Base score: 1 point per completion
            series_scores[series_id]['completed_views'] += 1
            
            # Weight recent views
            if progress.completed_at:
                if progress.completed_at >= seven_days_ago:
                    series_scores[series_id]['very_recent_views'] += 1
                elif progress.completed_at >= thirty_days_ago:
                    series_scores[series_id]['recent_views'] += 1
        
        # Process partial watches (>50% watched)
        for progress in partial_progress:
            series_id = progress.series_id
            if not series_id:
                continue
            
            if progress.duration_seconds > 0:
                watch_percentage = (progress.last_position_seconds / progress.duration_seconds) * 100
                if watch_percentage >= 50:  # Only count if watched at least 50%
                    if series_id not in series_scores:
                        series_scores[series_id] = {
                            'completed_views': 0,
                            'recent_views': 0,
                            'very_recent_views': 0,
                            'partial_views': 0,
                            'total_score': 0
                        }
                    series_scores[series_id]['partial_views'] += 1
        
        # Calculate total scores
        # Formula: completed (1pt) + recent completed (2pt) + very recent (3pt) + partial (0.5pt)
        for series_id, scores in series_scores.items():
            total = (
                (scores['completed_views'] - scores['recent_views'] - scores['very_recent_views']) * 1.0 +  # Base completions
                scores['recent_views'] * 2.0 +  # Last 30 days (but not last 7)
                scores['very_recent_views'] * 3.0 +  # Last 7 days
                scores['partial_views'] * 0.5  # Partial watches (less weight)
            )
            scores['total_score'] = total
        
        # Get all series and attach scores
        all_series = TVSeries.query.filter_by(is_published=True).all()
        series_with_scores = []
        
        for series in all_series:
            score_data = series_scores.get(series.id, {
                'completed_views': 0,
                'recent_views': 0,
                'very_recent_views': 0,
                'partial_views': 0,
                'total_score': 0
            })
            
            series_with_scores.append({
                'series': series.to_dict(),
                'watch_score': score_data['total_score'],
                'completed_views': score_data['completed_views'],
                'recent_views': score_data['recent_views'],
                'very_recent_views': score_data['very_recent_views'],
                'partial_views': score_data['partial_views']
            })
        
        # Sort by total score (descending)
        series_with_scores.sort(key=lambda x: x['watch_score'], reverse=True)
        
        # Return top 12
        top_series = [item['series'] for item in series_with_scores[:12]]
        
        return jsonify({
            'series': top_series,
            'count': len(top_series)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting most watched: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/upload-thumbnail', methods=['POST'])
@login_required
def upload_thumbnail():
    """Upload a thumbnail image for series/episode"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB'}), 400
        
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Optional: Resize/optimize image (keep it reasonable size)
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary (handles RGBA, P, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if larger than 1920x1080 (keep aspect ratio)
                max_size = (1920, 1080)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(filepath, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            logger.warning(f"Failed to optimize image: {e}")
            # Continue anyway - file is saved
        
        # Return URL for the uploaded file
        file_url = f"/uploads/tv/{unique_filename}"
        
        return jsonify({
            'url': file_url,
            'filename': unique_filename,
            'message': 'Image uploaded successfully'
        }), 200
        
    except RequestEntityTooLarge:
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB'}), 400
    except Exception as e:
        logger.error(f"Error uploading thumbnail: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/uploads/tv/<filename>')
def serve_tv_thumbnail(filename):
    """Serve uploaded TV thumbnails"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error serving thumbnail: {e}")
        return jsonify({'error': 'File not found'}), 404


@tv_bp.route('/person/<person_id>/watched', methods=['GET'])
@login_required
def get_person_watched_episodes(person_id):
    """Get all episodes a person has watched (for Heartbeat profile)"""
    try:
        # Check permissions - only admins or the person themselves
        current_person_id = getattr(current_user, 'id', None)
        user_role = getattr(current_user, 'role', None)
        is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
        
        if not is_admin and current_person_id != person_id:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get all completed episodes for this person
        progress_records = TVUserEpisodeProgress.query.filter_by(
            person_id=person_id,
            completed=True
        ).order_by(TVUserEpisodeProgress.completed_at.desc()).all()
        
        episodes = []
        for progress in progress_records:
            if progress.episode and progress.episode.is_published:
                episode_dict = progress.episode.to_dict()
                episode_dict['completed_at'] = progress.completed_at.isoformat() if progress.completed_at else None
                episode_dict['series'] = progress.episode.series.to_dict() if progress.episode.series else None
                episodes.append(episode_dict)
        
        return jsonify({
            'episodes': episodes,
            'count': len(episodes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting person watched episodes: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/continue-watching', methods=['GET'])
@login_required
def get_continue_watching():
    """Get episodes user has started but not completed"""
    try:
        person_id = getattr(current_user, 'id', None)
        if not person_id:
            return jsonify({'episodes': [], 'count': 0}), 200
        
        # Get progress records for incomplete episodes
        progress_records = TVUserEpisodeProgress.query.filter_by(
            person_id=person_id,
            completed=False
        ).order_by(TVUserEpisodeProgress.updated_at.desc()).limit(20).all()
        
        episodes = []
        for progress in progress_records:
            if progress.episode and progress.episode.is_published:
                episode_dict = progress.episode.to_dict(include_progress=True, person_id=person_id)
                episodes.append(episode_dict)
        
        return jsonify({
            'episodes': episodes,
            'count': len(episodes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting continue watching: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@tv_bp.route('/admin/series', methods=['POST'])
@login_required
def create_series():
    """Create a new series (admin only)"""
    try:
        # Check permissions
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'title' not in data:
            return jsonify({'error': 'Missing required field: title'}), 400
        
        series = TVSeries(
            title=data['title'],
            description=data.get('description'),
            category=data.get('category'),
            audience=data.get('audience', 'all'),
            thumbnail_url=data.get('thumbnail_url'),
            is_published=data.get('is_published', False),
            create_custom_step=data.get('create_custom_step', False),
            custom_step_name=data.get('custom_step_name')
        )
        
        db.session.add(series)
        db.session.flush()  # Get series.id
        
        # Add tags if provided
        if 'tags' in data and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag = TVTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = TVTag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                # Insert into pivot table directly
                db.session.execute(
                    tv_series_tags.insert().values(series_id=series.id, tag_id=tag.id)
                )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Series created successfully',
            'series': series.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating series: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/series/<int:series_id>', methods=['PUT'])
@login_required
def update_series(series_id):
    """Update a series"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        series = TVSeries.query.get(series_id)
        if not series:
            return jsonify({'error': 'Series not found'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            series.title = data['title']
        if 'description' in data:
            series.description = data['description']
        if 'category' in data:
            series.category = data['category']
        if 'audience' in data:
            series.audience = data['audience']
        if 'thumbnail_url' in data:
            series.thumbnail_url = data['thumbnail_url']
        if 'is_published' in data:
            series.is_published = bool(data['is_published'])
        if 'create_custom_step' in data:
            series.create_custom_step = bool(data['create_custom_step'])
        if 'custom_step_name' in data:
            series.custom_step_name = data['custom_step_name'] if data['custom_step_name'] else None
        
        # Update tags
        if 'tags' in data and isinstance(data['tags'], list):
            # Remove existing tags by deleting from pivot table
            db.session.execute(
                tv_series_tags.delete().where(tv_series_tags.c.series_id == series_id)
            )
            # Add new tags
            for tag_name in data['tags']:
                tag = TVTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = TVTag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                # Insert into pivot table directly
                db.session.execute(
                    tv_series_tags.insert().values(series_id=series_id, tag_id=tag.id)
                )
        
        series.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Series updated successfully',
            'series': series.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating series: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/series/<int:series_id>', methods=['DELETE'])
@login_required
def delete_series(series_id):
    """Delete a series"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        series = TVSeries.query.get(series_id)
        if not series:
            return jsonify({'error': 'Series not found'}), 404
        
        db.session.delete(series)
        db.session.commit()
        
        return jsonify({'message': 'Series deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting series: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/episode', methods=['POST'])
@login_required
def create_episode():
    """Create a new episode"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if 'title' not in data or 'series_id' not in data:
            return jsonify({'error': 'Missing required fields: title, series_id'}), 400
        
        series = TVSeries.query.get(data['series_id'])
        if not series:
            return jsonify({'error': 'Series not found'}), 404
        
        # Get next order_index
        max_order = db.session.query(func.max(TVEpisode.order_index)).filter_by(
            series_id=data['series_id']
        ).scalar() or 0
        
        episode = TVEpisode(
            series_id=data['series_id'],
            title=data['title'],
            description=data.get('description'),
            video_url=data.get('video_url'),
            duration_seconds=data.get('duration_seconds', 0),
            order_index=data.get('order_index', max_order + 1),
            is_published=data.get('is_published', False),
            downloadable_notes_url=data.get('downloadable_notes_url'),
            create_custom_step=data.get('create_custom_step', False),
            custom_step_name=data.get('custom_step_name')
        )
        
        db.session.add(episode)
        db.session.flush()
        
        # Add tags if provided
        if 'tags' in data and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag = TVTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = TVTag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                # Insert into pivot table directly
                db.session.execute(
                    tv_episode_tags.insert().values(episode_id=episode.id, tag_id=tag.id)
                )
        
        # Add discipleship links if provided
        if 'discipleship_links' in data and isinstance(data['discipleship_links'], list):
            for link_data in data['discipleship_links']:
                link = TVEpisodeDiscipleshipLink(
                    episode_id=episode.id,
                    discipleship_step_type=link_data.get('discipleship_step_type'),
                    auto_complete=link_data.get('auto_complete', True)
                )
                db.session.add(link)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Episode created successfully',
            'episode': episode.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating episode: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/episode/<int:episode_id>', methods=['PUT'])
@login_required
def update_episode(episode_id):
    """Update an episode"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        episode = TVEpisode.query.get(episode_id)
        if not episode:
            return jsonify({'error': 'Episode not found'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            episode.title = data['title']
        if 'description' in data:
            episode.description = data['description']
        if 'video_url' in data:
            episode.video_url = data['video_url']
        if 'duration_seconds' in data:
            episode.duration_seconds = int(data['duration_seconds'])
        if 'order_index' in data:
            episode.order_index = int(data['order_index'])
        if 'is_published' in data:
            episode.is_published = bool(data['is_published'])
        if 'downloadable_notes_url' in data:
            episode.downloadable_notes_url = data['downloadable_notes_url']
        if 'create_custom_step' in data:
            episode.create_custom_step = bool(data['create_custom_step'])
        if 'custom_step_name' in data:
            episode.custom_step_name = data['custom_step_name'] if data['custom_step_name'] else None
        
        # Update tags
        if 'tags' in data and isinstance(data['tags'], list):
            # Remove existing tags by deleting from pivot table
            db.session.execute(
                tv_episode_tags.delete().where(tv_episode_tags.c.episode_id == episode_id)
            )
            # Add new tags
            for tag_name in data['tags']:
                tag = TVTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = TVTag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                # Insert into pivot table directly
                db.session.execute(
                    tv_episode_tags.insert().values(episode_id=episode_id, tag_id=tag.id)
                )
        
        # Update discipleship links
        if 'discipleship_links' in data:
            # Delete existing links
            TVEpisodeDiscipleshipLink.query.filter_by(episode_id=episode_id).delete()
            # Add new links
            if isinstance(data['discipleship_links'], list):
                for link_data in data['discipleship_links']:
                    link = TVEpisodeDiscipleshipLink(
                        episode_id=episode_id,
                        discipleship_step_type=link_data.get('discipleship_step_type'),
                        auto_complete=link_data.get('auto_complete', True)
                    )
                    db.session.add(link)
        
        episode.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Episode updated successfully',
            'episode': episode.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating episode: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/episode/<int:episode_id>', methods=['DELETE'])
@login_required
def delete_episode(episode_id):
    """Delete an episode"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        episode = TVEpisode.query.get(episode_id)
        if not episode:
            return jsonify({'error': 'Episode not found'}), 404
        
        db.session.delete(episode)
        db.session.commit()
        
        return jsonify({'message': 'Episode deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting episode: {e}")
        return jsonify({'error': str(e)}), 500


@tv_bp.route('/admin/series/all', methods=['GET'])
@login_required
def get_all_series_admin():
    """Get all series (including unpublished) for admin"""
    try:
        if not _has_tv_admin_permission():
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        series_list = TVSeries.query.order_by(TVSeries.created_at.desc()).all()
        
        return jsonify({
            'series': [s.to_dict(include_episodes=True) for s in series_list],
            'count': len(series_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all series: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _has_tv_admin_permission():
    """Check if user has TV admin permissions"""
    user_role = getattr(current_user, 'role', None)
    is_admin = user_role in ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor']
    has_permission = current_user.has_permission('heartbeat', 'edit') if hasattr(current_user, 'has_permission') else False
    return is_admin or has_permission


def _handle_episode_completion(person_id, episode_id):
    """
    Handle episode completion - create discipleship steps and update heartbeat.
    
    This function:
    1. ALWAYS creates a DiscipleshipStep for episode completion (+5 spiritual score)
    2. Checks for EpisodeDiscipleshipLink records and creates additional steps
    3. Triggers Heartbeat recalculation
    4. Adds to activity feed
    """
    episode = TVEpisode.query.get(episode_id)
    if not episode:
        return
    
    # ALWAYS create a DiscipleshipStep for episode completion
    # This will boost spiritual score by 5 points (counted as "other milestone")
    episode_step = DiscipleshipStep(
        person_id=person_id,
        type='tv_episode_completion',
        description=f"Watched: {episode.title}",
        date=date.today(),
        created_by_person_id='system'
    )
    db.session.add(episode_step)
    logger.info(f"Created TV episode completion step for person {person_id}, episode {episode_id}")
    
    # Create custom discipleship step if enabled
    if episode.create_custom_step:
        step_name = episode.custom_step_name or episode.title
        # Check if custom step already exists for this episode
        existing_custom = DiscipleshipStep.query.filter_by(
            person_id=person_id,
            type='tv_custom_step',
            description=step_name
        ).first()
        
        if not existing_custom:
            custom_step = DiscipleshipStep(
                person_id=person_id,
                type='tv_custom_step',
                description=step_name,
                date=date.today(),
                created_by_person_id='system'
            )
            db.session.add(custom_step)
            logger.info(f"Created custom discipleship step '{step_name}' for person {person_id} from episode {episode_id}")
    
    # Check if this completes a series (all episodes watched)
    series = episode.series
    if series:
        # Count completed episodes in this series
        completed_episodes = TVUserEpisodeProgress.query.filter_by(
            person_id=person_id,
            completed=True
        ).join(TVEpisode).filter(
            TVEpisode.series_id == series.id,
            TVEpisode.is_published == True
        ).count()
        
        total_episodes = series.episodes.filter_by(is_published=True).count()
        
        # If all episodes completed, add series completion step (+10 spiritual score)
        if completed_episodes >= total_episodes and total_episodes > 0:
            # Check if series completion step already exists
            existing_series_step = DiscipleshipStep.query.filter_by(
                person_id=person_id,
                type='tv_series_completion',
                description=f"Completed Series: {series.title}"
            ).first()
            
            if not existing_series_step:
                series_step = DiscipleshipStep(
                    person_id=person_id,
                    type='tv_series_completion',
                    description=f"Completed Series: {series.title}",
                    date=date.today(),
                    created_by_person_id='system'
                )
                db.session.add(series_step)
                logger.info(f"Created TV series completion step for person {person_id}, series {series.id}")
                
                # Create custom discipleship step for series if enabled
                if series.create_custom_step:
                    step_name = series.custom_step_name or series.title
                    # Check if custom step already exists for this series
                    existing_series_custom = DiscipleshipStep.query.filter_by(
                        person_id=person_id,
                        type='tv_custom_step',
                        description=step_name
                    ).first()
                    
                    if not existing_series_custom:
                        series_custom_step = DiscipleshipStep(
                            person_id=person_id,
                            type='tv_custom_step',
                            description=step_name,
                            date=date.today(),
                            created_by_person_id='system'
                        )
                        db.session.add(series_custom_step)
                        logger.info(f"Created custom discipleship step '{step_name}' for person {person_id} from series {series.id}")
    
    # Get all discipleship links for this episode
    links = TVEpisodeDiscipleshipLink.query.filter_by(episode_id=episode_id).all()
    
    # Create discipleship steps for auto-complete links
    for link in links:
        if link.auto_complete:
            # Check if step already exists
            existing = DiscipleshipStep.query.filter_by(
                person_id=person_id,
                type=link.discipleship_step_type
            ).first()
            
            if not existing:
                # Create new discipleship step
                step = DiscipleshipStep(
                    person_id=person_id,
                    type=link.discipleship_step_type,
                    description=f"Completed: {episode.title}",
                    date=date.today(),
                    created_by_person_id='system'  # System-created
                )
                db.session.add(step)
                logger.info(f"Created discipleship step {link.discipleship_step_type} for person {person_id} from episode {episode_id}")
    
    db.session.commit()
    
    # Trigger Heartbeat recalculation
    try:
        engine = HeartbeatEngine()
        snapshot = engine.calculate_heartbeat(person_id)
        
        logger.info(f"Recalculated Heartbeat for person {person_id} after episode {episode_id} completion. New spiritual score: {snapshot.spiritual_score}")
    except Exception as e:
        logger.warning(f"Failed to recalculate Heartbeat after episode completion: {e}")
        # Don't raise - allow the request to succeed even if heartbeat update fails

