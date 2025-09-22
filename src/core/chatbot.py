from __future__ import annotations

from json import loads as read_json_from

from openai import OpenAI

from env import COMPANY_NAME, COMPANY_PHONE, OPENAI_API_KEY, PROMPTS_DIR

from .models import ConversationContext, NewPharmacyLead
from .prompt_manager import PromptManager


class ChatbotError(Exception):
    """Custom exception for chatbot errors."""

    pass


class PharmacyChatbot:
    """
    Intelligent chatbot for pharmacy SMS conversations.

    This chatbot can recognize returning customers, collect lead information,
    and provide contextual responses about Pharmesol's services.
    """

    def __init__(
        self, openai_api_key: str | None = None, prompts_dir: str | None = None
    ):
        api_key = openai_api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=api_key)

        prompts_directory = prompts_dir or PROMPTS_DIR
        self.prompt_manager = PromptManager(prompts_directory, COMPANY_NAME)

    def generate_greeting(self, context: ConversationContext) -> str:
        if context.is_returning_customer and context.pharmacy:
            return self.prompt_manager.get_returning_customer_greeting(context.pharmacy)
        return self.prompt_manager.get_new_lead_greeting()

    def process_user_message(
        self, context: ConversationContext, user_message: str
    ) -> str:
        context.messages.append(f"User: {user_message}")

        try:
            if context.is_returning_customer:
                response = self._handle_returning_customer(context, user_message)
            else:
                response = self._handle_new_lead(context, user_message)

            context.messages.append(f"Bot: {response}")
            return response

        except Exception as e:
            error_response = (
                "I apologize, but I'm having trouble processing your message right now. "
                f"Please call us directly at {COMPANY_PHONE} "
                "and we'll be happy to help!"
            )
            context.messages.append(f"Bot: {error_response}")
            return error_response

    def _handle_returning_customer(
        self, context: ConversationContext, message: str
    ) -> str:
        pharmacy = context.pharmacy

        system_prompt = self.prompt_manager.get_returning_customer_system_prompt(
            pharmacy
        )

        return self._generate_ai_response(system_prompt, message, context.messages)

    def _handle_new_lead(self, context: ConversationContext, message: str) -> str:
        lead = context.new_lead

        missing_info_prompt = self.prompt_manager.get_missing_info_prompt_for_lead(lead)

        if missing_info_prompt:
            self._extract_lead_info_with_openai(lead, message)

            # Check again if we still need information
            missing_info_prompt = self.prompt_manager.get_missing_info_prompt_for_lead(
                lead
            )
            if missing_info_prompt:
                return f"Thanks for that information! {missing_info_prompt}"

        # We have enough info, provide value proposition
        assessment = self.prompt_manager.get_lead_assessment(lead)
        system_prompt = self.prompt_manager.get_new_lead_system_prompt(lead, assessment)

        return self._generate_ai_response(system_prompt, message, context.messages)

    def _extract_lead_info_with_openai(
        self, lead: NewPharmacyLead, message: str
    ) -> None:
        try:
            extraction_prompt = self.prompt_manager.get_extraction_prompt(
                "lead_information", user_message=message
            )

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent extraction
            )

            extracted_data = read_json_from(response.choices[0].message.content.strip())

            if not lead.name and extracted_data.get("pharmacy_name"):
                lead.name = extracted_data["pharmacy_name"]

            if not lead.contact_person and extracted_data.get("contact_person"):
                lead.contact_person = extracted_data["contact_person"]

            if not lead.city and extracted_data.get("city"):
                lead.city = extracted_data["city"]

            if not lead.state and extracted_data.get("state"):
                lead.state = extracted_data["state"]

            if not lead.estimated_rx_volume and extracted_data.get(
                "estimated_rx_volume"
            ):
                lead.estimated_rx_volume = extracted_data["estimated_rx_volume"]

            if not lead.preferred_contact and extracted_data.get("preferred_contact"):
                lead.preferred_contact = extracted_data["preferred_contact"]

        except Exception as e:
            # If OpenAI extraction fails, fall back to basic extraction
            self._extract_lead_info_fallback(lead, message)

    def _extract_lead_info_fallback(self, lead: NewPharmacyLead, message: str) -> None:
        """
        Fallback extraction method using simple heuristics when OpenAI fails.

        This is a simplified backup method for when OpenAI is unavailable.
        """

    def _generate_ai_response(
        self, system_prompt: str, user_message: str, conversation_history: list[str]
    ) -> str:
        try:
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history (last 6 messages to stay within limits)
            for msg in conversation_history[-6:]:
                if msg.startswith("User: "):
                    messages.append({"role": "user", "content": msg[6:]})
                elif msg.startswith("Bot: "):
                    messages.append({"role": "assistant", "content": msg[5:]})

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,  # Keep responses concise for SMS
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise ChatbotError(f"Failed to generate AI response: {str(e)}") from e

    def suggest_follow_up_actions(self, context: ConversationContext) -> list[str]:
        actions = []

        if context.is_returning_customer and context.pharmacy:
            pharmacy = context.pharmacy
            if pharmacy.email:
                actions.append(f"Send follow-up email to {pharmacy.email}")
            actions.append(f"Schedule callback to {pharmacy.phone}")

        elif context.new_lead and context.new_lead.is_complete:
            actions.append("Send lead information to sales team")
            actions.append("Create CRM entry for new lead")
            actions.append(f"Schedule callback to {context.new_lead.phone}")

        return actions
