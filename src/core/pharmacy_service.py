"""
Pharmacy service functions for data lookup and management.

This module handles all pharmacy-related business logic, making it easy
to find, validate, and work with pharmacy data.
"""

from typing import List, Optional
from .models import Pharmacy, NewPharmacyLead, ConversationContext


def find_pharmacy_by_phone(pharmacies: List[Pharmacy], phone: str) -> Optional[Pharmacy]:
    """
    Find a pharmacy by phone number.
    
    Args:
        pharmacies: List of all pharmacies to search through
        phone: Phone number to search for
        
    Returns:
        Pharmacy object if found, None otherwise
    """
    # Normalize phone numbers by removing common formatting
    normalized_search = normalize_phone_number(phone)
    
    for pharmacy in pharmacies:
        normalized_pharmacy_phone = normalize_phone_number(pharmacy.phone)
        if normalized_pharmacy_phone == normalized_search:
            return pharmacy
    
    return None


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number by removing formatting characters.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Normalized phone number with only digits
    """
    return ''.join(filter(str.isdigit, phone))


def create_pharmacy_summary(pharmacy: Pharmacy) -> str:
    """
    Create a human-friendly summary of pharmacy information.
    
    Args:
        pharmacy: Pharmacy object to summarize
        
    Returns:
        Formatted string with key pharmacy details
    """
    summary_parts = [
        f"📋 **{pharmacy.name}**",
        f"📍 Located in {pharmacy.location}",
        f"💊 Total Rx Volume: {pharmacy.total_rx_volume} prescriptions",
    ]
    
    if pharmacy.prescriptions:
        top_drugs = sorted(pharmacy.prescriptions, key=lambda x: x.count, reverse=True)[:3]
        drugs_text = ", ".join([f"{drug.drug} ({drug.count})" for drug in top_drugs])
        summary_parts.append(f"🔝 Top medications: {drugs_text}")
    
    if pharmacy.is_high_volume:
        summary_parts.append("⭐ High-volume pharmacy - perfect fit for Pharmesol!")
    
    return "\n".join(summary_parts)


def assess_lead_potential(lead: NewPharmacyLead) -> str:
    """
    Assess the potential value of a new pharmacy lead.
    
    Args:
        lead: New pharmacy lead information
        
    Returns:
        Assessment message with recommendations
    """
    if not lead.estimated_rx_volume:
        return "We'd love to learn more about your prescription volume to better assist you."
    
    if lead.estimated_rx_volume >= 100:
        return (
            f"With {lead.estimated_rx_volume} monthly prescriptions, you're exactly the type of "
            "high-volume pharmacy that Pharmesol specializes in supporting!"
        )
    elif lead.estimated_rx_volume >= 50:
        return (
            f"Your {lead.estimated_rx_volume} monthly prescriptions show good growth potential. "
            "Pharmesol can help you scale efficiently."
        )
    else:
        return (
            "Every pharmacy starts somewhere! Pharmesol can help you grow your prescription "
            "volume with our comprehensive support system."
        )


def get_missing_info_prompt(lead: NewPharmacyLead) -> Optional[str]:
    """
    Generate a prompt for missing information from a lead.
    
    Args:
        lead: Current lead information
        
    Returns:
        Question to ask for missing info, or None if complete
    """
    if not lead.name:
        return "What's the name of your pharmacy?"
    
    if not lead.contact_person:
        return "And what's your name so I can address you properly?"
    
    if not lead.city or not lead.state:
        return "Where is your pharmacy located? (City and State)"
    
    if not lead.estimated_rx_volume:
        return "Approximately how many prescriptions do you fill per month?"
    
    return None


def initialize_conversation(caller_phone: str, pharmacy: Optional[Pharmacy] = None) -> ConversationContext:
    """
    Initialize a new conversation context.
    
    Args:
        caller_phone: Phone number of the caller
        pharmacy: Known pharmacy if this is a returning customer
        
    Returns:
        New conversation context object
    """
    context = ConversationContext(caller_phone=caller_phone)
    
    if pharmacy:
        context.pharmacy = pharmacy
        context.conversation_stage = "returning_customer_greeting"
    else:
        context.new_lead = NewPharmacyLead(phone=caller_phone)
        context.conversation_stage = "new_lead_greeting"
    
    return context
