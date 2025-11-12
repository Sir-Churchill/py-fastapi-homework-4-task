from datetime import date
from typing import Annotated

from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, field_validator, HttpUrl

from validation import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)

from database.models.accounts import GenderEnum

class ProfileSchema(BaseModel):
    first_name: str
    last_name: str
    gender: GenderEnum
    birth_date: date
    info: str


    @field_validator("first_name")
    def validate_first_name(cls, v):
        return validate_name(v)

    @field_validator("gender")
    def validate_gender(cls, v):
        return validate_gender(v)

    @field_validator("birth_date")
    def validate_birth_date(cls, v):
        return validate_birth_date(v)


class ProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str | None = None
    avatar: HttpUrl | None = None

