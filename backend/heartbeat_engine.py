# heartbeat_engine.py
"""
Heartbeat Engine Service

Calculates health scores for congregants based on:
- Gather (attendance)
- Engagement (connect groups, serving, events, giving)
- Spiritual (discipleship milestones)
- Care (pastoral care cases)
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from models import (
    db, Person, Campus, Service, AttendanceEvent, HeartbeatConnectGroup,
    ConnectAttendance, Team, ServingAssignment, GivingSummary,
    DiscipleshipStep, CareCase, CareTouchpoint, HeartbeatSnapshot,
    PersonPathwayProgress, PersonPathwayStepCompletion, PathwayStep
)
import json
import logging

logger = logging.getLogger(__name__)


class HeartbeatEngine:
    """Service for calculating and persisting Heartbeat health scores"""
    
    def __init__(self):
        self.weights = {
            'gather': 0.35,
            'engagement': 0.25,
            'spiritual': 0.25,
            'care': 0.15
        }
    
    def calculate_heartbeat(
        self,
        person_id: str,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None
    ) -> HeartbeatSnapshot:
        """
        Calculate heartbeat for a person and persist snapshot.
        
        Args:
            person_id: Person ID to calculate for
            date_range_start: Optional start date for calculation window
            date_range_end: Optional end date for calculation window
            
        Returns:
            HeartbeatSnapshot object
        """
        person = Person.query.get(person_id)
        if not person:
            raise ValueError(f"Person {person_id} not found")
        
        # Default to last 12 weeks if no range provided
        if date_range_end is None:
            date_range_end = date.today()
        if date_range_start is None:
            date_range_start = date_range_end - timedelta(weeks=12)
        
        # Get campus_id from person (map from campus string to campus_id)
        campus_id = self._get_campus_id(person.campus)
        
        # Load relevant data
        data = self._load_person_data(person_id, date_range_start, date_range_end)
        
        # Calculate individual scores
        gather_score = self._calculate_gather_score(data, date_range_start, date_range_end)
        engagement_score = self._calculate_engagement_score(data, date_range_start, date_range_end)
        spiritual_score = self._calculate_spiritual_score(data, date_range_start, date_range_end)
        care_score = self._calculate_care_score(data)
        
        # Calculate total score
        total_score = (
            gather_score * self.weights['gather'] +
            engagement_score * self.weights['engagement'] +
            spiritual_score * self.weights['spiritual'] +
            care_score * self.weights['care']
        )
        
        # Determine status
        status = self._determine_status(total_score)
        
        # Generate risk reasons
        risk_reasons = self._generate_risk_reasons(
            data, gather_score, engagement_score, spiritual_score, care_score, total_score
        )
        
        # Create or update snapshot
        snapshot = HeartbeatSnapshot.query.filter_by(
            person_id=person_id
        ).order_by(HeartbeatSnapshot.calculated_at.desc()).first()
        
        if snapshot:
            # Update existing snapshot
            snapshot.calculated_at = datetime.utcnow()
            snapshot.campus_id = campus_id
            snapshot.gather_score = gather_score
            snapshot.engagement_score = engagement_score
            snapshot.spiritual_score = spiritual_score
            snapshot.care_score = care_score
            snapshot.total_score = total_score
            snapshot.status = status
            snapshot.risk_reasons = json.dumps(risk_reasons)
        else:
            # Create new snapshot
            snapshot = HeartbeatSnapshot(
                person_id=person_id,
                campus_id=campus_id,
                calculated_at=datetime.utcnow(),
                gather_score=gather_score,
                engagement_score=engagement_score,
                spiritual_score=spiritual_score,
                care_score=care_score,
                total_score=total_score,
                status=status,
                risk_reasons=json.dumps(risk_reasons)
            )
            db.session.add(snapshot)
        
        db.session.commit()
        return snapshot
    
    def _get_campus_id(self, campus_name: str) -> str:
        """Map campus name to campus_id, creating if needed"""
        # Normalize campus name
        campus_normalized = campus_name.lower().replace(' ', '_')
        
        # Try to find existing campus
        campus = Campus.query.filter_by(id=campus_normalized).first()
        if not campus:
            # Create if doesn't exist
            campus = Campus(
                id=campus_normalized,
                name=campus_name,
                timezone='UTC',
                is_active=True
            )
            db.session.add(campus)
            db.session.commit()
        
        return campus.id
    
    def _load_person_data(
        self,
        person_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Load all relevant data for a person in the date range"""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get Sunday services in date range
        sunday_services = Service.query.filter(
            Service.type == 'sunday',
            Service.starts_at >= start_datetime,
            Service.starts_at <= end_datetime
        ).all()
        service_ids = [s.id for s in sunday_services]
        
        # Attendance events
        attendance_events = AttendanceEvent.query.filter(
            AttendanceEvent.person_id == person_id,
            AttendanceEvent.service_id.in_(service_ids) if service_ids else False
        ).all()
        
        # Connect group attendance
        connect_attendance = ConnectAttendance.query.filter(
            ConnectAttendance.person_id == person_id,
            ConnectAttendance.date >= start_date,
            ConnectAttendance.date <= end_date
        ).all()
        
        # Active connect groups (person is a member)
        # Get groups where person has attendance records
        group_ids_with_attendance = db.session.query(ConnectAttendance.connect_group_id).filter(
            ConnectAttendance.person_id == person_id,
            ConnectAttendance.date >= start_date
        ).distinct().all()
        group_ids = [gid[0] for gid in group_ids_with_attendance]
        
        active_groups = HeartbeatConnectGroup.query.filter(
            HeartbeatConnectGroup.id.in_(group_ids) if group_ids else False,
            HeartbeatConnectGroup.is_active == True
        ).all()
        
        # Serving assignments
        serving_assignments = ServingAssignment.query.filter(
            ServingAssignment.person_id == person_id,
            ServingAssignment.service_id.in_(service_ids) if service_ids else False
        ).all()
        
        # Giving summaries
        giving_summaries = GivingSummary.query.filter(
            GivingSummary.person_id == person_id,
            GivingSummary.period_end >= start_date,
            GivingSummary.period_start <= end_date
        ).all()
        
        # Discipleship steps (legacy)
        discipleship_steps = DiscipleshipStep.query.filter(
            DiscipleshipStep.person_id == person_id
        ).all()
        
        # Pathway progress and step completions (new system)
        pathway_progress = PersonPathwayProgress.query.filter_by(
            person_id=person_id,
            is_active=True
        ).all()
        
        # Get all completed pathway steps
        pathway_step_completions = []
        for progress in pathway_progress:
            completions = progress.step_completions.all()
            for completion in completions:
                if completion.pathway_step:
                    pathway_step_completions.append(completion.pathway_step)
        
        # Care cases
        care_cases = CareCase.query.filter(
            CareCase.person_id == person_id
        ).all()
        
        # Care touchpoints
        care_case_ids = [c.id for c in care_cases]
        care_touchpoints = CareTouchpoint.query.filter(
            CareTouchpoint.care_case_id.in_(care_case_ids) if care_case_ids else False
        ).all() if care_case_ids else []
        
        return {
            'attendance_events': attendance_events,
            'sunday_services': sunday_services,
            'connect_attendance': connect_attendance,
            'active_groups': active_groups,
            'serving_assignments': serving_assignments,
            'giving_summaries': giving_summaries,
            'discipleship_steps': discipleship_steps,
            'pathway_step_completions': pathway_step_completions,
            'care_cases': care_cases,
            'care_touchpoints': care_touchpoints
        }
    
    def _calculate_gather_score(
        self,
        data: Dict,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate gather score (0-100) based on Sunday attendance.
        
        Based on:
        - Last 12 weeks of Sunday attendance
        - Absence streaks
        """
        attendance_events = data['attendance_events']
        sunday_services = data['sunday_services']
        
        if not sunday_services:
            return 0.0
        
        # Count attended services
        attended_count = len(attendance_events)
        total_services = len(sunday_services)
        
        # Base score from attendance frequency
        if total_services == 0:
            attendance_rate = 0.0
        else:
            attendance_rate = min(attended_count / total_services, 1.0)
        
        base_score = attendance_rate * 100.0
        
        # Penalty for absence streaks
        if attendance_events:
            # Sort by date
            sorted_events = sorted(
                attendance_events,
                key=lambda e: e.service.starts_at if e.service else datetime.min
            )
            
            # Find longest absence streak
            max_streak = 0
            current_streak = 0
            
            service_dates = sorted([s.starts_at.date() for s in sunday_services])
            attended_dates = set([
                e.service.starts_at.date() for e in sorted_events
                if e.service
            ])
            
            for service_date in service_dates:
                if service_date not in attended_dates:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            
            # Penalty: -5 points per week in longest streak (max -30)
            streak_penalty = min(max_streak * 5, 30)
            base_score = max(0, base_score - streak_penalty)
        else:
            # No attendance at all
            base_score = 0.0
        
        return round(base_score, 2)
    
    def _calculate_engagement_score(
        self,
        data: Dict,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate engagement score (0-100) based on:
        - Connect group membership and attendance
        - Serving frequency
        - Event attendance (future: can add Event model)
        - Giving frequency
        """
        scores = []
        
        # 1. Connect Group (40% of engagement)
        active_groups = data['active_groups']
        connect_attendance = data['connect_attendance']
        
        # Check if in active group OR has attendance records (attendance is proof of membership)
        in_group = len(active_groups) > 0
        has_attendance = len(connect_attendance) > 0
        
        # Calculate attendance rate in groups
        if connect_attendance:
            present_count = len([a for a in connect_attendance if a.status == 'present'])
            total_meetings = len(connect_attendance)
            group_attendance_rate = present_count / total_meetings if total_meetings > 0 else 0.0
        else:
            group_attendance_rate = 0.0
        
        # Give credit for attendance even if group isn't marked as "active" in system
        # Attendance records are proof of group membership
        connect_score = 0.0
        if in_group or has_attendance:
            # If they have attendance, they're in a group (even if not marked active)
            # Calculate score based on attendance rate
            # Target: attend at least once every 2 weeks (6 times in 12 weeks)
            weeks_in_range = (end_date - start_date).days / 7
            target_attendances = max(1, int(weeks_in_range / 2))
            attendance_count = len([a for a in connect_attendance if a.status == 'present']) if connect_attendance else 0
            attendance_rate = min(attendance_count / target_attendances, 1.0) if target_attendances > 0 else 0.0
            connect_score = 40.0 * attendance_rate
        else:
            connect_score = 0.0  # Not in a group and no attendance
        
        scores.append(('connect', connect_score))
        
        # 2. Serving (30% of engagement)
        serving_assignments = data['serving_assignments']
        served_count = len([s for s in serving_assignments if s.status == 'served'])
        
        # Target: serve at least once every 4 weeks
        weeks_in_range = (end_date - start_date).days / 7
        target_serves = max(1, int(weeks_in_range / 4))
        serving_rate = min(served_count / target_serves, 1.0) if target_serves > 0 else 0.0
        serving_score = 30.0 * serving_rate
        
        scores.append(('serving', serving_score))
        
        # 3. Giving (30% of engagement)
        giving_summaries = data['giving_summaries']
        
        if giving_summaries:
            # Use most recent summary
            latest_summary = max(giving_summaries, key=lambda g: g.period_end)
            
            # Map frequency to score
            frequency_scores = {
                'weekly': 30.0,
                'monthly': 20.0,
                'occasional': 10.0,
                'none': 0.0
            }
            giving_score = frequency_scores.get(latest_summary.frequency, 0.0)
            
            # Boost with pattern_score
            giving_score += latest_summary.pattern_score * 10.0
            giving_score = min(30.0, giving_score)
        else:
            giving_score = 0.0
        
        scores.append(('giving', giving_score))
        
        # Total engagement score
        total_engagement = sum(score for _, score in scores)
        return round(total_engagement, 2)
    
    def _calculate_spiritual_score(
        self,
        data: Dict,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate spiritual score (0-100) based on:
        - Salvation milestone (from DiscipleshipStep or PathwayStep)
        - Baptism milestone (from DiscipleshipStep or PathwayStep)
        - Holy Spirit milestone (from DiscipleshipStep or PathwayStep)
        - Recent next steps
        - Other discipleship milestones
        """
        discipleship_steps = data['discipleship_steps']
        pathway_step_completions = data.get('pathway_step_completions', [])
        
        # If no data at all, return 0
        if not discipleship_steps and not pathway_step_completions:
            return 0.0
        
        score = 0.0
        
        # Check for major milestones from both sources
        # From legacy DiscipleshipStep
        has_salvation = any(s.type == 'salvation' for s in discipleship_steps)
        has_baptism = any(s.type == 'baptism' for s in discipleship_steps)
        has_holy_spirit = any(s.type == 'holy_spirit' for s in discipleship_steps)
        
        # From new PathwayStep completions (check milestone_type)
        for step in pathway_step_completions:
            milestone_type = (step.milestone_type or '').lower()
            if milestone_type == 'salvation':
                has_salvation = True
            elif milestone_type == 'baptism':
                has_baptism = True
            elif milestone_type == 'holy_spirit':
                has_holy_spirit = True
        
        # Major milestones (60 points total)
        if has_salvation:
            score += 20.0
        if has_baptism:
            score += 20.0
        if has_holy_spirit:
            score += 20.0
        
        # Recent next steps (30 points)
        # Check legacy DiscipleshipStep
        recent_steps = [
            s for s in discipleship_steps
            if s.type == 'next_steps' and s.date >= start_date
        ]
        # Check pathway steps with next_steps milestone_type
        for step in pathway_step_completions:
            if (step.milestone_type or '').lower() == 'next_steps':
                # Check if completion date is recent (if available)
                # For now, count all pathway next_steps as recent
                recent_steps.append(step)
        
        if recent_steps:
            # 10 points per recent next step, max 30
            score += min(len(recent_steps) * 10.0, 30.0)
        
        # Other milestones (10 points)
        # From legacy DiscipleshipStep
        other_milestones = [
            s for s in discipleship_steps
            if s.type not in ['salvation', 'baptism', 'holy_spirit', 'next_steps']
        ]
        # From pathway steps
        for step in pathway_step_completions:
            milestone_type = (step.milestone_type or '').lower()
            if milestone_type not in ['salvation', 'baptism', 'holy_spirit', 'next_steps']:
                other_milestones.append(step)
        
        if other_milestones:
            score += min(len(other_milestones) * 2.0, 10.0)
        
        return round(min(score, 100.0), 2)
    
    def _calculate_care_score(self, data: Dict) -> float:
        """
        Calculate care score (0-100) based on:
        - Open care cases and their priority
        - Recent touchpoints (positive indicator)
        """
        care_cases = data['care_cases']
        care_touchpoints = data['care_touchpoints']
        
        # Start with 100 (no care needed = healthy)
        score = 100.0
        
        # Penalties for open cases
        open_cases = [c for c in care_cases if c.status in ['open', 'in_progress']]
        
        # Debug logging for care score calculation
        if open_cases:
            logger.debug(f"Calculating care score: {len(open_cases)} open cases")
        
        for case in open_cases:
            priority_penalties = {
                'high': 30.0,
                'medium': 15.0,
                'low': 5.0
            }
            # Handle None or invalid priority values
            case_priority = case.priority if case.priority else 'low'
            penalty = priority_penalties.get(case_priority.lower() if isinstance(case_priority, str) else 'low', 5.0)
            score -= penalty
            
            logger.debug(f"  Case: {case.type}, priority={case_priority}, penalty={penalty}, new_score={score}")
        
        # Bonus for recent touchpoints (shows active care)
        recent_touchpoints = [
            t for t in care_touchpoints
            if t.created_at >= datetime.utcnow() - timedelta(days=14)
        ]
        if recent_touchpoints:
            # Add 5 points per recent touchpoint, max +20
            bonus = min(len(recent_touchpoints) * 5.0, 20.0)
            score += bonus
            logger.debug(f"  Recent touchpoints: {len(recent_touchpoints)}, bonus={bonus}, final_score={score}")
        
        final_score = round(max(0.0, min(score, 100.0)), 2)
        
        # Warn if score is unexpectedly low without open cases
        if final_score < 50 and len(open_cases) == 0:
            logger.warning(f"Care score is {final_score} but no open cases found. This may indicate a calculation bug.")
        
        return final_score
    
    def _determine_status(self, total_score: float) -> str:
        """Determine status bucket from total score"""
        if total_score >= 80:
            return 'healthy'
        elif total_score >= 60:
            return 'watch'
        elif total_score >= 40:
            return 'at_risk'
        else:
            return 'critical'
    
    def _generate_risk_reasons(
        self,
        data: Dict,
        gather_score: float,
        engagement_score: float,
        spiritual_score: float,
        care_score: float,
        total_score: float
    ) -> List[str]:
        """Generate list of risk reasons explaining the score"""
        reasons = []
        
        # Gather reasons
        if gather_score < 50:
            attendance_events = data['attendance_events']
            if not attendance_events:
                reasons.append('no_attendance_recorded')
            else:
                # Check for absence streak
                # This is simplified - could be more sophisticated
                reasons.append(f'low_attendance_score_{int(gather_score)}')
        
        # Engagement reasons
        if engagement_score < 50:
            active_groups = data['active_groups']
            serving_assignments = data['serving_assignments']
            giving_summaries = data['giving_summaries']
            
            if not active_groups:
                reasons.append('no_connect_group')
            
            served_count = len([s for s in serving_assignments if s.status == 'served'])
            if served_count == 0:
                reasons.append('no_serving')
            
            if not giving_summaries or all(g.frequency == 'none' for g in giving_summaries):
                reasons.append('no_giving')
        
        # Spiritual reasons
        if spiritual_score < 40:
            discipleship_steps = data['discipleship_steps']
            has_salvation = any(s.type == 'salvation' for s in discipleship_steps)
            if not has_salvation:
                reasons.append('no_salvation_milestone')
        
        # Care reasons
        if care_score < 70:
            care_cases = data['care_cases']
            open_cases = [c for c in care_cases if c.status in ['open', 'in_progress']]
            high_priority = [c for c in open_cases if c.priority == 'high']
            
            if high_priority:
                reasons.append('open_high_priority_case')
            elif open_cases:
                reasons.append('open_care_case')
        
        # Overall status
        if total_score < 40:
            reasons.append('critical_health_score')
        elif total_score < 60:
            reasons.append('at_risk_health_score')
        
        return reasons if reasons else ['healthy']
    
    def recalculate_campus(self, campus_id: str) -> Dict[str, int]:
        """
        Recalculate heartbeat for all active people in a campus.
        
        Returns:
            Dict with 'processed' and 'errors' counts
        """
        # Get all active people for this campus
        # Map campus_id back to campus name for Person query
        campus = Campus.query.get(campus_id)
        if not campus:
            raise ValueError(f"Campus {campus_id} not found")
        
        # Find people by campus name (Person.campus is a string)
        people = Person.query.filter_by(
            campus=campus.name,
            is_active=True
        ).all()
        
        processed = 0
        errors = 0
        
        for person in people:
            try:
                self.calculate_heartbeat(person.id)
                processed += 1
            except Exception as e:
                logger.error(f"Error calculating heartbeat for person {person.id}: {e}")
                errors += 1
        
        return {
            'processed': processed,
            'errors': errors,
            'total': len(people)
        }

