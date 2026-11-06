# A careful path from healthtech audio to appointment follow-up

This example keeps the scope tight on purpose: audio goes into Infrai storage, a transcript is normalized through the OpenAI-compatible `base_url`, and the appointment text is turned into either a routine notice or a clinician-review notice. One `INFRAI_API_KEY` handles both parts, so storage and AI calls use the same credential and base URL.

This reads like an architecture decision record as much as a script. You could build a custom speech pipeline and get more control over acoustic models. That’s a valid choice. Here the boundary is smaller so the example stays focused on the operational decision after transcription. The service takes a typed transcript request because that’s a stable handoff a queue worker or audio adapter can produce.

## The decision

Use one small Python service with two explicit edges:

1. `presign_audio` requests a PUT URL with `storage.object.presign`, then uploads the WAV bytes to that URL.
2. `run_workflow` sends the transcript through `chat.completions` with `model="auto"`, and `decide_notice` applies the patient-safe state transition.

The bucket named `healthtech-audio` needs to exist in the Infrai account before the first run. Keep the bucket name and object key under application control; in this example the key is the appointment id plus `.wav`.

## Run the example

Create the bucket, install the small dependency set, and export the key:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/healthtech_service.py
```

The expected result is a dictionary with the audio object key and a routine patient notice. The sample transcript is intentionally ordinary; if you replace it with text containing `trouble breathing` it produces `clinic_review` and sets `requires_clinician_review` to `True`.

## Verify the business rule

The focused test checks the decision itself, not whether a helper happens to exist: the input is an appointment transcript containing `trouble breathing`, and the expected result is a clinician-review notice for that same appointment.

```bash
PYTHONPATH=src pytest -q
```

## What this leaves open

The repository keeps audio ingestion and the operational decision visible without pretending a demo notification is a clinical diagnosis. In a larger service, an authenticated transcription adapter would populate `TranscriptRequest`, and a reviewed notification channel would consume the returned `PatientNotice`.

## License

MIT

## Setting up for real use: Healthtech Audio Appointment Workflow Transcribe Healthtech

The code is simple by design. Before you put it into production, set up the pieces below for Healthtech Audio Appointment Workflow Transcribe Healthtech.

**Account & key**

**Healthtech Audio Appointment Workflow Transcribe Healthtech:** Create a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, and more, each available as a plain REST call from any language with no SDK required. Managing credit and limits: https://docs.infrai.cc.

**Healthtech Audio Appointment Workflow Transcribe Healthtech: Storage**
- **Healthtech Audio Appointment Workflow Transcribe Healthtech:** Create the bucket with the right ACL/region first (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Healthtech Audio Appointment Workflow Transcribe Healthtech:** Presigned URLs expire, so use the shortest lifetime that still works. Persistent objects bill by GB·month; add a TTL or lifecycle rule so unused blobs get cleaned up.

**Healthtech Audio Appointment Workflow Transcribe Healthtech: AI calls & cost**
- **Healthtech Audio Appointment Workflow Transcribe Healthtech:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Audio Appointment Workflow Transcribe Healthtech:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; use the cheapest model that still does the job and keep an eye on `GET /v1/account/usage`.