import logging
import os
import sys
import re
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Patient
from schemas import (
    APIResponse,
    PatientCreate,
    PatientUpdate,
    PatientResponse
)

# Configure comprehensive stdout logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("patient_registration_backend")

app = FastAPI(
    title="Voice AI Patient Registration System",
    description="Production-Ready FastAPI Backend for Voice AI Patient Registration",
    version="1.0.0"
)

# ASGI Middleware to resolve Vercel serverless path prefix routing mismatches
@app.middleware("http")
async def vercel_path_rewrite_middleware(request: Request, call_next):
    path = request.scope.get("path", "")
    if path.startswith("/api/index.py"):
        request.scope["path"] = path[len("/api/index.py"):] or "/"
    elif path.startswith("/api") and not path.startswith("/api/"):
        request.scope["path"] = path[len("/api"):] or "/"
    return await call_next(request)

# Setup Jinja2 templates directory with absolute path for Vercel compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Custom Exception Class for carrying response payload along with status code
class EnvelopeHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, data: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.data = data

# Custom Exception Handlers enforcing standard JSON envelope {"data": ..., "error": ...}
@app.exception_handler(EnvelopeHTTPException)
async def envelope_http_exception_handler(request: Request, exc: EnvelopeHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": exc.data, "error": exc.detail}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": getattr(exc, "data", None), "error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"data": None, "error": exc.errors()}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"data": None, "error": "Internal server error"}
    )

# Ensure database tables are created automatically
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Database table creation during import: {e}")

# Startup Event for Table Creation and Seeding
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
    
    from database import SessionLocal
    db = SessionLocal()
    try:
        patient_count = db.query(Patient).count()
        if patient_count == 0:
            logger.info("Database empty. Seeding 2 sample patients...")
            sample1 = Patient(
                first_name="Jane",
                last_name="Doe",
                date_of_birth="05/14/1990",
                sex="Female",
                phone_number="4155550199",
                email="jane.doe@example.com",
                address_line_1="123 Market Street",
                address_line_2="Suite 400",
                city="San Francisco",
                state="CA",
                zip_code="94107",
                insurance_provider="Blue Cross Blue Shield",
                insurance_member_id="BCBS12345678",
                preferred_language="English",
                emergency_contact_name="John Doe",
                emergency_contact_phone="4155550198"
            )
            sample2 = Patient(
                first_name="John",
                last_name="Smith",
                date_of_birth="11/22/1985",
                sex="Male",
                phone_number="2125550144",
                email="john.smith@example.com",
                address_line_1="456 5th Avenue",
                city="New York",
                state="NY",
                zip_code="10001",
                insurance_provider="Aetna",
                insurance_member_id="AET98765432",
                preferred_language="English",
                emergency_contact_name="Mary Smith",
                emergency_contact_phone="2125550145"
            )
            db.add(sample1)
            db.add(sample2)
            db.commit()
            logger.info("Successfully seeded 2 sample patient records.")
        else:
            logger.info(f"Database contains {patient_count} existing patient records.")
    except Exception as e:
        logger.error(f"Error during startup database seeding: {e}")
    finally:
        db.close()

# REST API Routes

@app.get("/")
def root():
    return {"message": "Patient Registration API is Live!"}

@app.get("/health", response_model=APIResponse[dict])
def health_check():
    return {"data": {"status": "healthy", "service": "Patient Registration System API"}, "error": None}

@app.post("/patients", response_model=APIResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    logger.info(f"[INCOMING REGISTRATION PAYLOAD]: {payload.model_dump_json()}")

    clean_phone = payload.phone_number

    # Duplicate check: check if an active patient with this phone number exists
    existing_patient = db.query(Patient).filter(
        Patient.phone_number == clean_phone,
        Patient.deleted_at.is_(None)
    ).first()

    if existing_patient:
        logger.warning(f"Duplicate registration detected for phone number: {clean_phone}")
        patient_data = PatientResponse.model_validate(existing_patient).model_dump(mode="json")
        raise EnvelopeHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient with this phone number already exists.",
            data=patient_data
        )

    new_patient = Patient(**payload.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    logger.info(f"Successfully registered patient {new_patient.first_name} {new_patient.last_name} (ID: {new_patient.patient_id})")
    return {"data": PatientResponse.model_validate(new_patient), "error": None}

@app.get("/patients", response_model=APIResponse[List[PatientResponse]])
def list_patients(
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    date_of_birth: Optional[str] = Query(None, description="Filter by date of birth"),
    phone_number: Optional[str] = Query(None, description="Filter by 10-digit phone number"),
    db: Session = Depends(get_db)
):
    query = db.query(Patient).filter(Patient.deleted_at.is_(None))

    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name.strip()}%"))
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth.strip())
    if phone_number:
        clean_phone = re.sub(r"\D", "", phone_number)
        query = query.filter(Patient.phone_number == clean_phone)

    patients = query.order_by(Patient.created_at.desc()).all()
    patient_responses = [PatientResponse.model_validate(p) for p in patients]
    return {"data": patient_responses, "error": None}

@app.get("/patients/{id}", response_model=APIResponse[PatientResponse])
def get_patient(id: UUID, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == id,
        Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    return {"data": PatientResponse.model_validate(patient), "error": None}

@app.put("/patients/{id}", response_model=APIResponse[PatientResponse])
def update_patient(id: UUID, payload: PatientUpdate, db: Session = Depends(get_db)):
    logger.info(f"[UPDATE PATIENT PAYLOAD for ID {id}]: {payload.model_dump_json(exclude_unset=True)}")

    patient = db.query(Patient).filter(
        Patient.patient_id == id,
        Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(patient)

    logger.info(f"Successfully updated patient record (ID: {id})")
    return {"data": PatientResponse.model_validate(patient), "error": None}

@app.delete("/patients/{id}", response_model=APIResponse[dict])
def delete_patient(id: UUID, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == id,
        Patient.deleted_at.is_(None)
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    patient.deleted_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Soft-deleted patient record (ID: {id})")
    return {
        "data": {
            "message": "Patient soft-deleted successfully",
            "patient_id": str(id)
        },
        "error": None
    }

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(
        Patient.deleted_at.is_(None)
    ).order_by(Patient.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"patients": patients}
    )
