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

    def __getitem__(self, file_name: str) -> str:
        if not file_name.endswith(".txt"):
            file_name = f"{file_name}.txt"

        if file_name in self._cache:
            return self._cache[file_name]

        file_path = self.prompts_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            self._cache[file_name] = content
            return content

        except Exception as e:
            raise RuntimeError(
                f"Failed to read prompt file {file_path}: {str(e)}"
            ) from e

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

        return self["returning_customer_greeting"].format(
            pharmacy_name=pharmacy.name,
            location=pharmacy.location,
            total_rx_volume=pharmacy.total_rx_volume,
            top_drugs_text=top_drugs_text,
            high_volume_message=high_volume_message,
            company_name=self.company_name,
        )

    def get_new_lead_greeting(self) -> str:
        return self["new_lead_greeting"].format(company_name=self.company_name)

    def get_returning_customer_system_prompt(
        self,
        pharmacy: Pharmacy,
    ) -> str:
        volume_assessment = (
            "This is a high-volume pharmacy that's perfect for our services."
            if pharmacy.is_high_volume
            else "This pharmacy has growth potential."
        )

        return self["returning_customer_system"].format(
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
        return self["new_lead_system"].format(
            company_name=self.company_name,
            pharmacy_name=lead.name or "Unknown",
            contact_person=lead.contact_person or "Unknown",
            location=f"{lead.city or 'Unknown'}, {lead.state or 'Unknown'}",
            estimated_rx_volume=lead.estimated_rx_volume or "Unknown",
            lead_assessment=lead_assessment,
        )

    def get_missing_info_question(self, missing_field: str) -> str | None:
        try:
            questions_content = self["missing_info_questions"]

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
            return self["lead_assessment_unknown"].format(
                company_name=self.company_name
            )

        volume = lead.estimated_rx_volume

        if volume >= 100:
            template_name = "lead_assessment_high_volume"
        elif volume >= 50:
            template_name = "lead_assessment_medium_volume"
        else:
            template_name = "lead_assessment_low_volume"

        return self[template_name].format(
            estimated_rx_volume=volume, company_name=self.company_name
        )

    def get_missing_info_prompt_for_lead(self, lead: NewPharmacyLead) -> str | None:
        """
        Get the next question to ask for missing lead information.

        Args:
            lead: Current lead information

        Returns:
            Next question to ask, or None if lead is complete
        """
        # Check what information is missing and return the first question needed
        if not lead.name:
            return self.get_missing_info_question("name")

        if not lead.contact_person:
            return self.get_missing_info_question("contact_person")

        if not lead.city or not lead.state:
            return self.get_missing_info_question("location")

        if not lead.estimated_rx_volume:
            return self.get_missing_info_question("rx_volume")

        return None

    def reload_prompts(self) -> None:
        self._cache.clear()
