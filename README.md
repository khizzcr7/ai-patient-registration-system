# Voice AI Patient Registration System

A complete end-to-end Voice AI agent and REST API for conversational patient registration. Built for reliability, natural conversational flow, and strict data validation.

## 🚀 Live Demo & Links
* **Phone Number to Call:** `+1 (662) 546-8194`
* **API Base URL:** `https://ai-patient-registration-system.vercel.app`
* **Interactive API Docs (Swagger):** `https://ai-patient-registration-system.vercel.app/docs`
* **Web Dashboard (Bonus):** `https://ai-patient-registration-system.vercel.app/dashboard`

---

## 🏗️ Architecture & Separation of Concerns

The system is decoupled into three distinct layers to ensure the LLM handles conversation while the backend enforces strict business logic.

1. **Telephony & Voice AI (Vapi.ai + OpenAI):** 
   Handles the telephony layer, speech-to-text (STT), text-to-speech (TTS), and conversational LLM logic. The prompt is engineered to reject IVR-style interactions, handle mid-sentence corrections smoothly, conditionally offer optional fields, and enforce a mandatory read-back confirmation before triggering the webhook.
2. **Web Service (FastAPI / Serverless Python):** 
   A lightweight REST API deployed on Vercel. It acts as the ultimate source of truth, enforcing strict server-side validation (preventing future DOBs, validating 10-digit phone numbers) completely independently of the LLM. 
3. **Database (Neon PostgreSQL):** 
   A persistent, cloud-hosted relational database enforcing schema constraints, UUIDs, soft-deletes, and UTC timestamps.

---

## ✅ Core Features & Rubric Compliance
- **Conversational Flow:** Agent collects the 9 required fields naturally, prompts for optional fields exactly as requested, and performs a read-back confirmation.
- **Error Handling:** If the caller provides invalid data (e.g., 3-digit phone, future DOB), the LLM catches and re-prompts. If invalid data reaches the API, FastAPI strictly rejects it with a 422 Unprocessable Entity.
- **API Standards:** All endpoints (GET, POST, PUT, DELETE) are implemented. Responses are strictly wrapped in the `{"data": {...}, "error": null}` envelope.
- **Soft Deletion:** `DELETE /patients/{id}` sets a `deleted_at` timestamp rather than dropping the row.
- **Bonus - Duplicate Detection:** If a caller uses an existing phone number, the API returns a 409 Conflict. The voice agent recognizes this state and dynamically offers to update the existing record instead of crashing.

---

## ⚙️ Deployment & Configuration Guide

The following steps outline how this system was configured and deployed across its three core platforms.

### 1. Database Configuration (Neon PostgreSQL)
1. A new serverless PostgreSQL project was provisioned on Neon.
2. The database schema (tables for patients, UUID extensions, and UTC timestamps) was initialized.
3. The connection string was generated and copied for backend configuration.

### 2. Backend Deployment (Vercel)
1. The FastAPI codebase was linked to Vercel via GitHub deployment.
2. The `vercel.json` file was configured to route API requests to the serverless ASGI application.
3. The `DATABASE_URL` environment variable was injected into the Vercel project settings to enable database connectivity.
4. The deployment was published to the Vercel URL.

### 3. Voice Agent Configuration (Vapi.ai)
1. **Tool Creation:** A Custom API Tool named `register_patient` was created in Vapi. It points to the Vercel API `/patients` endpoint via a POST request. The payload schema was mapped strictly to the backend's expected JSON structure.
2. **Assistant Setup:** 
   * **Model:** Claude 3.5 Sonnet / OpenAI GPT-4o configured for conversational processing.
   * **Voice:** Configured for low-latency, natural TTS delivery, deliberately constrained to short sentences to prevent robotic buffering.
   * **System Prompt:** Engineered with strict rules to avoid markdown output, manage conversational flow, and validate data pre-submission.
3. **Telephony Integration:** A US phone number was provisioned within Vapi and assigned directly to the inbound assistant route.

---

## 🛠️ Local Setup Instructions

1. Clone the repository:
    git clone <your-repo-url>
    cd <repo-folder>

2. Create and activate a virtual environment:
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

3. Install dependencies:
    pip install -r requirements.txt

4. Configure the environment variables by creating a `.env` file in the root directory:
    DATABASE_URL="postgresql://<user>:<password>@<host>/<dbname>?sslmode=require"

5. Run the development server:
    uvicorn api.index:app --reload --port 8000

---

## ⚖️ Trade-offs & Known Limitations
* **Serverless Database Connections:** Vercel functions open new connections per invocation. While perfectly fine for this assessment's volume, a massive production environment would require a connection pooler like PgBouncer for Neon Postgres to prevent connection exhaustion.
* **Authentication:** The `/patients` webhook is currently public to ensure smooth testing for reviewers. In a production scenario, API key headers or Vapi webhook signature verification would be implemented to secure all write operations.