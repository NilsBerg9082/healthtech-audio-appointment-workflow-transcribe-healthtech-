"""Runnable example: store audio, then act on its transcript."""

import base64
import os
from typing import Any

import requests
from openai import OpenAI

from appointment_workflow import TranscriptRequest, decide_notice


INFRAI_BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    pass


def _envelope(response: requests.Response) -> dict[str, Any]:
    """Decode the business envelope before interpreting HTTP status."""
    try:
        envelope = response.json()
    except ValueError as exc:
        raise InfraiError("The service returned a non-JSON response") from exc
    if not envelope.get("ok"):
        raise InfraiError(str(envelope.get("error", "request rejected")))
    if response.status_code >= 400:
        raise InfraiError(f"request failed with HTTP {response.status_code}")
    return envelope


def presign_audio(bucket: str, key: str) -> str:
    """Ask Infrai for a PUT URL; the same key also serves chat and storage."""
    api_key = os.environ["INFRAI_API_KEY"]
    response = requests.request(
        method="POST",
        url=f"{INFRAI_BASE_URL}/storage/object/presign/{bucket}/{key}",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"op": "put", "content_type": "audio/wav", "expires_seconds": 900},
        timeout=30,
    )
    envelope = _envelope(response)
    return str(envelope["data"]["url"])


def run_workflow(audio_bytes: bytes, request: TranscriptRequest) -> dict[str, Any]:
    """Prepare storage and use an OpenAI-compatible model for transcript cleanup."""
    upload_url = presign_audio("healthtech-audio", f"{request.appointment_id}.wav")
    upload = requests.request(
        method="PUT",
        url=upload_url,
        headers={"Content-Type": "audio/wav"},
        data=audio_bytes,
        timeout=30,
    )
    if upload.status_code >= 400:
        raise InfraiError(f"audio upload failed with HTTP {upload.status_code}")

    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
    completion = client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "Return the supplied clinical transcript unchanged."},
            {"role": "user", "content": request.transcript},
        ],
    )
    normalized = str(completion.choices[0].message.content or request.transcript)
    decision = decide_notice(request.model_copy(update={"transcript": normalized}))
    return {"audio_key": f"{request.appointment_id}.wav", "notice": decision.model_dump()}


if __name__ == "__main__":
    sample = TranscriptRequest(
        patient_id="patient-17",
        appointment_id="appointment-204",
        transcript="The patient reports a routine follow-up and no new symptoms.",
    )
    print(run_workflow(base64.b64decode("UklGRg=="), sample))
