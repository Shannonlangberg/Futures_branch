#!/usr/bin/env python3
"""
Campaign Manager for LINK Reach System
Orchestrates email and SMS campaigns with targeting, scheduling, and engagement tracking
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from sqlalchemy import and_, or_, func
import json
import secrets
import hashlib

from models import db, Person
from communication_models import (
    Campaign, CampaignRecipient, EngagementEvent, CommunicationPreferences,
    CampaignType, CampaignStatus, EngagementType, EmailViewToken
)
from sendgrid_service import SendGridService
from twilio_service import TwilioService

logger = logging.getLogger(__name__)

class CampaignManager:
    """
    Manages the complete lifecycle of communication campaigns
    """
    
    def __init__(self):
        self.sendgrid_service = SendGridService()
        self.twilio_service = TwilioService()
        
        logger.info("Campaign Manager initialized")
    
    def create_campaign(self, campaign_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a new campaign
        
        Args:
            campaign_data: Campaign information
            user_id: ID of user creating the campaign
        
        Returns:
            Dictionary with campaign creation result
        """
        try:
            # Validate campaign data
            required_fields = ['name', 'campaign_type', 'content']
            for field in required_fields:
                if not campaign_data.get(field):
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Create campaign record
            campaign = Campaign(
                name=campaign_data['name'],
                description=campaign_data.get('description', ''),
                campaign_type=CampaignType(campaign_data['campaign_type']),
                subject_line=campaign_data.get('subject_line'),
                content=campaign_data['content'],
                content_text=campaign_data.get('content_text'),
                target_criteria=campaign_data.get('target_criteria', {}),
                scheduled_at=campaign_data.get('scheduled_at'),
                created_by=user_id
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            logger.info(f"Campaign created: {campaign.id} - {campaign.name}")
            
            return {
                "success": True,
                "campaign_id": campaign.id,
                "message": "Campaign created successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating campaign: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_target_recipients(self, target_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of recipients based on targeting criteria
        
        Args:
            target_criteria: Targeting criteria (campus, department, tags, etc.)
        
        Returns:
            List of recipient dictionaries
        """
        try:
            # Build query
            query = db.session.query(Person).filter(Person.is_active == True)
            
            # Apply campus filter
            if target_criteria.get('campus'):
                campuses = target_criteria['campus']
                if isinstance(campuses, str):
                    campuses = [campuses]
                query = query.filter(Person.campus.in_(campuses))
            
            # Apply department filter
            if target_criteria.get('department'):
                departments = target_criteria['department']
                if isinstance(departments, str):
                    departments = [departments]
                query = query.filter(Person.department.in_(departments))
            
            # Apply tags filter
            if target_criteria.get('tags'):
                tags = target_criteria['tags']
                if isinstance(tags, str):
                    tags = [tags]
                
                # Search for people with any of the specified tags
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append(Person.tags.contains([tag]))
                
                if tag_conditions:
                    query = query.filter(or_(*tag_conditions))
            
            # Apply engagement level filter
            if target_criteria.get('engagement_level'):
                engagement_level = target_criteria['engagement_level']
                # This would integrate with your existing engagement scoring system
                # For now, we'll skip this filter
                pass
            
            # Apply communication preferences filter
            if target_criteria.get('communication_channels'):
                channels = target_criteria['communication_channels']
                if isinstance(channels, str):
                    channels = [channels]
                
                # Filter by communication preferences
                for channel in channels:
                    if channel == 'email':
                        query = query.join(CommunicationPreferences).filter(
                            CommunicationPreferences.email_enabled == True
                        )
                    elif channel == 'sms':
                        query = query.join(CommunicationPreferences).filter(
                            CommunicationPreferences.sms_enabled == True
                        )
            
            # Execute query
            recipients = query.all()
            
            # Convert to dictionaries
            recipient_list = []
            for person in recipients:
                recipient_data = {
                    'id': person.id,
                    'person_id': person.id,
                    'name': person.preferred_name or person.full_name,
                    'email': person.email,
                    'phone': person.phone,
                    'campus': person.campus,
                    'department': person.department,
                    'personalization': {
                        'name': person.preferred_name or person.full_name,
                        'campus': person.campus,
                        'department': person.department
                    }
                }
                
                # Add additional personalization based on person data
                if person.dna_completed:
                    recipient_data['personalization']['dna_completed'] = 'Yes'
                if person.baptised_on:
                    recipient_data['personalization']['baptised'] = 'Yes'
                if person.connect_group:
                    recipient_data['personalization']['connect_group'] = person.connect_group
                
                recipient_list.append(recipient_data)
            
            logger.info(f"Found {len(recipient_list)} recipients for targeting criteria")
            return recipient_list
            
        except Exception as e:
            logger.error(f"Error getting target recipients: {str(e)}")
            return []
    
    def schedule_campaign(self, campaign_id: str, scheduled_time: datetime) -> Dict[str, Any]:
        """
        Schedule a campaign for future delivery
        
        Args:
            campaign_id: Campaign ID
            scheduled_time: When to send the campaign
        
        Returns:
            Dictionary with scheduling result
        """
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign.status != CampaignStatus.DRAFT:
                return {"success": False, "error": "Campaign must be in draft status to schedule"}
            
            # Update campaign
            campaign.status = CampaignStatus.SCHEDULED
            campaign.scheduled_at = scheduled_time
            
            db.session.commit()
            
            logger.info(f"Campaign {campaign_id} scheduled for {scheduled_time}")
            
            return {
                "success": True,
                "message": "Campaign scheduled successfully",
                "scheduled_at": scheduled_time.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error scheduling campaign {campaign_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Send a campaign immediately
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Dictionary with sending result
        """
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
                return {"success": False, "error": "Campaign cannot be sent in current status"}
            
            # Get target recipients
            recipients = self.get_target_recipients(campaign.target_criteria)
            if not recipients:
                return {"success": False, "error": "No recipients found for targeting criteria"}
            
            # Update campaign status
            campaign.status = CampaignStatus.ACTIVE
            campaign.total_recipients = len(recipients)
            campaign.sent_at = datetime.utcnow()
            
            # Create recipient records
            recipient_records = []
            for recipient in recipients:
                recipient_record = CampaignRecipient(
                    campaign_id=campaign_id,
                    person_id=recipient['person_id'],
                    email=recipient.get('email'),
                    phone=recipient.get('phone')
                )
                recipient_records.append(recipient_record)
                db.session.add(recipient_record)
            
            db.session.commit()
            
            # Send campaign based on type
            if campaign.campaign_type == CampaignType.EMAIL:
                send_result = self._send_email_campaign(campaign, recipients)
            elif campaign.campaign_type == CampaignType.SMS:
                send_result = self._send_sms_campaign(campaign, recipients)
            else:
                return {"success": False, "error": f"Unsupported campaign type: {campaign.campaign_type}"}
            
            # Update campaign metrics
            if send_result.get('success'):
                campaign.sent_count = send_result.get('sent_count', 0)
                campaign.delivered_count = send_result.get('delivered_count', 0)
                campaign.status = CampaignStatus.COMPLETED
                db.session.commit()
            
            return send_result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sending campaign {campaign_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_view_token(self, campaign_id: str, recipient_id: str, person_id: str = None) -> str:
        """
        Generate a secure token for viewing email online
        
        Args:
            campaign_id: Campaign ID
            recipient_id: Recipient ID
            person_id: Person ID (optional)
        
        Returns:
            Secure token string
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Create token record (expires in 90 days)
        expires_at = datetime.utcnow() + timedelta(days=90)
        
        view_token = EmailViewToken(
            campaign_id=campaign_id,
            recipient_id=recipient_id,
            person_id=person_id,
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(view_token)
        db.session.commit()
        
        return token
    
    def _add_view_online_link(self, html_content: str, token: str, base_url: str = None) -> str:
        """
        Add a "View Online" link to email content
        
        Args:
            html_content: Original HTML content
            token: Secure view token
            base_url: Base URL for the application
        
        Returns:
            HTML content with view online link
        """
        if not base_url:
            base_url = os.getenv('BASE_URL', 'https://ranch-production.up.railway.app')
        
        view_url = f"{base_url}/view-email/{token}"
        
        # Add view online link at the top of the email
        view_online_html = f'''
        <div style="background-color: #f3f4f6; padding: 15px; text-align: center; margin-bottom: 20px; border-bottom: 2px solid #e5e7eb;">
            <p style="margin: 0; color: #6b7280; font-size: 12px;">
                Having trouble viewing this email? 
                <a href="{view_url}" style="color: #3b82f6; text-decoration: none; font-weight: 600;">View it in your browser</a>
            </p>
        </div>
        '''
        
        # Insert view online link at the beginning of the body
        if '<body' in html_content:
            html_content = html_content.replace('<body', f'{view_online_html}<body', 1)
        elif '<html' in html_content:
            html_content = html_content.replace('<html>', f'<html>{view_online_html}', 1)
        else:
            # If no body tag, prepend to content
            html_content = view_online_html + html_content
        
        return html_content
    
    def _send_email_campaign(self, campaign: Campaign, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send email campaign using SendGrid
        
        Args:
            campaign: Campaign object
            recipients: List of recipients
        
        Returns:
            Dictionary with sending results
        """
        try:
            # Generate view tokens for each recipient and add view online links
            base_url = os.getenv('BASE_URL', 'https://ranch-production.up.railway.app')
            
            # Prepare campaign data for SendGrid
            campaign_data = {
                'id': campaign.id,
                'subject_line': campaign.subject_line,
                'content': campaign.content,
                'content_text': campaign.content_text
            }
            
            # Generate tokens and add view online links for each recipient
            for recipient in recipients:
                # Get or create recipient record
                recipient_record = CampaignRecipient.query.filter_by(
                    campaign_id=campaign.id,
                    person_id=recipient.get('person_id')
                ).first()
                
                if recipient_record:
                    # Generate view token
                    token = self._generate_view_token(
                        campaign.id,
                        recipient_record.id,
                        recipient.get('person_id')
                    )
                    
                    # Add view online link to content for this recipient
                    recipient['view_token'] = token
                    recipient['html_content'] = self._add_view_online_link(
                        campaign.content,
                        token,
                        base_url
                    )
                else:
                    # Fallback: use original content
                    recipient['html_content'] = campaign.content
            
            # Update campaign data with view online links
            # Note: We'll send personalized content per recipient
            modified_recipients = []
            for recipient in recipients:
                if 'html_content' in recipient:
                    modified_recipient = recipient.copy()
                    modified_recipient['content'] = recipient['html_content']
                    modified_recipients.append(modified_recipient)
                else:
                    modified_recipients.append(recipient)
            
            # Send campaign with modified recipients
            result = self.sendgrid_service.send_campaign_email(campaign_data, modified_recipients)
            
            if result.get('success'):
                # Update recipient records with message IDs
                for msg_info in result.get('message_ids', []):
                    recipient = next((r for r in recipients if r['email'] == msg_info['email']), None)
                    if recipient:
                        recipient_record = CampaignRecipient.query.filter_by(
                            campaign_id=campaign.id,
                            person_id=recipient['person_id']
                        ).first()
                        
                        if recipient_record:
                            recipient_record.sendgrid_message_id = msg_info.get('message_id', '')
                            recipient_record.sent_at = datetime.utcnow()
                            recipient_record.delivered_at = datetime.utcnow()
                
                db.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending email campaign: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_sms_campaign(self, campaign: Campaign, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send SMS campaign using Twilio
        
        Args:
            campaign: Campaign object
            recipients: List of recipients
        
        Returns:
            Dictionary with sending results
        """
        try:
            # Prepare campaign data for Twilio
            campaign_data = {
                'id': campaign.id,
                'content': campaign.content
            }
            
            # Send campaign
            result = self.twilio_service.send_campaign_sms(campaign_data, recipients)
            
            if result.get('success'):
                # Update recipient records with message SIDs
                for msg_info in result.get('message_sids', []):
                    recipient = next((r for r in recipients if r['phone'] == msg_info['phone']), None)
                    if recipient:
                        recipient_record = CampaignRecipient.query.filter_by(
                            campaign_id=campaign.id,
                            person_id=recipient['person_id']
                        ).first()
                        
                        if recipient_record:
                            recipient_record.twilio_message_sid = msg_info.get('message_sid', '')
                            recipient_record.sent_at = datetime.utcnow()
                            recipient_record.delivered_at = datetime.utcnow()
                
                db.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS campaign: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def track_engagement(self, event_type: str, campaign_id: str, recipient_id: str, 
                        person_id: str, external_id: str = None, event_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Track engagement events (opens, clicks, replies, etc.)
        
        Args:
            event_type: Type of engagement event
            campaign_id: Campaign ID
            recipient_id: Recipient ID
            person_id: Person ID
            external_id: External service ID (SendGrid/Twilio)
            event_data: Additional event data
        
        Returns:
            Dictionary with tracking result
        """
        try:
            # Determine points based on event type
            points_map = {
                EngagementType.OPEN.value: 3,      # Email open
                EngagementType.CLICK.value: 5,     # Email click
                EngagementType.REPLY.value: 8,     # Email reply
                EngagementType.SMS_DELIVERED.value: 1,  # SMS delivered
                EngagementType.SMS_READ.value: 3,   # SMS read
                EngagementType.SMS_REPLY.value: 8   # SMS reply
            }
            
            points_earned = points_map.get(event_type, 0)
            
            # Create engagement event
            engagement_event = EngagementEvent(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                person_id=person_id,
                event_type=EngagementType(event_type),
                points_earned=points_earned,
                external_id=external_id,
                event_data=event_data
            )
            
            db.session.add(engagement_event)
            
            # Update recipient record
            recipient_record = CampaignRecipient.query.get(recipient_id)
            if recipient_record:
                if event_type == EngagementType.OPEN.value:
                    recipient_record.opened_at = datetime.utcnow()
                elif event_type == EngagementType.CLICK.value:
                    recipient_record.clicked_at = datetime.utcnow()
                elif event_type == EngagementType.REPLY.value:
                    recipient_record.replied_at = datetime.utcnow()
                elif event_type == EngagementType.SMS_DELIVERED.value:
                    recipient_record.delivered_at = datetime.utcnow()
            
            # Update campaign metrics
            campaign = Campaign.query.get(campaign_id)
            if campaign:
                if event_type == EngagementType.OPEN.value:
                    campaign.open_count += 1
                elif event_type == EngagementType.CLICK.value:
                    campaign.click_count += 1
                elif event_type == EngagementType.REPLY.value:
                    campaign.reply_count += 1
            
            # Update person's engagement profile for heartbeat tracking
            person = Person.query.get(person_id)
            if person and person.engagement_profile:
                try:
                    engagement_date = datetime.utcnow().date()
                    campaign_type_str = campaign.campaign_type.value if campaign else 'general'
                    
                    # Track email engagement (opens, clicks, replies)
                    if event_type == EngagementType.OPEN.value:
                        person.engagement_profile.add_email_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='open',
                            engagement_date=engagement_date
                        )
                    elif event_type == EngagementType.CLICK.value:
                        person.engagement_profile.add_email_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='click',
                            engagement_date=engagement_date
                        )
                    elif event_type == EngagementType.REPLY.value:
                        person.engagement_profile.add_email_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='reply',
                            engagement_date=engagement_date
                        )
                    # Track SMS engagement (delivered, read, reply)
                    elif event_type == EngagementType.SMS_DELIVERED.value:
                        person.engagement_profile.add_sms_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='delivered',
                            engagement_date=engagement_date
                        )
                    elif event_type == EngagementType.SMS_READ.value:
                        person.engagement_profile.add_sms_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='read',
                            engagement_date=engagement_date
                        )
                    elif event_type == EngagementType.SMS_REPLY.value:
                        person.engagement_profile.add_sms_engagement(
                            campaign_type=campaign_type_str,
                            engagement_type='reply',
                            engagement_date=engagement_date
                        )
                    
                    logger.info(f"Updated engagement profile for person {person_id} with {event_type}")
                except Exception as e:
                    logger.error(f"Error updating engagement profile for campaign engagement: {e}")
                    # Don't fail the tracking if profile update fails
            
            db.session.commit()
            
            logger.info(f"Engagement tracked: {event_type} for campaign {campaign_id}, person {person_id}")
            
            return {
                "success": True,
                "points_earned": points_earned,
                "event_id": engagement_event.id
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error tracking engagement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a campaign
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Dictionary with campaign analytics
        """
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return {"error": "Campaign not found"}
            
            # Get recipient statistics
            total_recipients = campaign.total_recipients
            sent_count = campaign.sent_count
            delivered_count = campaign.delivered_count
            open_count = campaign.open_count
            click_count = campaign.click_count
            reply_count = campaign.reply_count
            
            # Calculate rates
            delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
            open_rate = (open_count / delivered_count * 100) if delivered_count > 0 else 0
            click_rate = (click_count / delivered_count * 100) if delivered_count > 0 else 0
            reply_rate = (reply_count / delivered_count * 100) if delivered_count > 0 else 0
            
            # Get engagement events breakdown
            engagement_events = db.session.query(
                EngagementEvent.event_type,
                func.count(EngagementEvent.id).label('count')
            ).filter(
                EngagementEvent.campaign_id == campaign_id
            ).group_by(EngagementEvent.event_type).all()
            
            engagement_breakdown = {}
            for event_type, count in engagement_events:
                engagement_breakdown[event_type] = count
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "campaign_type": campaign.campaign_type.value,
                "status": campaign.status.value,
                "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
                "metrics": {
                    "total_recipients": total_recipients,
                    "sent_count": sent_count,
                    "delivered_count": delivered_count,
                    "open_count": open_count,
                    "click_count": click_count,
                    "reply_count": reply_count
                },
                "rates": {
                    "delivery_rate": round(delivery_rate, 2),
                    "open_rate": round(open_rate, 2),
                    "click_rate": round(click_rate, 2),
                    "reply_rate": round(reply_rate, 2)
                },
                "engagement_breakdown": engagement_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics for {campaign_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_campaigns(self, status: str = None, campaign_type: str = None, 
                     limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get list of campaigns with optional filtering
        
        Args:
            status: Filter by campaign status
            campaign_type: Filter by campaign type
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip
        
        Returns:
            List of campaign dictionaries
        """
        try:
            query = Campaign.query
            
            if status:
                query = query.filter(Campaign.status == CampaignStatus(status))
            
            if campaign_type:
                query = query.filter(Campaign.campaign_type == CampaignType(campaign_type))
            
            # Order by creation date (newest first)
            query = query.order_by(Campaign.created_at.desc())
            
            # Apply pagination
            campaigns = query.limit(limit).offset(offset).all()
            
            # Convert to dictionaries
            campaign_list = []
            for campaign in campaigns:
                campaign_list.append(campaign.to_dict())
            
            return campaign_list
            
        except Exception as e:
            logger.error(f"Error getting campaigns: {str(e)}")
            return []
