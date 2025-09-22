"""
Follow-up actions for pharmacy leads and customers.

This module provides mock implementations of follow-up actions like
email sending and callback scheduling.

In production, these would integrate with real email services and
CRM systems.
"""

from datetime import datetime

import env
from src.core.models import NewPharmacyLead, Pharmacy
from src.core.prompt_manager import PromptManager

prompt_manager = PromptManager(env.PROMPTS_DIR, env.COMPANY_NAME)


def send_email(
    recipient_email: str,
    subject: str,
    content: str,
    sender_name: str = "Pharmesol Team",
) -> bool:
    """
    Mock function to send follow-up emails.

    In production, this would integrate with an email service like SendGrid,
    AWS SES, or similar.

    Args:
        recipient_email: Email address to send to
        subject: Email subject line
        content: Email body content
        sender_name: Name of the sender

    Returns:
        True if email was "sent" successfully
    """
    print(f"\n📧 EMAIL SENT")
    print(f"To: {recipient_email}")
    print(f"From: {sender_name}")
    print(f"Subject: {subject}")
    print(f"Content:\n{content}")
    print("=" * 50)

    return True


def schedule_callback(
    phone: str, preferred_time: str | None = None, notes: str = ""
) -> str:
    """
    Mock function to schedule a callback.

    In production, this would integrate with a CRM system or scheduling
    platform to actually book the callback.

    Args:
        phone: Phone number to call back
        preferred_time: When the customer prefers to be called
        notes: Any additional notes for the callback

    Returns:
        Confirmation message with callback details
    """
    # Default to next business day if no preference given
    callback_time = preferred_time or "tomorrow between 9 AM - 5 PM EST"
    callback_id = f"CB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n📞 CALLBACK SCHEDULED")
    print(f"Callback ID: {callback_id}")
    print(f"Phone: {phone}")
    print(f"Scheduled for: {callback_time}")
    if notes:
        print(f"Notes: {notes}")
    print("=" * 50)

    return f"Callback scheduled for {callback_time} (ID: {callback_id})"


def send_pharmacy_welcome_email(pharmacy: Pharmacy) -> bool:
    if not pharmacy.email:
        print(f"⚠️  No email address on file for {pharmacy.name}")
        return False

    volume_message = (
        f"As a high-volume pharmacy, you're exactly who we love working with!"
        if pharmacy.is_high_volume
        else "We're excited to help you grow your prescription volume."
    )

    subject = prompt_manager["system/welcome_email_subject"].format(
        pharmacy_name=pharmacy.name
    )

    content = prompt_manager["system/welcome_email_content"].format(
        pharmacy_name=pharmacy.name,
        company_name=env.COMPANY_NAME,
        location=pharmacy.location,
        total_rx_volume=pharmacy.total_rx_volume,
        volume_message=volume_message,
    )

    return send_email(pharmacy.email, subject, content)


def send_lead_follow_up_email(lead: NewPharmacyLead) -> bool:
    email = f"leads@{env.COMPANY_NAME.lower()}.com"

    subject = prompt_manager["system/lead_notification_subject"].format(
        pharmacy_name=lead.name or "Unknown Pharmacy"
    )

    content = prompt_manager["system/lead_notification_content"].format(
        pharmacy_name=lead.name or "Not provided",
        contact_person=lead.contact_person or "Not provided",
        phone=lead.phone,
        location=f"{lead.city or 'Unknown'}, {lead.state or 'Unknown'}",
        estimated_rx_volume=lead.estimated_rx_volume or "Not provided",
        preferred_contact=lead.preferred_contact or "Not specified",
        follow_up_needed="No" if lead.is_complete else "Yes - missing information",
    )

    return send_email(email, subject, content)


def create_crm_entry(lead: NewPharmacyLead) -> str:
    """
    Mock function to create a CRM entry for a new lead.

    Args:
        lead: New pharmacy lead information

    Returns:
        CRM entry ID
    """
    entry_id = f"CRM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"\n💼 CRM ENTRY CREATED")
    print(f"Entry ID: {entry_id}")
    print(f"Lead: {lead.name or 'Unknown Pharmacy'}")
    print(f"Phone: {lead.phone}")
    print(f"Status: {'Qualified' if lead.is_complete else 'Needs Follow-up'}")
    print("=" * 50)

    return entry_id
