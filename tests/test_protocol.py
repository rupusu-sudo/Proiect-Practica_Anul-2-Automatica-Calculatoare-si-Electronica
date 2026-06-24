import uuid
from datetime import datetime, timezone
import pytest  # pyrefly: ignore [missing-import]
from pydantic import ValidationError  # pyrefly: ignore [missing-import]
from shared.protocol import A2AMessage, A2AResponse

def test_valid_a2a_message_creation():
    msg = A2AMessage(
        sender="coordinator",
        receiver="summarizer",
        task_type="summarize",
        payload={"text": "Hello world"}
    )
    assert isinstance(msg.message_id, uuid.UUID)
    assert msg.sender == "coordinator"
    assert msg.receiver == "summarizer"
    assert isinstance(msg.timestamp, datetime)
    assert msg.priority == 3
    assert msg.payload == {"text": "Hello world"}

def test_invalid_agent_names():
    with pytest.raises(ValidationError) as excinfo:
        A2AMessage(
            sender="malicious_agent",
            receiver="summarizer",
            task_type="summarize",
            payload={"text": "test"}
        )
    assert "nu este valid" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        A2AMessage(
            sender="coordinator",
            receiver="database",
            task_type="summarize",
            payload={"text": "test"}
        )
    assert "nu este valid" in str(excinfo.value)

def test_priority_boundaries():
    with pytest.raises(ValidationError):
        A2AMessage(
            sender="coordinator",
            receiver="summarizer",
            task_type="summarize",
            priority=0,
            payload={"text": "test"}
        )

    with pytest.raises(ValidationError):
        A2AMessage(
            sender="coordinator",
            receiver="summarizer",
            task_type="summarize",
            priority=6,
            payload={"text": "test"}
        )

    for p in [1, 2, 3, 4, 5]:
        msg = A2AMessage(
            sender="coordinator",
            receiver="summarizer",
            task_type="summarize",
            priority=p,
            payload={"text": "test"}
        )
        assert msg.priority == p

def test_sender_receiver_equality():
    with pytest.raises(ValidationError) as excinfo:
        A2AMessage(
            sender="coordinator",
            receiver="coordinator",
            task_type="orchestrate",
            payload={"text": "test"}
        )
    assert "Expeditorul și destinatarul nu pot fi același agent" in str(excinfo.value)

def test_empty_payload():
    with pytest.raises(ValidationError) as excinfo:
        A2AMessage(
            sender="coordinator",
            receiver="summarizer",
            task_type="summarize",
            payload={}
        )
    assert "Payload-ul nu poate fi gol" in str(excinfo.value)

def test_valid_a2a_response_completed():
    resp = A2AResponse(
        message_id=uuid.uuid4(),
        status="completed",
        processing_time=1.45,
        result={"summary": "Done"}
    )
    assert resp.status == "completed"
    assert resp.result == {"summary": "Done"}
    assert resp.error is None

def test_valid_a2a_response_failed():
    msg_id = uuid.uuid4()
    resp = A2AResponse(
        message_id=msg_id,
        status="failed",
        processing_time=0.01,
        error="Service Unavailable"
    )
    assert resp.status == "failed"
    assert resp.result is None
    assert resp.error == "Service Unavailable"

def test_invalid_a2a_response_combinations():
    with pytest.raises(ValidationError):
        A2AResponse(
            message_id=uuid.uuid4(),
            status="completed",
            processing_time=0.5
        )

    with pytest.raises(ValidationError):
        A2AResponse(
            message_id=uuid.uuid4(),
            status="failed",
            processing_time=0.5
        )
