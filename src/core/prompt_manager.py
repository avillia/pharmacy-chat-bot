from __future__ import annotations
from pathlib import Path
from src.core.models import Pharmacy, NewPharmacyLead


class PromptManager:
    """
    Manages prompt templates and provides formatted prompts for conversations.

    This class loads prompt templates from text files and provides methods
    to generate formatted prompts for different conversation scenarios.
    """

    def __init__(
        self,
        prompts_dir: str | Path = "prompts",
        company_name: str = "Pharmesol",
    ):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}
        self.company_name = company_name

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

    def __getitem__(self, prompt_path: str) -> str:
        if not prompt_path.endswith(".txt"):
            prompt_path = f"{prompt_path}.txt"
        file_path = self.prompts_dir / prompt_path

        cache_key = str(file_path.relative_to(self.prompts_dir))

        if cache_key in self._cache:
            return self._cache[cache_key]

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            self._cache[cache_key] = content
            return content

        except Exception as e:
            raise RuntimeError(f"Failed to read prompt file {file_path}: {str(e)}") from e

    def get_returning_customer_greeting(self, pharmacy: Pharmacy) -> str:
        top_drugs_text = ""
        if pharmacy.prescriptions:
            top_drugs = sorted(
                pharmacy.prescriptions, key=lambda x: x.count, reverse=True
            )[:3]
            drugs_text = ", ".join(
                [f"{drug.drug} ({drug.count})" for drug in top_drugs]
            )
            top_drugs_text = f"🔝 Top medications: {drugs_text}"

        high_volume_message = ""
        if pharmacy.is_high_volume:
            high_volume_message = (
                f"⭐ High-volume pharmacy - perfect fit for {self.company_name}!"
            )

        return self["responses/returning_customer_greeting"].format(
            pharmacy_name=pharmacy.name,
            location=pharmacy.location,
            total_rx_volume=pharmacy.total_rx_volume,
            top_drugs_text=top_drugs_text,
            high_volume_message=high_volume_message,
            company_name=self.company_name,
        )

    def get_new_lead_greeting(self) -> str:
        return self["responses/new_lead_greeting"].format(
            company_name=self.company_name
        )

    def get_returning_customer_system_prompt(
        self,
        pharmacy: Pharmacy,
    ) -> str:
        volume_assessment = (
            "This is a high-volume pharmacy that's perfect for our services."
            if pharmacy.is_high_volume
            else "This pharmacy has growth potential."
        )

        return self["system/returning_customer_system"].format(
            company_name=self.company_name,
            pharmacy_name=pharmacy.name,
            location=pharmacy.location,
            total_rx_volume=pharmacy.total_rx_volume,
            volume_assessment=volume_assessment,
        )

    def get_new_lead_system_prompt(
        self,
        lead: NewPharmacyLead,
        lead_assessment: str,
    ) -> str:
        return self["system/new_lead_system"].format(
            company_name=self.company_name,
            pharmacy_name=lead.name or "Unknown",
            contact_person=lead.contact_person or "Unknown",
            location=f"{lead.city or 'Unknown'}, {lead.state or 'Unknown'}",
            estimated_rx_volume=lead.estimated_rx_volume or "Unknown",
            lead_assessment=lead_assessment,
        )

    def get_missing_info_question(self, missing_field: str) -> str | None:
        try:
            questions_content = self["responses/missing_info_questions"]

            questions = self._parse_questions_file(questions_content)

            return questions.get(missing_field)

        except Exception:
            return None

    def _parse_questions_file(self, questions_content: str) -> dict[str, str]:
        questions = {}
        for line in questions_content.split("\n"):
            if ":" in line:
                field, question = line.split(":", 1)
                questions[field.strip()] = question.strip()
        return questions

    def get_lead_assessment(
        self,
        lead: NewPharmacyLead,
    ) -> str:
        if not lead.estimated_rx_volume:
            return self["responses/lead_assessment_unknown"].format(
                company_name=self.company_name
            )

        volume = lead.estimated_rx_volume

        if volume >= 100:
            return self["responses/lead_assessment_high_volume"].format(
                estimated_rx_volume=volume,
                company_name=self.company_name
            )
        if volume >= 50:
            return self["responses/lead_assessment_medium_volume"].format(
                estimated_rx_volume=volume,
                company_name=self.company_name
            )

        return self["responses/lead_assessment_low_volume"].format(
            estimated_rx_volume=volume,
            company_name=self.company_name
        )

    def get_missing_info_prompt_for_lead(self, lead: NewPharmacyLead) -> str | None:
        questions_to_ask = []
        if not lead.name:
            question = self.get_missing_info_question("name")
            if question:
                questions_to_ask.append(question)

        if not lead.contact_person:
            question = self.get_missing_info_question("contact_person")
            if question:
                questions_to_ask.append(question)

        if not lead.city or not lead.state:
            question = self.get_missing_info_question("location")
            if question:
                questions_to_ask.append(question)

        if not lead.estimated_rx_volume:
            question = self.get_missing_info_question("rx_volume")
            if question:
                questions_to_ask.append(question)

        if not questions_to_ask:
            return None
            
        if len(questions_to_ask) == 1:
            return questions_to_ask[0]
        else:
            return " Also, " + " And ".join(questions_to_ask)

    def reload_prompts(self) -> None:
        self._cache.clear()
