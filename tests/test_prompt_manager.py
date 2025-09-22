import pytest
from src.core.prompt_manager import PromptManager
from src.core.models import Pharmacy, NewPharmacyLead, Prescription


class TestPromptManager:
    
    @pytest.fixture
    def prompt_manager(self):
        return PromptManager("prompts", "TestCompany")
    
    @pytest.fixture
    def sample_pharmacy(self):
        return Pharmacy(
            id=999,
            name="Test Pharmacy",
            phone="+1-555-TEST-123",
            email="test@example.com",
            city="Test City",
            state="TS",
            prescriptions=[
                Prescription(drug="TestDrug A", count=75),
                Prescription(drug="TestDrug B", count=50),
                Prescription(drug="TestDrug C", count=25),
            ]
        )
    
    @pytest.fixture
    def sample_high_volume_lead(self):
        return NewPharmacyLead(
            phone="+1-555-HIGH-VOL",
            name="High Volume Pharmacy",
            contact_person="Jane Smith",
            city="Big City",
            state="BC",
            estimated_rx_volume=150
        )
    
    @pytest.fixture
    def sample_low_volume_lead(self):
        return NewPharmacyLead(
            phone="+1-555-LOW-VOL",
            name="Small Pharmacy",
            contact_person="Bob Johnson",
            city="Small Town",
            state="ST",
            estimated_rx_volume=25
        )
    
    @pytest.fixture
    def incomplete_lead(self):
        return NewPharmacyLead(
            phone="+1-555-INCOMPLETE",
            # Missing name, contact_person, city, state, estimated_rx_volume
        )
    
    def test_direct_file_access(self, prompt_manager):
        greeting = prompt_manager["responses/new_lead_greeting.txt"]
        assert "Hello!" in greeting
        assert "{company_name}" in greeting
        
        greeting_no_ext = prompt_manager["responses/new_lead_greeting"]
        assert greeting == greeting_no_ext
        
        greeting_cached = prompt_manager["responses/new_lead_greeting"]
        assert greeting == greeting_cached
    
    def test_file_not_found(self, prompt_manager):
        with pytest.raises(FileNotFoundError):
            prompt_manager["responses/non_existent_template"]
    
    def test_returning_customer_greeting(self, prompt_manager, sample_pharmacy):
        greeting = prompt_manager.get_returning_customer_greeting(
            sample_pharmacy
        )
        
        assert "Test Pharmacy" in greeting
        assert "Test City, TS" in greeting
        assert "150 prescriptions" in greeting  # Total volume
        assert "TestCompany" in greeting
        
        assert "High-volume pharmacy" in greeting
        
        assert "TestDrug A (75)" in greeting
        assert "TestDrug B (50)" in greeting
        assert "TestDrug C (25)" in greeting
    
    def test_new_lead_greeting(self, prompt_manager):
        greeting = prompt_manager.get_new_lead_greeting()
        
        assert "Hello!" in greeting
        assert "TestCompany" in greeting
        assert "new pharmacy" in greeting.lower()
        assert "high-volume pharmacies" in greeting.lower()
    
    def test_returning_customer_system_prompt(self, prompt_manager, sample_pharmacy):
        system_prompt = prompt_manager.get_returning_customer_system_prompt(
            sample_pharmacy
        )
        
        assert "TestCompany" in system_prompt
        assert "Test Pharmacy" in system_prompt
        assert "Test City, TS" in system_prompt
        assert "150 total prescriptions" in system_prompt
        assert "high-volume pharmacy" in system_prompt.lower()
    
    def test_new_lead_system_prompt(self, prompt_manager, sample_high_volume_lead):
        assessment = "Test assessment message"
        system_prompt = prompt_manager.get_new_lead_system_prompt(
            sample_high_volume_lead, assessment
        )
        
        assert "TestCompany" in system_prompt
        assert "High Volume Pharmacy" in system_prompt
        assert "Jane Smith" in system_prompt
        assert "Big City, BC" in system_prompt
        assert "150" in system_prompt
        assert assessment in system_prompt
    
    def test_lead_assessment_high_volume(self, prompt_manager, sample_high_volume_lead):
        assessment = prompt_manager.get_lead_assessment(
            sample_high_volume_lead
        )
        
        assert "150 monthly prescriptions" in assessment
        assert "high-volume pharmacy" in assessment.lower()
        assert "TestCompany specializes" in assessment
    
    def test_lead_assessment_low_volume(self, prompt_manager, sample_low_volume_lead):
        assessment = prompt_manager.get_lead_assessment(
            sample_low_volume_lead
        )
        
        assert "pharmacy starts somewhere" in assessment.lower()
        assert "TestCompany" in assessment
        assert "comprehensive support" in assessment.lower()
    
    def test_lead_assessment_medium_volume(self, prompt_manager):
        medium_lead = NewPharmacyLead(
            phone="+1-555-MEDIUM",
            estimated_rx_volume=75  # Between 50-99
        )
        
        assessment = prompt_manager.get_lead_assessment(medium_lead)
        
        assert "75 monthly prescriptions" in assessment
        assert "growth potential" in assessment.lower()
        assert "scale efficiently" in assessment.lower()
    
    def test_lead_assessment_unknown_volume(self, prompt_manager):
        unknown_lead = NewPharmacyLead(
            phone="+1-555-UNKNOWN"
            # No estimated_rx_volume
        )
        
        assessment = prompt_manager.get_lead_assessment(unknown_lead)
        
        assert "learn more about your prescription volume" in assessment.lower()
    
    def test_missing_info_questions(self, prompt_manager):
        name_question = prompt_manager.get_missing_info_question("name")
        assert "name of your pharmacy" in name_question.lower()
        
        contact_question = prompt_manager.get_missing_info_question("contact_person")
        assert "your name" in contact_question.lower()
        
        location_question = prompt_manager.get_missing_info_question("location")
        assert "where is your pharmacy located" in location_question.lower()
        
        volume_question = prompt_manager.get_missing_info_question("rx_volume")
        assert "prescriptions do you fill" in volume_question.lower()
        
        unknown_question = prompt_manager.get_missing_info_question("unknown_field")
        assert unknown_question is None
    
    def test_missing_info_prompt_for_lead_complete(self, prompt_manager, sample_high_volume_lead):
        prompt = prompt_manager.get_missing_info_prompt_for_lead(sample_high_volume_lead)
        assert prompt is None
    
    def test_missing_info_prompt_for_lead_incomplete(self, prompt_manager, incomplete_lead):
        prompt = prompt_manager.get_missing_info_prompt_for_lead(incomplete_lead)
        assert prompt is not None
        assert "name of your pharmacy" in prompt.lower()
        
        incomplete_lead.name = "Test Pharmacy"
        prompt = prompt_manager.get_missing_info_prompt_for_lead(incomplete_lead)
        assert prompt is not None
        
        incomplete_lead.contact_person = "John Doe"
        prompt = prompt_manager.get_missing_info_prompt_for_lead(incomplete_lead)
        assert prompt is not None
        
        incomplete_lead.city = "Test City"
        incomplete_lead.state = "TS"
        prompt = prompt_manager.get_missing_info_prompt_for_lead(incomplete_lead)
        assert prompt is not None
        
        incomplete_lead.estimated_rx_volume = 50
        prompt = prompt_manager.get_missing_info_prompt_for_lead(incomplete_lead)
        assert prompt is None
    
    def test_cache_functionality(self, prompt_manager):
        first_load = prompt_manager["responses/new_lead_greeting"]
        second_load = prompt_manager["responses/new_lead_greeting"]
        assert first_load == second_load
        
        prompt_manager.reload_prompts()
        third_load = prompt_manager["responses/new_lead_greeting"]
        assert first_load == third_load
    
    def test_reload_prompts(self, prompt_manager):
        original = prompt_manager["responses/new_lead_greeting"]
        prompt_manager.reload_prompts()
        reloaded = prompt_manager["responses/new_lead_greeting"]
        assert original == reloaded


def test_prompt_manager_integration():
    """Integration test demonstrating complete PromptManager workflow."""
    print("\n🧪 PromptManager Integration Test")
    print("=" * 50)
    
    # Initialize PromptManager
    pm = PromptManager("prompts", "TestCompany")
    
    # Test with sample pharmacy
    pharmacy = Pharmacy(
        id=1,
        name="Integration Test Pharmacy",
        phone="+1-555-INTEGRATION",
        email="test@integration.com",
        city="Integration City",
        state="IC",
        prescriptions=[
            Prescription(drug="TestDrug", count=120),
        ]
    )
    
    print("🏥 Testing returning customer workflow:")
    greeting = pm.get_returning_customer_greeting(pharmacy)
    print(f"Greeting: {greeting[:100]}...")
    
    system_prompt = pm.get_returning_customer_system_prompt(pharmacy)
    print(f"System prompt: {system_prompt[:100]}...")
    
    # Test with sample lead
    lead = NewPharmacyLead(
        phone="+1-555-NEW-INTEGRATION",
        name="New Integration Pharmacy",
        contact_person="Test Person",
        city="New City",
        state="NC",
        estimated_rx_volume=80
    )
    
    print("\n📊 Testing new lead workflow:")
    assessment = pm.get_lead_assessment(lead)
    print(f"Assessment: {assessment}")
    
    new_greeting = pm.get_new_lead_greeting()
    print(f"New lead greeting: {new_greeting[:100]}...")
    
    print("\n✅ Integration test completed successfully!")


if __name__ == "__main__":
    # Run the integration test when script is executed directly
    test_prompt_manager_integration()
    print("\n💡 To run full test suite: pytest tests/test_prompt_manager.py -v")
