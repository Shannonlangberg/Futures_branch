#!/usr/bin/env python3
"""
Twilio SMS Service for LINK Reach System
Handles SMS campaigns, two-way messaging, and engagement tracking
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import json

logger = logging.getLogger(__name__)

class TwilioService:
    """
    Twilio integration for SMS campaigns and two-way messaging
    """
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        self.webhook_url = os.getenv('TWILIO_WEBHOOK_URL', '')
        
        # Predefined sender IDs for different church departments and campaigns
        self.sender_ids = {
            # Core church identity
            'futures': 'FUTURES',
            'paradise': 'PARADISE',
            'sunshine_coast': 'SUNSHINE',
            'brisbane': 'BRISBANE',
            'gold_coast': 'GOLDCOAST',
            'toowoomba': 'TOOWOOMBA',
            
            # Age groups
            'kids': 'FUTURESKIDS',
            'youth': 'FUTURESYOUTH',
            'young_adults': 'FUTURESYA',
            'adults': 'FUTURESADULTS',
            'seniors': 'FUTURESSENIORS',
            'families': 'FUTURESFAM',
            
            # Ministries
            'worship': 'FUTURESWORSHIP',
            'prayer': 'FUTURESPRAYER',
            'outreach': 'FUTURESOUTREACH',
            'missions': 'FUTURESMISSIONS',
            'small_groups': 'FUTURESGROUPS',
            'bible_study': 'FUTURESBIBLE',
            'men': 'FUTURESMEN',
            'women': 'FUTURESWOMEN',
            
            # Events and celebrations
            'events': 'FUTURESEVENTS',
            'baptism': 'FUTURESBAPTISM',
            'marriage': 'FUTURESMARRIAGE',
            'counseling': 'FUTURESCOUNSEL',
            'celebration': 'FUTURESPARTY',
            'conference': 'FUTURESCONF',
            'retreat': 'FUTURESRETREAT',
            
            # Special campaigns
            'giving': 'FUTURESGIVE',
            'welcome': 'FUTURESWELCOME',
            'urgent': 'FUTURESURGENT',
            'reminder': 'FUTURESREMIND',
            'invitation': 'FUTURESINVITE',
            'update': 'FUTURESUPDATE',
            
            # Campus-specific variations
            'paradise_youth': 'PARADISEYOUTH',
            'paradise_kids': 'PARADISEKIDS',
            'sunshine_youth': 'SUNSHINEYOUTH',
            'brisbane_families': 'BRISBANEFAM',
            
            # Seasonal and special
            'christmas': 'FUTURESXMAS',
            'easter': 'FUTURESEASTER',
            'summer': 'FUTURESSUN',
            'winter': 'FUTURESWARM',
            'spring': 'FUTURESNEW',
            'fall': 'FUTURESCHANGE',
            
            # Fun and creative
            'cheer': 'FUTURESCHEER',
            'love': 'FUTURESLOVE',
            'hope': 'FUTURESHOPE',
            'joy': 'FUTURESJOY',
            'peace': 'FUTURESPEACE',
            'faith': 'FUTURESFAITH',
            
            # Emergency and urgent
            'emergency': 'FUTURES911',
            'urgent': 'FUTURESURGENT',
            'important': 'FUTURESIMPORTANT',
            'alert': 'FUTURESALERT',
            'notice': 'FUTURESNOTICE',
            
            # Community building
            'community': 'FUTURESCOMM',
            'fellowship': 'FUTURESFELLOW',
            'connection': 'FUTURESCONNECT',
            'support': 'FUTURESSURPPORT',
            'encourage': 'FUTURESENCOURAGE'
        }
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not configured - SMS service disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio service initialized successfully")
    
    def get_available_sender_ids(self) -> Dict[str, str]:
        """Get available sender IDs for SMS campaigns"""
        return self.sender_ids
    
    def add_sender_id(self, key: str, sender_id: str) -> bool:
        """
        Add a new custom sender ID dynamically
        
        Args:
            key: Internal key for the sender ID
            sender_id: The actual sender ID text (e.g., 'FUTURESLOVE')
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Validate sender ID format (alphanumeric only, max 11 characters)
            if not sender_id.isalnum() or len(sender_id) > 11:
                logger.warning(f"Invalid sender ID format: {sender_id}")
                return False
            
            self.sender_ids[key] = sender_id
            logger.info(f"Added new sender ID: {key} -> {sender_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding sender ID {key}: {str(e)}")
            return False
    
    def remove_sender_id(self, key: str) -> bool:
        """
        Remove a custom sender ID
        
        Args:
            key: Internal key for the sender ID to remove
        
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if key in self.sender_ids:
                removed_id = self.sender_ids.pop(key)
                logger.info(f"Removed sender ID: {key} -> {removed_id}")
                return True
            else:
                logger.warning(f"Sender ID key not found: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing sender ID {key}: {str(e)}")
            return False
    
    def update_sender_id(self, key: str, new_sender_id: str) -> bool:
        """
        Update an existing sender ID
        
        Args:
            key: Internal key for the sender ID
            new_sender_id: New sender ID text
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if key in self.sender_ids:
                old_id = self.sender_ids[key]
                self.sender_ids[key] = new_sender_id
                logger.info(f"Updated sender ID: {key} -> {old_id} -> {new_sender_id}")
                return True
            else:
                logger.warning(f"Sender ID key not found: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating sender ID {key}: {str(e)}")
            return False
    
    def get_sender_id_suggestions(self, campaign_type: str = None, target_criteria: Dict[str, Any] = None) -> List[str]:
        """
        Get suggested sender IDs based on campaign type and targeting
        
        Args:
            campaign_type: Type of campaign
            target_criteria: Targeting criteria
        
        Returns:
            List of suggested sender ID keys
        """
        suggestions = []
        
        if target_criteria:
            campus = target_criteria.get('campus', [])
            department = target_criteria.get('department', [])
            
            # Campus-specific suggestions
            if campus:
                for campus_name in campus:
                    campus_key = campus_name.lower().replace(' ', '_')
                    if campus_key in self.sender_ids:
                        suggestions.append(campus_key)
            
            # Department-specific suggestions
            if department:
                for dept_name in department:
                    dept_key = dept_name.lower().replace(' ', '_')
                    if dept_key in self.sender_ids:
                        suggestions.append(dept_key)
        
        # Campaign type suggestions
        if campaign_type:
            campaign_key = campaign_type.lower().replace(' ', '_')
            if campaign_key in self.sender_ids:
                suggestions.append(campaign_key)
        
        # Add some general suggestions
        general_suggestions = ['futures', 'events', 'welcome', 'urgent']
        for suggestion in general_suggestions:
            if suggestion in self.sender_ids and suggestion not in suggestions:
                suggestions.append(suggestion)
        
        return suggestions
    
    def get_sender_id_for_campaign(self, campaign_type: str, target_criteria: Dict[str, Any] = None) -> str:
        """
        Automatically determine the best sender ID based on campaign type and targeting
        
        Args:
            campaign_type: Type of campaign (welcome, events, ministry, etc.)
            target_criteria: Targeting criteria (campus, department, etc.)
        
        Returns:
            Appropriate sender ID string
        """
        # Priority-based sender ID selection
        if target_criteria:
            # Campus-specific sender IDs
            campus = target_criteria.get('campus', [])
            if campus and len(campus) == 1:
                campus_name = campus[0].lower().replace(' ', '_')
                if campus_name in self.sender_ids:
                    return self.sender_ids[campus_name]
            
            # Department-specific sender IDs
            department = target_criteria.get('department', [])
            if department and len(department) == 1:
                dept_name = department[0].lower().replace(' ', '_')
                if dept_name in self.sender_ids:
                    return self.sender_ids[dept_name]
        
        # Campaign type-based sender IDs
        campaign_sender_map = {
            'welcome': 'welcome',
            'baptism': 'baptism',
            'marriage': 'marriage',
            'counseling': 'counseling',
            'events': 'events',
            'giving': 'giving',
            'prayer': 'prayer',
            'ministry': 'ministry'
        }
        
        if campaign_type in campaign_sender_map:
            sender_key = campaign_sender_map[campaign_type]
            if sender_key in self.sender_ids:
                return self.sender_ids[sender_key]
        
        # Default to main FUTURES sender ID
        return self.sender_ids.get('futures', 'FUTURES')
    
    def send_campaign_sms(self, campaign_data: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send an SMS campaign to multiple recipients
        
        Args:
            campaign_data: Campaign information (message content, etc.)
            recipients: List of recipient dictionaries with phone, name, and personalization data
        
        Returns:
            Dictionary with results and message SIDs
        """
        if not self.enabled:
            logger.warning("Twilio service disabled - cannot send SMS campaign")
            return {"success": False, "error": "Service disabled"}
        
        try:
            results = {
                "success": True,
                "sent_count": 0,
                "failed_count": 0,
                "message_sids": [],
                "errors": []
            }
            
            # Get message content
            message_content = campaign_data.get('content', '')
            if not message_content:
                return {"success": False, "error": "No message content provided"}
            
            # Send to each recipient
            for recipient in recipients:
                try:
                    phone = recipient.get('phone')
                    if not phone:
                        results["failed_count"] += 1
                        results["errors"].append(f"No phone number for recipient {recipient.get('id', 'unknown')}")
                        continue
                    
                    # Personalize message content
                    personalized_content = self._personalize_message(message_content, recipient.get('personalization', {}))
                    
                    # Determine sender ID for this campaign
                    sender_id = campaign_data.get('sender_id') or self.get_sender_id_for_campaign(
                        campaign_data.get('campaign_type', 'general'),
                        campaign_data.get('target_criteria', {})
                    )
                    
                    # Send SMS with appropriate sender ID
                    message = self.client.messages.create(
                        body=personalized_content,
                        from_=sender_id,  # Use custom sender ID instead of phone number
                        to=phone,
                        # Add custom parameters for tracking
                        status_callback=f"{self.webhook_url}/sms/status" if self.webhook_url else None
                    )
                    
                    results["sent_count"] += 1
                    results["message_sids"].append({
                        "phone": phone,
                        "message_sid": message.sid,
                        "status": message.status,
                        "recipient_id": recipient.get('id', ''),
                        "person_id": recipient.get('person_id', '')
                    })
                    
                    logger.info(f"SMS sent successfully to {phone}: {message.sid}")
                    
                except TwilioException as e:
                    results["failed_count"] += 1
                    error_msg = f"Twilio error sending to {recipient.get('phone', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                except Exception as e:
                    results["failed_count"] += 1
                    error_msg = f"Error sending SMS to {recipient.get('phone', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in send_campaign_sms: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_single_sms(self, to_phone: str, message_content: str, 
                        personalization: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a single SMS to one recipient
        
        Args:
            to_phone: Recipient phone number
            message_content: SMS message content
            personalization: Custom fields for tracking
        
        Returns:
            Dictionary with result and message SID
        """
        if not self.enabled:
            logger.warning("Twilio service disabled - cannot send SMS")
            return {"success": False, "error": "Service disabled"}
        
        try:
            # Personalize message if variables provided
            if personalization:
                message_content = self._personalize_message(message_content, personalization)
            
            # Send SMS
            message = self.client.messages.create(
                body=message_content,
                from_=self.from_number,
                to=to_phone,
                status_callback=f"{self.webhook_url}/sms/status" if self.webhook_url else None
            )
            
            logger.info(f"Single SMS sent successfully to {to_phone}: {message.sid}")
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": to_phone
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {str(e)}")
            return {"success": False, "error": str(e), "twilio_error": True}
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_bulk_sms(self, phone_numbers: List[str], message_content: str, 
                      batch_size: int = 100) -> Dict[str, Any]:
        """
        Send SMS to a large list of phone numbers in batches
        
        Args:
            phone_numbers: List of phone numbers
            message_content: SMS message content
            batch_size: Number of messages to send per batch
        
        Returns:
            Dictionary with batch results
        """
        if not self.enabled:
            return {"success": False, "error": "Service disabled"}
        
        try:
            total_count = len(phone_numbers)
            results = {
                "success": True,
                "total_count": total_count,
                "sent_count": 0,
                "failed_count": 0,
                "batches": []
            }
            
            # Process in batches
            for i in range(0, total_count, batch_size):
                batch = phone_numbers[i:i + batch_size]
                batch_results = []
                
                for phone in batch:
                    try:
                        message = self.client.messages.create(
                            body=message_content,
                            from_=self.from_number,
                            to=phone
                        )
                        
                        batch_results.append({
                            "phone": phone,
                            "message_sid": message.sid,
                            "status": message.status,
                            "success": True
                        })
                        results["sent_count"] += 1
                        
                    except Exception as e:
                        batch_results.append({
                            "phone": phone,
                            "error": str(e),
                            "success": False
                        })
                        results["failed_count"] += 1
                
                results["batches"].append({
                    "batch_number": i // batch_size + 1,
                    "results": batch_results
                })
                
                # Add delay between batches to avoid rate limiting
                if i + batch_size < total_count:
                    import time
                    time.sleep(1)
            
            logger.info(f"Bulk SMS completed: {results['sent_count']} sent, {results['failed_count']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in send_bulk_sms: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get the status of a specific SMS message
        
        Args:
            message_sid: Twilio message SID
        
        Returns:
            Dictionary with message status information
        """
        if not self.enabled:
            return {"error": "Service disabled"}
        
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "price": message.price,
                "price_unit": message.price_unit
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error getting message status for {message_sid}: {str(e)}")
            return {"error": str(e), "twilio_error": True}
        except Exception as e:
            logger.error(f"Error getting message status for {message_sid}: {str(e)}")
            return {"error": str(e)}
    
    def get_messages(self, to_phone: str = None, from_phone: str = None, 
                    status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get a list of SMS messages with optional filtering
        
        Args:
            to_phone: Filter by recipient phone number
            from_phone: Filter by sender phone number
            status: Filter by message status
            limit: Maximum number of messages to return
        
        Returns:
            List of message dictionaries
        """
        if not self.enabled:
            return []
        
        try:
            # Build filter parameters
            filters = {}
            if to_phone:
                filters['to'] = to_phone
            if from_phone:
                filters['from_'] = from_phone
            if status:
                filters['status'] = status
            
            # Get messages
            messages = self.client.messages.list(**filters, limit=limit)
            
            # Convert to dictionaries
            message_list = []
            for message in messages:
                message_list.append({
                    "message_sid": message.sid,
                    "status": message.status,
                    "to": message.to,
                    "from": message.from_,
                    "body": message.body,
                    "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                    "date_updated": message.date_updated.isoformat() if message.date_updated else None,
                    "direction": message.direction,
                    "price": message.price,
                    "price_unit": message.price_unit
                })
            
            return message_list
            
        except TwilioException as e:
            logger.error(f"Twilio error getting messages: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Validate a phone number using Twilio's Lookup API
        
        Args:
            phone_number: Phone number to validate
        
        Returns:
            Dictionary with validation results
        """
        if not self.enabled:
            return {"valid": False, "error": "Service disabled"}
        
        try:
            # Use Twilio's Lookup API to validate phone number
            number_info = self.client.lookups.v2.phone_numbers(phone_number).fetch()
            
            return {
                "valid": True,
                "phone_number": number_info.phone_number,
                "country_code": number_info.country_code,
                "national_format": number_info.national_format,
                "international_format": number_info.international_format,
                "carrier": number_info.carrier.get('name') if number_info.carrier else None,
                "line_type": number_info.line_type
            }
            
        except TwilioException as e:
            if "not found" in str(e).lower():
                return {"valid": False, "error": "Invalid phone number"}
            else:
                logger.error(f"Twilio error validating phone {phone_number}: {str(e)}")
                return {"valid": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error validating phone {phone_number}: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    def get_account_usage(self, start_date: datetime = None, 
                         end_date: datetime = None) -> Dict[str, Any]:
        """
        Get Twilio account usage statistics
        
        Args:
            start_date: Start date for usage statistics
            end_date: End date for usage statistics
        
        Returns:
            Dictionary with usage statistics
        """
        if not self.enabled:
            return {"error": "Service disabled"}
        
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get usage records
            usage_records = self.client.usage.records.list(
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            
            # Process usage data
            usage_stats = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_cost": 0,
                "total_usage": 0,
                "categories": {}
            }
            
            for record in usage_records:
                category = record.category
                if category not in usage_stats["categories"]:
                    usage_stats["categories"][category] = {
                        "count": 0,
                        "usage": 0,
                        "cost": 0
                    }
                
                usage_stats["categories"][category]["count"] += 1
                usage_stats["categories"][category]["usage"] += record.usage
                usage_stats["categories"][category]["cost"] += float(record.price or 0)
                usage_stats["total_usage"] += record.usage
                usage_stats["total_cost"] += float(record.price or 0)
            
            return usage_stats
            
        except TwilioException as e:
            logger.error(f"Twilio error getting account usage: {str(e)}")
            return {"error": str(e), "twilio_error": True}
        except Exception as e:
            logger.error(f"Error getting account usage: {str(e)}")
            return {"error": str(e)}
    
    def _personalize_message(self, message_content: str, personalization: Dict[str, Any]) -> str:
        """
        Replace placeholder variables in message content with personalization data
        
        Args:
            message_content: Original message content with placeholders
            personalization: Dictionary of personalization data
        
        Returns:
            Personalized message content
        """
        try:
            personalized = message_content
            
            for key, value in personalization.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in personalized:
                    personalized = personalized.replace(placeholder, str(value))
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            return message_content
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhooks from Twilio (message status updates, incoming messages)
        
        Args:
            webhook_data: Webhook data from Twilio
        
        Returns:
            Dictionary with webhook processing result
        """
        try:
            webhook_type = webhook_data.get('MessageStatus') or webhook_data.get('SmsStatus')
            
            if webhook_type:
                # Message status update
                message_sid = webhook_data.get('MessageSid')
                status = webhook_data.get('MessageStatus') or webhook_data.get('SmsStatus')
                
                logger.info(f"Message status update: {message_sid} -> {status}")
                
                # Here you would update your database with the new status
                # and trigger any engagement scoring logic
                
                return {
                    "success": True,
                    "type": "status_update",
                    "message_sid": message_sid,
                    "status": status
                }
            
            elif webhook_data.get('Body'):
                # Incoming SMS message
                from_phone = webhook_data.get('From')
                body = webhook_data.get('Body')
                message_sid = webhook_data.get('MessageSid')
                
                logger.info(f"Incoming SMS from {from_phone}: {body}")
                
                # Here you would process the incoming message
                # and potentially trigger automated responses
                
                return {
                    "success": True,
                    "type": "incoming_message",
                    "from_phone": from_phone,
                    "body": body,
                    "message_sid": message_sid
                }
            
            else:
                return {
                    "success": False,
                    "error": "Unknown webhook type"
                }
                
        except Exception as e:
            logger.error(f"Error handling Twilio webhook: {str(e)}")
            return {"success": False, "error": str(e)}
