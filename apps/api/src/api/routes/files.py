import os
import uuid
import shutil
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.file_asset import FileAsset
from api.schemas.file_asset import FileAssetResponse

router = APIRouter(prefix="/files", tags=["files"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


@router.post("/", response_model=FileAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save the file locally
    file_id = uuid.uuid4()
    extension = file.filename.split(".")[-1] if "." in file.filename else ""
    local_filename = f"{file_id}.{extension}" if extension else f"{file_id}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Get file stats
    file_size = os.path.getsize(file_path)
    
    # Create DB entry
    file_asset = FileAsset(
        id=file_id,
        filename=file.filename,
        file_type=extension.upper() or "BINARY",
        mime_type=file.content_type,
        file_size=file_size,
        storage_url=f"/api/v1/files/{file_id}/download",
        organization_id=membership.organization_id,
    )
    
    db.add(file_asset)
    db.commit()
    db.refresh(file_asset)
    return file_asset


@router.get("/", response_model=List[FileAssetResponse])
def list_files(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(FileAsset)
        .filter(FileAsset.organization_id == membership.organization_id)
        .all()
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    file_asset = (
        db.query(FileAsset)
        .filter(
            FileAsset.id == file_id,
            FileAsset.organization_id == membership.organization_id,
        )
        .first()
    )
    if not file_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File asset not found"
        )
        
    # Delete local file if it exists
    extension = file_asset.filename.split(".")[-1] if "." in file_asset.filename else ""
    local_filename = f"{file_id}.{extension}" if extension else f"{file_id}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.delete(file_asset)
    db.commit()


@router.get("/{file_id}/download")
def download_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    from fastapi.responses import FileResponse
    file_asset = (
        db.query(FileAsset)
        .filter(
            FileAsset.id == file_id,
            FileAsset.organization_id == membership.organization_id,
        )
        .first()
    )
    if not file_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File asset not found"
        )
        
    extension = file_asset.filename.split(".")[-1] if "." in file_asset.filename else ""
    local_filename = f"{file_id}.{extension}" if extension else f"{file_id}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File physical copy missing"
        )
        
    return FileResponse(
        path=file_path,
        filename=file_asset.filename,
        media_type=file_asset.mime_type,
    )
