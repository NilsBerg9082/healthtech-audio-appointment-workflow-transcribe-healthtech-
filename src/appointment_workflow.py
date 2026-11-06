"""Typed, patient-safe decisions for an appointment transcript."""

from enum import Enum

from pydantic import BaseModel, Field


class NoticeKind(str, Enum):
    ROUTINE = "routine"
    CLINIC_REVIEW = "clinic_review"


class TranscriptRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    appointment_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)


class PatientNotice(BaseModel):
    appointment_id: str
    kind: NoticeKind
    message: str
    requires_clinician_review: bool


def decide_notice(request: TranscriptRequest) -> PatientNotice:
    """Turn transcript content into a conservative operational next step."""
    urgent_terms = ("chest pain", "trouble breathing", "fainted", "severe bleeding")
    text = request.transcript.casefold()
    needs_review = any(term in text for term in urgent_terms)
    if needs_review:
        return PatientNotice(
            appointment_id=request.appointment_id,
            kind=NoticeKind.CLINIC_REVIEW,
            message="Your care team will review this appointment note promptly.",
            requires_clinician_review=True,
        )
    return PatientNotice(
        appointment_id=request.appointment_id,
        kind=NoticeKind.ROUTINE,
        message="Your appointment note was received for routine care-team follow-up.",
        requires_clinician_review=False,
    )
