# Speech API (FastAPI + ElevenLabs Speech-to-Text)

Backend API สำหรับรับไฟล์เสียง/วิดีโอแล้วถอดเสียงเป็นข้อความด้วย ElevenLabs Speech-to-Text โดยรองรับภาษาไทยเป็นหลัก และออกแบบให้สามารถต่อยอดเป็น chunk-based realtime transcription ได้ในอนาคต

## Project Structure

```text
speech-api/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ schemas.py
│  ├─ services/
│  │  └─ whisper_service.py
│  ├─ routers/
│  │  └─ transcription_router.py
│  └─ utils/
│     └─ file_utils.py
├─ uploads/
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Features

- `GET /health`
- `POST /api/transcriptions` (multipart/form-data)
  - `file`: UploadFile (required)
  - `language`: string (optional เช่น `th`, `en`)
- เตรียม REST flow สำหรับ realtime/chunk session (ยังไม่เปิด WebSocket)
  - `POST /api/realtime-transcriptions/sessions`
  - `POST /api/realtime-transcriptions/sessions/{session_id}/chunks`
  - `POST /api/realtime-transcriptions/sessions/{session_id}/close`
  - `GET /api/realtime-transcriptions/sessions/{session_id}`
- รองรับไฟล์: `mp3`, `wav`, `webm`, `m4a`, `mp4`
- เปิด `vad_filter=True`
- ใช้ ElevenLabs Speech-to-Text API (`model_id` ค่าเริ่มต้น `scribe_v1`)

## Setup

1) สร้าง virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

2) ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

3) คัดลอกไฟล์ environment

```bash
cp .env.example .env
```

4) Run server

```bash
uvicorn app.main:app --reload --port 8000
```

5) เปิด Swagger

- http://localhost:8000/docs

## Environment Variables

```env
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_MODEL_ID=scribe_v1
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=200
CORS_ORIGINS=*
```




## Docker

### Build image

```bash
docker build -t speech-api:latest ./speech-api
```

### Run with Docker Compose

```bash
docker compose up -d --build
```

API docs: http://localhost:8000/docs

## Example curl

```bash
curl -X POST "http://localhost:8000/api/transcriptions" \
  -F "file=@test.mp3" \
  -F "language=th"
```

## Next.js Example (TypeScript)

```ts
const transcribeAudio = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", "th");

  const response = await fetch("http://localhost:8000/api/transcriptions", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to transcribe audio");
  }

  return response.json();
};
```

## Notes

- ยังไม่รวม WebSocket realtime (ออกแบบ service/route รองรับไว้แล้ว)
- ยังไม่รวม auth/database/queue/diarization
- temp file จะถูกลบใน `finally` ทุกครั้งหลังจบงาน
