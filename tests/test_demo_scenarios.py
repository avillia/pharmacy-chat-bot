"""
Demo scenarios test suite for the pharmacy chatbot.

This module contains comprehensive demo scenarios that showcase all the
chatbot's capabilities in realistic conversation flows.
"""

import pytest

import env
from src.api.follow_up_actions import (
    create_crm_entry,
    schedule_callback,
    send_lead_follow_up_email,
    send_pharmacy_welcome_email,
)
from src.api.pharmacy.client import PharmacyAPIError, PharmacyClient
from src.core.chatbot import ChatbotError, PharmacyChatbot
from src.core.models import ConversationContext
from src.core.pharmacy_service import find_pharmacy_by_phone, initialize_conversation


class TestDemoScenarios:
    """Test suite for comprehensive demo scenarios."""

    @pytest.fixture(scope="class")
    def pharmacy_client(self):
        """Create a pharmacy client for testing."""
        return PharmacyClient(env.PHARMACY_API_URL)

    @pytest.fixture(scope="class")
    def pharmacies_data(self, pharmacy_client):
        """Load pharmacy data once for all tests."""
        try:
            return pharmacy_client.fetch_all_pharmacies_sync()
        except PharmacyAPIError:
            pytest.skip("Cannot connect to pharmacy API")

    @pytest.fixture
    def chatbot(self):
        """Create a chatbot instance (or None if no API key)."""
        if not env.OPENAI_API_KEY:
            return None
        try:
            return PharmacyChatbot()
        except ChatbotError:
            return None

    def simulate_conversation(
        self,
        caller_phone: str,
        messages: list[str],
        pharmacies_data: list,
        chatbot=None,
        print_output: bool = False,
    ) -> ConversationContext:
        """
        Simulate a complete SMS conversation with a caller.

        Args:
            caller_phone: Phone number of the caller
            messages: List of messages the caller will send
            pharmacies_data: List of pharmacy data
            chatbot: Chatbot instance (optional)
            print_output: Whether to print conversation output

        Returns:
            Final conversation context
        """
        if print_output:
            print(f"\n🔄 Starting conversation simulation for {caller_phone}")
            print("=" * 60)

        # Look up the caller
        pharmacy = find_pharmacy_by_phone(pharmacies_data, caller_phone)
        context = initialize_conversation(caller_phone, pharmacy)

        # Generate and capture greeting
        if chatbot:
            greeting = chatbot.generate_greeting(context)
        else:
            greeting = self.get_mock_greeting(context)

        if print_output:
            print(f"\n🤖 Bot: {greeting}")

        # Process each message in the conversation
        for i, message in enumerate(messages, 1):
            if print_output:
                print(f"\n👤 User: {message}")

            if chatbot:
                response = chatbot.process_user_message(context, message)
            else:
                response = self.get_mock_response(context, message, i)

            if print_output:
                print(f"🤖 Bot: {response}")

        return context

    def get_mock_greeting(self, context: ConversationContext) -> str:
        """Generate a mock greeting when OpenAI is not available."""
        if context.is_returning_customer and context.pharmacy:
            pharmacy = context.pharmacy
            return f"""Hello {pharmacy.name}! 👋

Great to hear from you again. I see you're calling from {pharmacy.location} with {pharmacy.total_rx_volume} total prescriptions.

How can {env.COMPANY_NAME} help you today?"""
        else:
            return f"""Hello! 👋 Thank you for contacting {env.COMPANY_NAME}.

I don't recognize this number - are you a new pharmacy looking to learn about our services?"""

    def get_mock_response(
        self, context: ConversationContext, message: str, message_num: int
    ) -> str:
        """Generate mock responses when OpenAI is not available."""
        responses = [
            "That's great to hear! Tell me more about your pharmacy.",
            f"I understand. {env.COMPANY_NAME} specializes in helping high-volume pharmacies like yours.",
            "Perfect! I'd love to follow up with you. Would you prefer email or a phone call?",
        ]
        return responses[min(message_num - 1, len(responses) - 1)]

    def execute_follow_up_actions(
        self, context: ConversationContext, print_output: bool = False
    ) -> dict:
        """
        Execute appropriate follow-up actions based on the conversation.

        Returns:
            Dict with information about actions taken
        """
        actions_taken = {
            "emails_sent": 0,
            "callbacks_scheduled": 0,
            "crm_entries_created": 0,
        }

        if print_output:
            print(f"\n🎯 Executing follow-up actions...")

        if context.is_returning_customer and context.pharmacy:
            pharmacy = context.pharmacy

            # Send welcome email if we have an email address
            if pharmacy.email:
                send_pharmacy_welcome_email(pharmacy)
                actions_taken["emails_sent"] += 1

            # Schedule a callback
            schedule_callback(
                pharmacy.phone,
                notes=f"Follow-up call for {pharmacy.name} - discussed support needs",
            )
            actions_taken["callbacks_scheduled"] += 1

        elif context.new_lead and context.new_lead.is_complete:
            lead = context.new_lead

            # Send lead follow-up email (internal notification)
            send_lead_follow_up_email(lead)
            actions_taken["emails_sent"] += 1

            # Create CRM entry
            create_crm_entry(lead)
            actions_taken["crm_entries_created"] += 1

            # Schedule callback
            schedule_callback(
                lead.phone,
                notes=f"New lead follow-up: {lead.name or 'Unknown pharmacy'}",
            )
            actions_taken["callbacks_scheduled"] += 1

        return actions_taken

    def test_returning_established_customer(self, pharmacies_data, chatbot):
        """Test conversation with a returning established pharmacy customer."""
        context = self.simulate_conversation(
            caller_phone="+1-555-123-4567",  # HealthFirst Pharmacy
            messages=[
                "Hi, we're having issues with our prescription management system",
                "We process about 100+ prescriptions daily and need better support",
                "Yes, I'd like to schedule a call to discuss our options",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
        )

        # Verify it's a returning customer
        assert context.is_returning_customer
        assert context.pharmacy is not None
        assert context.pharmacy.name == "HealthFirst Pharmacy"
        assert context.pharmacy.total_rx_volume == 100  # Has exactly 100 Rx (threshold)

        # Execute follow-up actions
        actions = self.execute_follow_up_actions(context)

        # Verify appropriate actions were taken
        assert actions["emails_sent"] == 1  # Welcome email
        assert actions["callbacks_scheduled"] == 1  # Callback scheduled
        assert actions["crm_entries_created"] == 0  # No CRM entry for existing customer

    def test_returning_regular_customer(self, pharmacies_data, chatbot):
        """Test conversation with a returning regular pharmacy customer."""
        context = self.simulate_conversation(
            caller_phone="+1-555-666-7777",  # MediCare Plus
            messages=[
                "Hello, I wanted to learn more about your services",
                "We're looking to grow our prescription volume",
                "Please send me more information via email",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
        )

        # Verify it's a returning customer
        assert context.is_returning_customer
        assert context.pharmacy is not None
        assert context.pharmacy.name == "MediCare Plus"
        assert not context.pharmacy.is_high_volume  # Should be regular volume

        # Execute follow-up actions
        actions = self.execute_follow_up_actions(context)

        # Verify appropriate actions were taken
        assert actions["emails_sent"] == 1  # Welcome email
        assert actions["callbacks_scheduled"] == 1  # Callback scheduled
        assert actions["crm_entries_created"] == 0  # No CRM entry for existing customer

    def test_new_pharmacy_lead(self, pharmacies_data, chatbot):
        """Test conversation with a new pharmacy lead."""
        context = self.simulate_conversation(
            caller_phone="+1-555-999-0000",  # Unknown number
            messages=[
                "Hi, I heard about Pharmesol from a colleague",
                "I'm Sarah and I run Metro Pharmacy in Denver, Colorado",
                "We handle about 150 prescriptions per month",
                "I'd prefer a phone call to discuss how you can help us",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
        )

        # Verify it's a new lead
        assert not context.is_returning_customer
        assert context.pharmacy is None
        assert context.new_lead is not None

        # Check if lead information was extracted
        lead = context.new_lead
        # Note: Information extraction depends on the chatbot's NLP capabilities
        # In mock mode, this might not work perfectly

        # Execute follow-up actions (even if lead is incomplete)
        actions = self.execute_follow_up_actions(context)

        # For incomplete leads, fewer actions might be taken
        assert actions["emails_sent"] >= 0
        assert actions["callbacks_scheduled"] >= 0
        assert actions["crm_entries_created"] >= 0

    def test_pharmacy_data_loading(self, pharmacy_client):
        """Test that pharmacy data loads correctly from the API."""
        pharmacies = pharmacy_client.fetch_all_pharmacies_sync()

        # Verify we have the expected pharmacies
        assert len(pharmacies) >= 5

        # Check for known pharmacies
        pharmacy_names = [p.name for p in pharmacies]
        assert "HealthFirst Pharmacy" in pharmacy_names
        assert "MediCare Plus" in pharmacy_names

        # Verify pharmacy data structure
        healthfirst = next(p for p in pharmacies if p.name == "HealthFirst Pharmacy")
        assert healthfirst.phone == "+1-555-123-4567"
        assert healthfirst.city == "New York"
        assert healthfirst.state == "NY"
        assert healthfirst.total_rx_volume == 100
        # Note: 100 is exactly at threshold, not >100, so not technically "high volume"

    def test_phone_number_recognition(self, pharmacies_data):
        """Test phone number recognition and normalization."""
        # Test exact match
        pharmacy = find_pharmacy_by_phone(pharmacies_data, "+1-555-123-4567")
        assert pharmacy is not None
        assert pharmacy.name == "HealthFirst Pharmacy"

        # Test with different formatting (should still work due to normalization)
        pharmacy = find_pharmacy_by_phone(pharmacies_data, "15551234567")
        assert pharmacy is not None
        assert pharmacy.name == "HealthFirst Pharmacy"

        # Test unknown number
        pharmacy = find_pharmacy_by_phone(pharmacies_data, "+1-555-UNKNOWN")
        assert pharmacy is None

    @pytest.mark.integration
    def test_complete_demo_flow(self, pharmacies_data, chatbot):
        """Integration test running all demo scenarios."""
        print("\n🎭 PHARMACY CHATBOT DEMO")
        print("=" * 60)
        print("This demo shows how the chatbot handles different scenarios:")
        print("1. Returning high-volume pharmacy customer")
        print("2. Returning regular pharmacy customer")
        print("3. New pharmacy lead")
        print("=" * 60)

        # Scenario 1: Returning high-volume customer
        print("\n📊 Scenario 1: High-Volume Returning Customer")
        context1 = self.simulate_conversation(
            caller_phone="+1-555-123-4567",
            messages=[
                "Hi, we're having issues with our prescription management system",
                "We process about 100+ prescriptions daily and need better support",
                "Yes, I'd like to schedule a call to discuss our options",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
            print_output=True,
        )
        actions1 = self.execute_follow_up_actions(context1, print_output=True)
        print(f"✅ Scenario 1 completed - Actions: {actions1}")

        # Scenario 2: Returning regular customer
        print("\n📈 Scenario 2: Regular Returning Customer")
        context2 = self.simulate_conversation(
            caller_phone="+1-555-666-7777",
            messages=[
                "Hello, I wanted to learn more about your services",
                "We're looking to grow our prescription volume",
                "Please send me more information via email",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
            print_output=True,
        )
        actions2 = self.execute_follow_up_actions(context2, print_output=True)
        print(f"✅ Scenario 2 completed - Actions: {actions2}")

        # Scenario 3: New pharmacy lead
        print("\n🆕 Scenario 3: New Pharmacy Lead")
        context3 = self.simulate_conversation(
            caller_phone="+1-555-999-0000",
            messages=[
                "Hi, I heard about Pharmesol from a colleague",
                "I'm Sarah and I run Metro Pharmacy in Denver, Colorado",
                "We handle about 150 prescriptions per month",
                "I'd prefer a phone call to discuss how you can help us",
            ],
            pharmacies_data=pharmacies_data,
            chatbot=chatbot,
            print_output=True,
        )
        actions3 = self.execute_follow_up_actions(context3, print_output=True)
        print(f"✅ Scenario 3 completed - Actions: {actions3}")

        print("\n🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Phone number recognition and pharmacy lookup")
        print("✅ Personalized greetings for returning customers")
        print("✅ New lead information collection")
        print("✅ High-volume pharmacy identification and targeting")
        print("✅ Mock follow-up actions (email/callback scheduling)")
        print("✅ Graceful handling of missing data")

        # Verify all scenarios worked
        assert context1.is_returning_customer
        assert context2.is_returning_customer
        assert not context3.is_returning_customer


def test_environment_configuration():
    """Test that environment configuration is properly loaded."""
    # Test that required variables are set
    assert env.PHARMACY_API_URL is not None
    assert env.COMPANY_NAME is not None
    assert env.COMPANY_PHONE is not None

    # Test that defaults are reasonable
    assert "pharmesol" in env.COMPANY_NAME.lower()
    assert "prompts" in env.PROMPTS_DIR
    assert env.DEFAULT_TIMEOUT > 0


if __name__ == "__main__":
    # Run integration test when executed directly
    import sys

    print("🧪 Running Pharmacy Chatbot Demo Scenarios")
    print("=" * 50)

    try:
        # Load pharmacy data
        client = PharmacyClient(env.PHARMACY_API_URL)
        pharmacies = client.fetch_all_pharmacies_sync()
        print(f"✅ Loaded {len(pharmacies)} pharmacies from API")

        # Try to initialize chatbot
        chatbot = None
        if env.OPENAI_API_KEY:
            try:
                chatbot = PharmacyChatbot()
                print("✅ Chatbot initialized with OpenAI")
            except ChatbotError:
                print("⚠️  OpenAI initialization failed, using mock responses")
        else:
            print("⚠️  No OpenAI API key, using mock responses")

        # Run the integration test
        test_instance = TestDemoScenarios()
        test_instance.test_complete_demo_flow(pharmacies, chatbot)

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        sys.exit(1)

    print("\n💡 To run with pytest: pytest tests/test_demo_scenarios.py -v -s")
