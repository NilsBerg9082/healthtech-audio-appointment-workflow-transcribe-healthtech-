from appointment_workflow import NoticeKind, TranscriptRequest, decide_notice


def test_transcript_with_breathing_difficulty_routes_to_clinician_review():
    request = TranscriptRequest(
        patient_id="patient-17",
        appointment_id="appointment-204",
        transcript="The patient reports trouble breathing after walking upstairs.",
    )

    notice = decide_notice(request)

    assert notice.kind is NoticeKind.CLINIC_REVIEW
    assert notice.requires_clinician_review is True
    assert notice.appointment_id == "appointment-204"
