from pydantic import BaseModel, Field


class Prescription(BaseModel):
    """Represents a prescription with drug name and count."""

    drug: str = Field(..., description="Name of the prescribed drug")
    count: int = Field(..., ge=0, description="Number of prescriptions for this drug")


class Pharmacy(BaseModel):
    """Represents a pharmacy with all its details."""

    id: int = Field(..., description="Unique identifier for the pharmacy")
    name: str = Field(..., description="Name of the pharmacy")
    phone: str = Field(..., description="Phone number of the pharmacy")
    email: str | None = Field(None, description="Email address (may be None)")
    city: str = Field(..., description="City where pharmacy is located")
    state: str = Field(..., description="State where pharmacy is located")
    prescriptions: list[Prescription] = Field(default_factory=list, description="List of prescriptions")

    @property
    def total_rx_volume(self) -> int:
        """Calculate total prescription volume across all drugs."""
        return sum(prescription.count for prescription in self.prescriptions)

    @property
    def location(self) -> str:
        """Get formatted location string."""
        return f"{self.city}, {self.state}"

    @property
    def is_high_volume(self) -> bool:
        """Determine if this is a high-volume pharmacy (>100 total prescriptions)."""
        return self.total_rx_volume > 100


class NewPharmacyLead(BaseModel):
    """Represents information collected from a new pharmacy lead."""

    phone: str = Field(..., description="Phone number of the caller")
    name: str | None = Field(None, description="Pharmacy name")
    contact_person: str | None = Field(None, description="Name of contact person")
    city: str | None = Field(None, description="City location")
    state: str | None = Field(None, description="State location")
    estimated_rx_volume: int | None = Field(None, ge=0, description="Estimated monthly Rx volume")
    preferred_contact: str | None = Field(None, description="Preferred contact method (email/phone)")

    @property
    def is_complete(self) -> bool:
        """Check if we have enough information to qualify this lead."""
        return all(
            (
                self.name,
                self.contact_person,
                self.city,
                self.state,
            )
        )


class ConversationContext(BaseModel):
    """Tracks the context and state of an ongoing conversation."""

    caller_phone: str = Field(..., description="Phone number of the caller")
    pharmacy: Pharmacy | None = Field(None, description="Known pharmacy if recognized")
    new_lead: NewPharmacyLead | None = Field(None, description="New lead information if unknown caller")
    conversation_stage: str = Field(default="greeting", description="Current stage of conversation")
    messages: list[str] = Field(default_factory=list, description="Conversation history")

    @property
    def is_returning_customer(self) -> bool:
        """Check if this is a returning customer."""
        return self.pharmacy is not None

    @property
    def caller_name(self) -> str:
        """Get the name to use when addressing the caller."""
        if self.pharmacy:
            return self.pharmacy.name
        if self.new_lead and self.new_lead.contact_person:
            return self.new_lead.contact_person
        return "there"
