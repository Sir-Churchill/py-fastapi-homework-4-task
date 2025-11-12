import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.params import Depends, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from database import get_db, UserModel, UserProfileModel
from schemas.profiles import ProfileResponseSchema, ProfileSchema
from sqlalchemy.orm import selectinload

from storages.interfaces import S3StorageInterface

from config.dependencies import get_s3_storage_client

from database.models.accounts import GenderEnum

router = APIRouter()


async def save_avatar(file, s3_client, user_id) -> str:
    file_data = await file.read()

    max_size_mb = 1
    if len(file_data) > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 1MB limit.")

    extension = file.filename.split(".")[-1]
    unique_filename = f"avatars/{user_id}_avatar.{extension}"

    await s3_client.upload_file(unique_filename, file_data)

    file_url = await s3_client.get_file_url(unique_filename)

    return file_url


@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=201)
async def user_profile(
        user_id: int,
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: GenderEnum = Form(...),
        date_of_birth: date = Form(...),
        info: str = Form(...),
        avatar: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        s3_client: S3StorageInterface = Depends(get_s3_storage_client)
):
    result = await db.execute(
        select(UserModel).options(selectinload(UserModel.profile)).where(UserModel.id == user_id)
    )
    user_db = result.scalar_one_or_none()

    if not user_db or not user_db.is_active:
        raise HTTPException(status_code=401, detail="User not found or not active.")
    elif user_db.profile:
        raise HTTPException(status_code=403, detail="User already has a profile.")


    try:
        avatar_url = await save_avatar(avatar, s3_client, user_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload avatar. Please try again later.")

    profile = UserProfileModel(
        first_name=first_name,
        last_name=last_name,
        avatar=avatar_url,
        gender=gender,
        date_of_birth=date_of_birth,
        info=info,
        user_id=user_id
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
