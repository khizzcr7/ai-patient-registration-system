import re
from datetime import datetime, date
from typing import Generic, TypeVar, Optional, Union, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict

T = TypeVar('T')

ALLOWED_SEX_VALUES = {"Male", "Female", "Other", "Decline to Answer"}

class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[Union[str, dict, List[Any]]] = None

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str
    sex: str
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: str = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        if not v:
            raise ValueError("Phone number is required")
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("Phone number must have exactly 10 numeric digits")
        return digits

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) != 10:
            raise ValueError("Emergency contact phone must have exactly 10 numeric digits")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if not v:
            raise ValueError("State is required")
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z]{2}$", cleaned):
            raise ValueError("State must be a 2-letter uppercase alphabetic code (e.g., CA, NY)")
        return cleaned

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        if not v:
            raise ValueError("Zip code is required")
        cleaned = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", cleaned):
            raise ValueError("Zip code must be 5-digit standard or 9-digit ZIP+4 format")
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: str) -> str:
        if not v:
            raise ValueError("Date of birth is required")
        cleaned = v.strip()
        parsed_date = None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(cleaned, fmt).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            raise ValueError("Date of birth must be in MM/DD/YYYY or YYYY-MM-DD format")
        
        if parsed_date > date.today():
            raise ValueError("Date of birth cannot be in the future")
        
        return parsed_date.strftime("%m/%d/%Y")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        if not v:
            raise ValueError("Sex is required")
        cleaned = v.strip()
        matched = next((item for item in ALLOWED_SEX_VALUES if item.lower() == cleaned.lower()), None)
        if not matched:
            allowed_str = ", ".join(sorted(ALLOWED_SEX_VALUES))
            raise ValueError(f"Sex must be one of the following: {allowed_str}")
        return matched

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("Phone number must have exactly 10 numeric digits")
        return digits

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) != 10:
            raise ValueError("Emergency contact phone must have exactly 10 numeric digits")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z]{2}$", cleaned):
            raise ValueError("State must be a 2-letter uppercase alphabetic code (e.g., CA, NY)")
        return cleaned

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", cleaned):
            raise ValueError("Zip code must be 5-digit standard or 9-digit ZIP+4 format")
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        parsed_date = None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(cleaned, fmt).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            raise ValueError("Date of birth must be in MM/DD/YYYY or YYYY-MM-DD format")
        if parsed_date > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return parsed_date.strftime("%m/%d/%Y")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        matched = next((item for item in ALLOWED_SEX_VALUES if item.lower() == cleaned.lower()), None)
        if not matched:
            allowed_str = ", ".join(sorted(ALLOWED_SEX_VALUES))
            raise ValueError(f"Sex must be one of the following: {allowed_str}")
        return matched

class PatientResponse(PatientBase):
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
