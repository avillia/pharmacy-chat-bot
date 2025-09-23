from src.core.models import ConversationContext, Pharmacy, NewPharmacyLead


def find_pharmacy_by_phone(
    pharmacies: list[Pharmacy],
    phone: str,
) -> Pharmacy | None:
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
    return "".join(filter(str.isdigit, phone))


def initialize_conversation(
    caller_phone: str,
    pharmacy: Pharmacy | None = None,
) -> ConversationContext:
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
    else:
        context.new_lead = NewPharmacyLead(phone=caller_phone)

    return context
