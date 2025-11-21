#!/usr/bin/env python3
"""
Diagnostic script to check why heartbeat data is missing
"""

from app import app
from models import db, Person, EngagementProfile, Service, AttendanceEvent, ConnectAttendance, GivingSummary, DiscipleshipStep, PersonPathwayStepCompletion, HeartbeatSnapshot
from datetime import datetime, date, timedelta
import json

def diagnose_person(email):
    """Diagnose heartbeat data for a person"""
    print(f"\n{'='*80}")
    print(f"HEARTBEAT DIAGNOSTIC FOR: {email}")
    print(f"{'='*80}\n")
    
    # Find person
    person = Person.query.filter(
        db.func.lower(Person.email) == email.lower(),
        Person.is_active == True
    ).first()
    
    if not person:
        print(f"❌ Person not found with email: {email}")
        return
    
    print(f"✅ Person found: {person.id} - {person.full_name}")
    print(f"   Campus: {person.campus}")
    print(f"   Email: {person.email}")
    print(f"   Connect Group: {person.connect_group or 'None'}")
    print()
    
    # Check engagement profile
    print("="*80)
    print("ENGAGEMENT PROFILE")
    print("="*80)
    engagement = EngagementProfile.query.filter_by(person_id=person.id).first()
    if not engagement:
        print("❌ No engagement profile found")
    else:
        print(f"✅ Engagement profile exists")
        print(f"   Pulse Status: {engagement.pulse_status}")
        print(f"   Last Seen: {engagement.last_seen}")
        print(f"   Overall Engagement: {engagement.overall_engagement}")
        
        # Check attendance_log
        try:
            attendance_log = json.loads(engagement.attendance_log or '[]')
            print(f"\n   📋 Attendance Log ({len(attendance_log)} entries):")
            for i, entry in enumerate(attendance_log[-5:]):  # Show last 5
                timestamp = entry.get('timestamp', 'unknown')
                zones = entry.get('zones', [])
                campus = entry.get('campus', 'unknown')
                print(f"      {i+1}. {timestamp} - {zones} - {campus}")
        except Exception as e:
            print(f"   ❌ Error parsing attendance_log: {e}")
        
        # Check serving_log (also stores milestones)
        try:
            serving_log = json.loads(engagement.serving_log or '[]')
            print(f"\n   📋 Serving/Milestones Log ({len(serving_log)} entries):")
            giving_entries = [e for e in serving_log if e.get('type') == 'giving']
            serving_entries = [e for e in serving_log if e.get('type') != 'giving']
            print(f"      Giving entries: {len(giving_entries)}")
            print(f"      Other entries: {len(serving_entries)}")
            
            # Show recent entries
            for entry in serving_log[-3:]:
                entry_type = entry.get('type', 'unknown')
                entry_date = entry.get('date', 'unknown')
                print(f"         - {entry_type}: {entry_date}")
        except Exception as e:
            print(f"   ❌ Error parsing serving_log: {e}")
    
    print()
    
    # Check Sunday services
    print("="*80)
    print("SUNDAY SERVICES (Last 12 weeks)")
    print("="*80)
    end_date = date.today()
    start_date = end_date - timedelta(weeks=12)
    
    services = Service.query.filter(
        Service.type == 'sunday',
        Service.starts_at >= datetime.combine(start_date, datetime.min.time()),
        Service.starts_at <= datetime.combine(end_date, datetime.max.time())
    ).order_by(Service.starts_at).all()
    
    print(f"Found {len(services)} Sunday services")
    for service in services[-5:]:  # Show last 5
        service_name = getattr(service, 'name', 'Service')
        print(f"   - {service.starts_at.date()}: {service.campus} - {service_name}")
    
    # Check AttendanceEvents
    print("\n" + "="*80)
    print("ATTENDANCE EVENTS")
    print("="*80)
    attendance_events = AttendanceEvent.query.filter(
        AttendanceEvent.person_id == person.id
    ).order_by(AttendanceEvent.created_at.desc()).limit(10).all()
    
    print(f"Found {len(attendance_events)} attendance events")
    for event in attendance_events[:5]:
        print(f"   - {event.created_at.date()}: Service ID {event.service_id}")
    
    # Check Connect Group Attendance
    print("\n" + "="*80)
    print("CONNECT GROUP ATTENDANCE")
    print("="*80)
    connect_attendance = ConnectAttendance.query.filter(
        ConnectAttendance.person_id == person.id
    ).order_by(ConnectAttendance.date.desc()).limit(10).all()
    
    print(f"Found {len(connect_attendance)} connect group attendance records")
    for att in connect_attendance[:5]:
        print(f"   - {att.date}: Group {att.connect_group_id} - Status: {att.status}")
    
    # Check Giving
    print("\n" + "="*80)
    print("GIVING SUMMARIES")
    print("="*80)
    giving_summaries = GivingSummary.query.filter(
        GivingSummary.person_id == person.id
    ).order_by(GivingSummary.period_end.desc()).all()
    
    print(f"Found {len(giving_summaries)} giving summary records")
    for summary in giving_summaries:
        print(f"   - {summary.period_start} to {summary.period_end}: "
              f"Frequency: {summary.frequency}, Last gift: {summary.last_gift_at}")
    
    # Check Discipleship Steps
    print("\n" + "="*80)
    print("DISCIPLESHIP / SPIRITUAL")
    print("="*80)
    
    # Check Person's discipleship milestones
    print(f"Person milestones:")
    print(f"   - DNA Completed: {person.dna_completed or 'No'}")
    print(f"   - Baptised: {person.baptised_on or 'No'}")
    print(f"   - Holy Spirit: {person.filled_holy_spirit or 'No'}")
    print(f"   - RISE Attended: {person.rise_attended or 'No'}")
    print(f"   - First Served: {person.first_served_on or 'No'}")
    
    # Check DiscipleshipStep table
    discipleship_steps = DiscipleshipStep.query.filter_by(person_id=person.id).all()
    print(f"\nDiscipleship steps in table: {len(discipleship_steps)}")
    for step in discipleship_steps:
        print(f"   - {step.type}: {step.completed_at}")
    
    # Check pathway completions
    pathway_completions = PersonPathwayStepCompletion.query.filter_by(person_id=person.id).all()
    print(f"\nPathway step completions: {len(pathway_completions)}")
    for completion in pathway_completions[:5]:
        print(f"   - Step {completion.pathway_step_id}: {completion.completed_at}")
    
    # Check HeartbeatSnapshot
    print("\n" + "="*80)
    print("HEARTBEAT SNAPSHOT (Current)")
    print("="*80)
    snapshot = HeartbeatSnapshot.query.filter_by(
        person_id=person.id
    ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
    
    if not snapshot:
        print("❌ No heartbeat snapshot found")
    else:
        print(f"✅ Heartbeat snapshot found")
        print(f"   Calculated at: {snapshot.calculated_at}")
        print(f"   GATHER Score: {snapshot.gather_score}/100")
        print(f"   ENGAGEMENT Score: {snapshot.engagement_score}/100")
        print(f"   SPIRITUAL Score: {snapshot.spiritual_score}/100")
        print(f"   CARE Score: {snapshot.care_score}/100")
        print(f"   TOTAL Score: {snapshot.total_score}/100")
        print(f"   Status: {snapshot.status}")
        
        try:
            risk_reasons = json.loads(snapshot.risk_reasons or '[]')
            print(f"\n   Risk Factors ({len(risk_reasons)}):")
            for reason in risk_reasons:
                print(f"      - {reason}")
        except Exception as e:
            print(f"   ❌ Error parsing risk reasons: {e}")
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    with app.app_context():
        # Run diagnostic for Shannon
        diagnose_person('Shannon.langberg@futures.church')

