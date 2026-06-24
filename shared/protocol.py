import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator  # pyrefly: ignore [missing-import]

VALID_AGENTS = {"coordinator", "summarizer", "translator", "user", "researcher", "validator", "exporter"}


class A2AMessage(BaseModel):
    """Mesaj de cerere conform protocolului Agent-to-Agent (A2A)."""

    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sender: str = Field(...)
    receiver: str = Field(...)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    task_type: str = Field(...)
    priority: int = Field(default=3)
    payload: Dict[str, Any] = Field(...)

    @field_validator("sender", "receiver")
    @classmethod
    def validate_agent_name(cls, value: str) -> str:
        cleaned = value.lower().strip()
        if cleaned not in VALID_AGENTS:
            raise ValueError(f"Agentul '{value}' nu este valid. Trebuie să fie unul dintre {VALID_AGENTS}")
        return cleaned

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        if not (1 <= value <= 5):
            raise ValueError("Prioritatea trebuie să fie între 1 și 5 inclusiv.")
        return value

    @model_validator(mode="after")
    def validate_sender_receiver_not_same(self) -> "A2AMessage":
        if self.sender == self.receiver:
            raise ValueError("Expeditorul și destinatarul nu pot fi același agent.")
        return self

    @field_validator("payload")
    @classmethod
    def validate_payload_not_empty(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("Payload-ul nu poate fi gol și trebuie să conțină parametri pentru sarcină.")
        return value


class A2AResponse(BaseModel):
    """Mesaj de răspuns conform protocolului Agent-to-Agent (A2A)."""

    message_id: uuid.UUID = Field(...)
    status: Literal["completed", "failed"] = Field(...)
    processing_time: float = Field(...)
    result: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_status_results(self) -> "A2AResponse":
        if self.status == "completed" and self.result is None:
            raise ValueError("Rezultatul este obligatoriu atunci când statusul este 'completed'.")
        if self.status == "failed" and self.error is None:
            raise ValueError("Mesajul de eroare este obligatoriu atunci când statusul este 'failed'.")
        return self
