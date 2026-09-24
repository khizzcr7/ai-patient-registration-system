# Assessment Compliance Audit

This system was built to explicitly fulfill all requirements in the Patient Registration System Technical Assessment.

### 1. Telephony & Voice Agent
- **US Phone Number Provisioned:** Vapi number (+1 662-546-8194) is active and receives inbound calls.
- **Conversational Flow:** The LLM (Claude 3.5 Sonnet) is strictly prompted to avoid IVR menus, collect 1-2 fields at a time, and handle mid-sentence corrections naturally.
- **Error Handling:** Prompts catch future DOBs and invalid phone lengths before saving.
- **Confirmation:** A mandatory read-back of all details occurs before the webhook is triggered.

### 2. Patient Demographic Data Model[cite: 9]
- **Schema Enforcement:** 9 required fields and 6 optional fields are strictly validated via Pydantic.
- **Auto-Generated Fields:** `patient_id` (UUID), `created_at` (UTC), and `updated_at` (UTC) are handled by the database schema.

### 3. Persistent Database[cite: 9]
- **Engine:** Neon PostgreSQL (Serverless Relational DB).
- **Persistence:** Data survives server restarts and subsequent calls.

### 4. Web Service (REST API)[cite: 9]
- **Endpoints:** `GET /patients`, `GET /patients/{id}`, `POST /patients`, `PUT /patients/{id}`, `DELETE /patients/{id}` are all implemented.
- **Standards:** All responses utilize the `{ "data": {...}, "error": null }` envelope. Invalid payloads (e.g., 3-digit phone numbers) return HTTP 422.
- **Soft Deletes:** Deleting sets a `deleted_at` timestamp.

### 5. Bonus Challenges Completed[cite: 9]
- **Duplicate Detection:** `POST /patients` returns a 409 Conflict if the phone number already exists. The Voice Agent reads this and offers to update the existing record.
- **Dashboard:** A simple web UI is deployed at `/dashboard` to display registered patients in real-time.