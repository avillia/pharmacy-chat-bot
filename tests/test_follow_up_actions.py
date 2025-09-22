import pytest
from unittest.mock import patch
import env
from src.api.follow_up_actions import (
    send_email,
    schedule_callback,
    send_pharmacy_welcome_email,
    send_lead_follow_up_email,
    create_crm_entry
)
from src.core.models import Pharmacy, NewPharmacyLead, Prescription


class TestFollowUpActions:
    
    @pytest.fixture
    def sample_pharmacy(self):
        return Pharmacy(
            id=1,
            name="Test Pharmacy",
            phone="+1-555-TEST-PHARM",
            email="test@testpharmacy.com",
            city="Test City",
            state="TS",
            prescriptions=[
                Prescription(drug="TestDrug A", count=75),
                Prescription(drug="TestDrug B", count=50),
            ]
        )
    
    @pytest.fixture
    def high_volume_pharmacy(self):
        return Pharmacy(
            id=2,
            name="High Volume Pharmacy",
            phone="+1-555-HIGH-VOL",
            email="contact@highvolume.com",
            city="Big City",
            state="BC",
            prescriptions=[
                Prescription(drug="Popular Drug", count=150),
            ]
        )
    
    @pytest.fixture
    def pharmacy_no_email(self):
        return Pharmacy(
            id=3,
            name="No Email Pharmacy",
            phone="+1-555-NO-EMAIL",
            email=None,
            city="Some City",
            state="SC",
            prescriptions=[]
        )
    
    @pytest.fixture
    def complete_lead(self):
        return NewPharmacyLead(
            phone="+1-555-COMPLETE",
            name="Complete Lead Pharmacy",
            contact_person="Jane Smith",
            city="Lead City",
            state="LC",
            estimated_rx_volume=80,
            preferred_contact="email"
        )
    
    @pytest.fixture
    def incomplete_lead(self):
        return NewPharmacyLead(
            phone="+1-555-INCOMPLETE",
            name="Incomplete Pharmacy"
        )
    
    def test_send_email_basic(self, capsys):
        result = send_email(
            "test@example.com",
            "Test Subject",
            "Test content here"
        )
        
        assert result is True
        captured = capsys.readouterr()
        assert "📧 EMAIL SENT" in captured.out
        assert "To: test@example.com" in captured.out
        assert "Subject: Test Subject" in captured.out
        assert "Test content here" in captured.out
    
    def test_send_email_custom_sender(self, capsys):
        result = send_email(
            "recipient@example.com",
            "Custom Subject",
            "Custom content",
            "Custom Sender"
        )
        
        assert result is True
        captured = capsys.readouterr()
        assert "From: Custom Sender" in captured.out
    
    def test_schedule_callback_basic(self, capsys):
        result = schedule_callback("+1-555-CALLBACK")
        
        assert "CB-" in result
        assert "tomorrow between 9 AM - 5 PM EST" in result
        captured = capsys.readouterr()
        assert "📞 CALLBACK SCHEDULED" in captured.out
        assert "Phone: +1-555-CALLBACK" in captured.out
    
    def test_schedule_callback_with_time_and_notes(self, capsys):
        result = schedule_callback(
            "+1-555-CUSTOM",
            preferred_time="Monday 2 PM",
            notes="Important client discussion"
        )
        
        assert "Monday 2 PM" in result
        captured = capsys.readouterr()
        assert "Scheduled for: Monday 2 PM" in captured.out
        assert "Notes: Important client discussion" in captured.out
    
    def test_send_pharmacy_welcome_email_success(self, sample_pharmacy, capsys):
        result = send_pharmacy_welcome_email(sample_pharmacy)
        
        assert result is True
        captured = capsys.readouterr()
        assert "📧 EMAIL SENT" in captured.out
        assert "To: test@testpharmacy.com" in captured.out
        assert "Subject: Great to hear from Test Pharmacy again!" in captured.out
        assert "Hello Test Pharmacy team" in captured.out
        assert "Test City, TS" in captured.out
        assert "125 prescriptions" in captured.out
    
    def test_send_pharmacy_welcome_email_high_volume(self, high_volume_pharmacy, capsys):
        result = send_pharmacy_welcome_email(high_volume_pharmacy)
        
        assert result is True
        captured = capsys.readouterr()
        assert "As a high-volume pharmacy, you're exactly who we love working with!" in captured.out
    
    def test_send_pharmacy_welcome_email_no_email(self, pharmacy_no_email, capsys):
        result = send_pharmacy_welcome_email(pharmacy_no_email)
        
        assert result is False
        captured = capsys.readouterr()
        assert "⚠️  No email address on file for No Email Pharmacy" in captured.out
    
    def test_send_lead_follow_up_email_complete(self, complete_lead, capsys):
        result = send_lead_follow_up_email(complete_lead)
        
        assert result is True
        captured = capsys.readouterr()
        assert "📧 EMAIL SENT" in captured.out
        assert "To: leads@pharmesol.com" in captured.out
        assert "Subject: New Pharmacy Lead: Complete Lead Pharmacy" in captured.out
        assert "Pharmacy: Complete Lead Pharmacy" in captured.out
        assert "Contact: Jane Smith" in captured.out
        assert "Phone: +1-555-COMPLETE" in captured.out
        assert "Location: Lead City, LC" in captured.out
        assert "Est. Monthly Rx Volume: 80" in captured.out
        assert "Preferred Contact: email" in captured.out
        assert "Follow up needed: No" in captured.out
    
    def test_send_lead_follow_up_email_incomplete(self, incomplete_lead, capsys):
        result = send_lead_follow_up_email(incomplete_lead)
        
        assert result is True
        captured = capsys.readouterr()
        assert "Subject: New Pharmacy Lead: Incomplete Pharmacy" in captured.out
        assert "Contact: Not provided" in captured.out
        assert "Location: Unknown, Unknown" in captured.out
        assert "Est. Monthly Rx Volume: Not provided" in captured.out
        assert "Follow up needed: Yes - missing information" in captured.out
    
    def test_create_crm_entry_complete(self, complete_lead, capsys):
        entry_id = create_crm_entry(complete_lead)
        
        assert entry_id.startswith("CRM-")
        captured = capsys.readouterr()
        assert "💼 CRM ENTRY CREATED" in captured.out
        assert "Lead: Complete Lead Pharmacy" in captured.out
        assert "Phone: +1-555-COMPLETE" in captured.out
        assert "Status: Qualified" in captured.out
    
    def test_create_crm_entry_incomplete(self, incomplete_lead, capsys):
        entry_id = create_crm_entry(incomplete_lead)
        
        assert entry_id.startswith("CRM-")
        captured = capsys.readouterr()
        assert "Lead: Incomplete Pharmacy" in captured.out
        assert "Status: Needs Follow-up" in captured.out
    
    def test_template_integration_welcome_email(self, sample_pharmacy):
        with patch('src.api.follow_up_actions.send_email') as mock_send:
            mock_send.return_value = True
            
            result = send_pharmacy_welcome_email(sample_pharmacy)
            
            assert result is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0]
            email, subject, content = call_args
            
            assert email == "test@testpharmacy.com"
            assert "Test Pharmacy" in subject
            assert "Test Pharmacy team" in content
            assert "Test City, TS" in content
            assert "125 prescriptions" in content
            assert "Pharmesol Team" in content
    
    def test_template_integration_lead_notification(self, complete_lead):
        with patch('src.api.follow_up_actions.send_email') as mock_send:
            mock_send.return_value = True
            
            result = send_lead_follow_up_email(complete_lead)
            
            assert result is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0]
            email, subject, content = call_args
            
            assert email == "leads@pharmesol.com"
            assert "Complete Lead Pharmacy" in subject
            assert "Jane Smith" in content
            assert "Lead City, LC" in content
            assert "80" in content
            assert "email" in content
    
    def test_pharmacy_volume_assessment_in_email(self):
        regular_pharmacy = Pharmacy(
            id=1, name="Regular Pharmacy", phone="+1-555-REG", 
            email="reg@test.com", city="Regular City", state="RC",
            prescriptions=[Prescription(drug="Drug", count=50)]
        )
        
        high_volume_pharmacy = Pharmacy(
            id=2, name="High Volume Pharmacy", phone="+1-555-HIGH",
            email="high@test.com", city="High City", state="HC", 
            prescriptions=[Prescription(drug="Drug", count=150)]
        )
        
        with patch('src.api.follow_up_actions.send_email') as mock_send:
            mock_send.return_value = True
            
            send_pharmacy_welcome_email(regular_pharmacy)
            regular_content = mock_send.call_args[0][2]
            
            send_pharmacy_welcome_email(high_volume_pharmacy)
            high_volume_content = mock_send.call_args[0][2]
            
            assert "we're excited to help you grow" in regular_content.lower()
            assert "exactly who we love working with" in high_volume_content.lower()
    
    def test_dynamic_company_branding(self):
        test_pharmacy = Pharmacy(
            id=1, name="Brand Test Pharmacy", phone="+1-555-BRAND",
            email="brand@test.com", city="Brand City", state="BC",
            prescriptions=[]
        )
        
        with patch('src.api.follow_up_actions.send_email') as mock_send:
            mock_send.return_value = True
            
            send_pharmacy_welcome_email(test_pharmacy)
            
            call_args = mock_send.call_args[0]
            content = call_args[2]
            
            assert env.COMPANY_NAME in content
    
    def test_lead_notification_email_address_generation(self, complete_lead):
        with patch('src.api.follow_up_actions.send_email') as mock_send:
            mock_send.return_value = True
            
            send_lead_follow_up_email(complete_lead)
            
            call_args = mock_send.call_args[0]
            email = call_args[0]
            
            assert email == f"leads@{env.COMPANY_NAME.lower()}.com"


def test_follow_up_actions_integration():
    print("\n🧪 Testing Follow-Up Actions Integration")
    print("=" * 50)
    
    test_pharmacy = Pharmacy(
        id=999,
        name="Integration Test Pharmacy",
        phone="+1-555-INTEGRATION",
        email="integration@test.com",
        city="Integration City",
        state="IC",
        prescriptions=[Prescription(drug="TestDrug", count=120)]
    )
    
    print("📧 Testing welcome email:")
    result = send_pharmacy_welcome_email(test_pharmacy)
    print(f"✅ Welcome email sent: {result}")
    
    test_lead = NewPharmacyLead(
        phone="+1-555-TEST-LEAD",
        name="Test Lead Pharmacy",
        contact_person="Test Person",
        city="Test City",
        state="TC",
        estimated_rx_volume=90
    )
    
    print("\n📨 Testing lead notification:")
    result = send_lead_follow_up_email(test_lead)
    print(f"✅ Lead notification sent: {result}")
    
    print("\n📞 Testing callback scheduling:")
    callback_id = schedule_callback(
        "+1-555-CALLBACK-TEST",
        notes="Integration test callback"
    )
    print(f"✅ Callback scheduled: {callback_id}")
    
    print("\n💼 Testing CRM entry:")
    crm_id = create_crm_entry(test_lead)
    print(f"✅ CRM entry created: {crm_id}")
    
    print("\n✅ Follow-up actions integration test completed!")


if __name__ == "__main__":
    test_follow_up_actions_integration()
    print("\n💡 To run full test suite: pytest tests/test_follow_up_actions.py -v")
