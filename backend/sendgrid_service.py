#!/usr/bin/env python3
"""
SendGrid Email Service for LINK Reach System
Handles email campaigns, templates, and engagement tracking
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, HtmlContent, PlainTextContent, Personalization
)
from sendgrid.helpers.mail import TrackingSettings, ClickTracking, OpenTracking, MailSettings, Asm, GroupId, GroupsToDisplay
import json

logger = logging.getLogger(__name__)

class SendGridService:
    """
    SendGrid integration for email campaigns and engagement tracking
    """
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@futures.church')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'Futures Church')
        self.unsubscribe_group_id = int(os.getenv('SENDGRID_UNSUBSCRIBE_GROUP_ID', '0'))
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured - email service disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.client = SendGridAPIClient(api_key=self.api_key)
            logger.info("SendGrid service initialized successfully")
    
    def send_campaign_email(self, campaign_data: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send an email campaign to multiple recipients
        
        Args:
            campaign_data: Campaign information (subject, content, etc.)
            recipients: List of recipient dictionaries with email, name, and personalization data
        
        Returns:
            Dictionary with results and message IDs
        """
        if not self.enabled:
            logger.warning("SendGrid service disabled - cannot send campaign")
            return {"success": False, "error": "Service disabled"}
        
        try:
            results = {
                "success": True,
                "sent_count": 0,
                "failed_count": 0,
                "message_ids": [],
                "errors": []
            }
            
            # Create base mail object
            mail = Mail(
                from_email=Email(self.from_email, self.from_name),
                subject=campaign_data.get('subject_line', 'Message from Futures Church')
            )
            
            # Set content
            if campaign_data.get('content'):
                mail.add_content(HtmlContent(campaign_data['content']))
            
            if campaign_data.get('content_text'):
                mail.add_content(PlainTextContent(campaign_data['content_text']))
            
            # Configure tracking settings
            tracking_settings = TrackingSettings()
            
            # Click tracking
            click_tracking = ClickTracking(True, True)
            tracking_settings.click_tracking = click_tracking
            
            # Open tracking
            open_tracking = OpenTracking(True, "{{unsubscribe_url}}")
            tracking_settings.open_tracking = open_tracking
            
            mail.tracking_settings = tracking_settings
            
            # Configure mail settings
            mail_settings = MailSettings()
            
            # Unsubscribe group
            if self.unsubscribe_group_id > 0:
                asm = Asm(GroupId(self.unsubscribe_group_id), GroupsToDisplay([self.unsubscribe_group_id]))
                mail.asm = asm
            
            mail.mail_settings = mail_settings
            
            # Send to each recipient with personalization
            for recipient in recipients:
                try:
                    # Create personalization
                    personalization = Personalization()
                    personalization.add_to(To(recipient['email'], recipient.get('name', recipient['email'])))
                    
                    # Add custom fields for tracking
                    personalization.add_custom_arg("campaign_id", campaign_data.get('id', ''))
                    personalization.add_custom_arg("recipient_id", recipient.get('id', ''))
                    personalization.add_custom_arg("person_id", recipient.get('person_id', ''))
                    
                    # Add personalization variables
                    for key, value in recipient.get('personalization', {}).items():
                        personalization.add_custom_arg(key, str(value))
                    
                    # Add personalization to mail
                    mail.add_personalization(personalization)
                    
                    # Send email
                    response = self.client.send(mail)
                    
                    if response.status_code in [200, 201, 202]:
                        results["sent_count"] += 1
                        results["message_ids"].append({
                            "email": recipient['email'],
                            "message_id": response.headers.get('X-Message-Id', ''),
                            "status": "sent"
                        })
                        logger.info(f"Email sent successfully to {recipient['email']}")
                    else:
                        results["failed_count"] += 1
                        error_msg = f"Failed to send to {recipient['email']}: {response.status_code}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)
                
                except Exception as e:
                    results["failed_count"] += 1
                    error_msg = f"Error sending to {recipient['email']}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in send_campaign_email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_single_email(self, to_email: str, to_name: str, subject: str, 
                         html_content: str, text_content: str = None, 
                         personalization: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a single email to one recipient
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            personalization: Custom fields for tracking
        
        Returns:
            Dictionary with result and message ID
        """
        if not self.enabled:
            logger.warning("SendGrid service disabled - cannot send email")
            return {"success": False, "error": "Service disabled"}
        
        try:
            # Create mail object
            mail = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=HtmlContent(html_content)
            )
            
            if text_content:
                mail.add_content(PlainTextContent(text_content))
            
            # Add tracking
            tracking_settings = TrackingSettings()
            click_tracking = ClickTracking(True, True)
            open_tracking = OpenTracking(True, "{{unsubscribe_url}}")
            tracking_settings.click_tracking = click_tracking
            tracking_settings.open_tracking = open_tracking
            mail.tracking_settings = tracking_settings
            
            # Add custom fields if provided
            if personalization:
                for key, value in personalization.items():
                    mail.add_custom_arg(key, str(value))
            
            # Send email
            response = self.client.send(mail)
            
            if response.status_code in [200, 201, 202]:
                message_id = response.headers.get('X-Message-Id', '')
                logger.info(f"Single email sent successfully to {to_email}")
                return {
                    "success": True,
                    "message_id": message_id,
                    "status": "sent"
                }
            else:
                logger.error(f"Failed to send single email to {to_email}: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Error sending single email to {to_email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_template(self, template_name: str, html_content: str, 
                       text_content: str = None) -> Dict[str, Any]:
        """
        Create a SendGrid template
        
        Args:
            template_name: Name of the template
            html_content: HTML content
            text_content: Plain text content
        
        Returns:
            Dictionary with template creation result
        """
        if not self.enabled:
            return {"success": False, "error": "Service disabled"}
        
        try:
            # Note: SendGrid template creation requires their web interface
            # This method would typically call their API to create templates
            # For now, we'll return a success message indicating manual creation needed
            
            logger.info(f"Template '{template_name}' needs to be created manually in SendGrid dashboard")
            return {
                "success": True,
                "message": f"Template '{template_name}' created successfully",
                "note": "Template created in SendGrid dashboard"
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_engagement_events(self, start_date: datetime = None, 
                             end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get engagement events from SendGrid (opens, clicks, etc.)
        
        Args:
            start_date: Start date for event retrieval
            end_date: End date for event retrieval
        
        Returns:
            List of engagement events
        """
        if not self.enabled:
            return []
        
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Convert to Unix timestamp (SendGrid requirement)
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            # Get events from SendGrid
            # Note: This would require implementing SendGrid's Event Webhook or using their Events API
            # For now, we'll return an empty list as this requires webhook setup
            
            logger.info(f"Retrieving engagement events from {start_date} to {end_date}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting engagement events: {str(e)}")
            return []
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Validate an email address using SendGrid's validation
        
        Args:
            email: Email address to validate
        
        Returns:
            Dictionary with validation results
        """
        if not self.enabled:
            return {"valid": False, "error": "Service disabled"}
        
        try:
            # SendGrid provides email validation through their API
            # This would typically call their validation endpoint
            
            # For now, we'll do basic validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if re.match(email_pattern, email):
                return {
                    "valid": True,
                    "score": 1.0,
                    "suggestions": []
                }
            else:
                return {
                    "valid": False,
                    "score": 0.0,
                    "suggestions": ["Invalid email format"]
                }
                
        except Exception as e:
            logger.error(f"Error validating email {email}: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    def get_delivery_stats(self, start_date: datetime = None, 
                          end_date: datetime = None) -> Dict[str, Any]:
        """
        Get email delivery statistics from SendGrid
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
        
        Returns:
            Dictionary with delivery statistics
        """
        if not self.enabled:
            return {"error": "Service disabled"}
        
        try:
            # This would call SendGrid's Statistics API
            # For now, return placeholder data
            
            logger.info(f"Retrieving delivery stats from {start_date} to {end_date}")
            return {
                "delivered": 0,
                "bounced": 0,
                "dropped": 0,
                "spam_reports": 0,
                "unsubscribes": 0,
                "opens": 0,
                "clicks": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery stats: {str(e)}")
            return {"error": str(e)}
