#!/usr/bin/env python3
"""
Email Service for Event Management System

Handles email confirmations, reminders, and notifications for events.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration - in production, these should be environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL', 'events@futures.church')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.sender_name = os.getenv('SENDER_NAME', 'Futures Church Events')
        
        self.enabled = bool(self.sender_password)  # Only enable if password is set
        
        if not self.enabled:
            logger.warning("Email service disabled - no SENDER_PASSWORD configured")

    def send_registration_confirmation(self, registration, event):
        """Send registration confirmation email"""
        if not self.enabled:
            logger.info(f"Would send registration confirmation to {registration.registered_email}")
            return True
        
        try:
            subject = f"Registration Confirmed: {event.title}"
            
            # Create email content
            html_content = self._create_confirmation_email(registration, event)
            text_content = self._create_confirmation_text(registration, event)
            
            return self._send_email(
                to_email=registration.registered_email,
                to_name=registration.registered_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending registration confirmation: {e}")
            return False

    def send_waitlist_notification(self, registration, event):
        """Send waitlist notification email"""
        if not self.enabled:
            logger.info(f"Would send waitlist notification to {registration.registered_email}")
            return True
        
        try:
            subject = f"You're on the Waitlist: {event.title}"
            
            html_content = self._create_waitlist_email(registration, event)
            text_content = self._create_waitlist_text(registration, event)
            
            return self._send_email(
                to_email=registration.registered_email,
                to_name=registration.registered_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending waitlist notification: {e}")
            return False

    def send_promotion_notification(self, registration, event):
        """Send email when promoted from waitlist to confirmed"""
        if not self.enabled:
            logger.info(f"Would send promotion notification to {registration.registered_email}")
            return True
        
        try:
            subject = f"Great News! You're Confirmed for {event.title}"
            
            html_content = self._create_promotion_email(registration, event)
            text_content = self._create_promotion_text(registration, event)
            
            return self._send_email(
                to_email=registration.registered_email,
                to_name=registration.registered_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending promotion notification: {e}")
            return False

    def send_event_reminder(self, registration, event):
        """Send event reminder email (24 hours before)"""
        if not self.enabled:
            logger.info(f"Would send event reminder to {registration.registered_email}")
            return True
        
        try:
            subject = f"Reminder: {event.title} Tomorrow"
            
            html_content = self._create_reminder_email(registration, event)
            text_content = self._create_reminder_text(registration, event)
            
            return self._send_email(
                to_email=registration.registered_email,
                to_name=registration.registered_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending event reminder: {e}")
            return False

    def _send_email(self, to_email, to_name, subject, html_content, text_content):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            msg['Subject'] = subject
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {e}")
            return False

    def _create_confirmation_email(self, registration, event):
        """Create HTML confirmation email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .event-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                .button {{ display: inline-block; background: #1e40af; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Registration Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Hi {registration.registered_name},</p>
                    <p>Great news! Your registration for <strong>{event.title}</strong> has been confirmed.</p>
                    
                    <div class="event-details">
                        <h3>Event Details</h3>
                        <p><strong>Event:</strong> {event.title}</p>
                        <p><strong>Date:</strong> {event.start_datetime.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>Time:</strong> {event.start_datetime.strftime('%I:%M %p')}</p>
                        <p><strong>Location:</strong> {event.location}</p>
                        <p><strong>Campus:</strong> {event.campus.replace('_', ' ').title()}</p>
                        {f'<p><strong>Contact:</strong> {event.contact_person} ({event.contact_email})</p>' if event.contact_person else ''}
                    </div>
                    
                    {f'<div class="event-details"><h4>Additional Information</h4><p>{event.additional_info}</p></div>' if event.additional_info else ''}
                    
                    <p>We're looking forward to seeing you there!</p>
                    
                    <p>Blessings,<br>The Futures Church Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {registration.registered_email}</p>
                    <p>Futures Church | Building God's Kingdom Together</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_confirmation_text(self, registration, event):
        """Create plain text confirmation email"""
        return f"""
Hi {registration.registered_name},

Great news! Your registration for {event.title} has been confirmed.

EVENT DETAILS:
- Event: {event.title}
- Date: {event.start_datetime.strftime('%A, %B %d, %Y')}
- Time: {event.start_datetime.strftime('%I:%M %p')}
- Location: {event.location}
- Campus: {event.campus.replace('_', ' ').title()}
{f'- Contact: {event.contact_person} ({event.contact_email})' if event.contact_person else ''}

{f'ADDITIONAL INFORMATION:\\n{event.additional_info}\\n' if event.additional_info else ''}

We're looking forward to seeing you there!

Blessings,
The Futures Church Team

---
This email was sent to {registration.registered_email}
Futures Church | Building God's Kingdom Together
        """

    def _create_waitlist_email(self, registration, event):
        """Create HTML waitlist notification email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .event-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're on the Waitlist</h1>
                </div>
                <div class="content">
                    <p>Hi {registration.registered_name},</p>
                    <p>Thank you for your interest in <strong>{event.title}</strong>!</p>
                    <p>This event is currently full, but we've added you to the waitlist. We'll notify you immediately if a spot becomes available.</p>
                    
                    <div class="event-details">
                        <h3>Event Details</h3>
                        <p><strong>Event:</strong> {event.title}</p>
                        <p><strong>Date:</strong> {event.start_datetime.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>Time:</strong> {event.start_datetime.strftime('%I:%M %p')}</p>
                        <p><strong>Location:</strong> {event.location}</p>
                    </div>
                    
                    <p>We'll be in touch if a spot opens up!</p>
                    
                    <p>Blessings,<br>The Futures Church Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {registration.registered_email}</p>
                    <p>Futures Church | Building God's Kingdom Together</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_waitlist_text(self, registration, event):
        """Create plain text waitlist notification"""
        return f"""
Hi {registration.registered_name},

Thank you for your interest in {event.title}!

This event is currently full, but we've added you to the waitlist. We'll notify you immediately if a spot becomes available.

EVENT DETAILS:
- Event: {event.title}
- Date: {event.start_datetime.strftime('%A, %B %d, %Y')}
- Time: {event.start_datetime.strftime('%I:%M %p')}
- Location: {event.location}

We'll be in touch if a spot opens up!

Blessings,
The Futures Church Team

---
This email was sent to {registration.registered_email}
Futures Church | Building God's Kingdom Together
        """

    def _create_promotion_email(self, registration, event):
        """Create HTML promotion notification email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .event-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Great News! You're Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Hi {registration.registered_name},</p>
                    <p>Wonderful news! A spot has opened up for <strong>{event.title}</strong> and your registration is now confirmed!</p>
                    
                    <div class="event-details">
                        <h3>Event Details</h3>
                        <p><strong>Event:</strong> {event.title}</p>
                        <p><strong>Date:</strong> {event.start_datetime.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>Time:</strong> {event.start_datetime.strftime('%I:%M %p')}</p>
                        <p><strong>Location:</strong> {event.location}</p>
                        <p><strong>Campus:</strong> {event.campus.replace('_', ' ').title()}</p>
                    </div>
                    
                    {f'<div class="event-details"><h4>Additional Information</h4><p>{event.additional_info}</p></div>' if event.additional_info else ''}
                    
                    <p>We're excited to see you there!</p>
                    
                    <p>Blessings,<br>The Futures Church Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {registration.registered_email}</p>
                    <p>Futures Church | Building God's Kingdom Together</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_promotion_text(self, registration, event):
        """Create plain text promotion notification"""
        return f"""
Hi {registration.registered_name},

Wonderful news! A spot has opened up for {event.title} and your registration is now confirmed!

EVENT DETAILS:
- Event: {event.title}
- Date: {event.start_datetime.strftime('%A, %B %d, %Y')}
- Time: {event.start_datetime.strftime('%I:%M %p')}
- Location: {event.location}
- Campus: {event.campus.replace('_', ' ').title()}

{f'ADDITIONAL INFORMATION:\\n{event.additional_info}\\n' if event.additional_info else ''}

We're excited to see you there!

Blessings,
The Futures Church Team

---
This email was sent to {registration.registered_email}
Futures Church | Building God's Kingdom Together
        """

    def _create_reminder_email(self, registration, event):
        """Create HTML reminder email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #7c3aed; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .event-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Event Reminder</h1>
                </div>
                <div class="content">
                    <p>Hi {registration.registered_name},</p>
                    <p>This is a friendly reminder that <strong>{event.title}</strong> is tomorrow!</p>
                    
                    <div class="event-details">
                        <h3>Event Details</h3>
                        <p><strong>Event:</strong> {event.title}</p>
                        <p><strong>Date:</strong> {event.start_datetime.strftime('%A, %B %d, %Y')}</p>
                        <p><strong>Time:</strong> {event.start_datetime.strftime('%I:%M %p')}</p>
                        <p><strong>Location:</strong> {event.location}</p>
                        <p><strong>Campus:</strong> {event.campus.replace('_', ' ').title()}</p>
                    </div>
                    
                    {f'<div class="event-details"><h4>What to Bring</h4><p>{event.additional_info}</p></div>' if event.additional_info else ''}
                    
                    <p>We can't wait to see you there!</p>
                    
                    <p>Blessings,<br>The Futures Church Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {registration.registered_email}</p>
                    <p>Futures Church | Building God's Kingdom Together</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_reminder_text(self, registration, event):
        """Create plain text reminder email"""
        return f"""
Hi {registration.registered_name},

This is a friendly reminder that {event.title} is tomorrow!

EVENT DETAILS:
- Event: {event.title}
- Date: {event.start_datetime.strftime('%A, %B %d, %Y')}
- Time: {event.start_datetime.strftime('%I:%M %p')}
- Location: {event.location}
- Campus: {event.campus.replace('_', ' ').title()}

{f'WHAT TO BRING:\\n{event.additional_info}\\n' if event.additional_info else ''}

We can't wait to see you there!

Blessings,
The Futures Church Team

---
This email was sent to {registration.registered_email}
Futures Church | Building God's Kingdom Together
        """


# Global email service instance
email_service = EmailService()

