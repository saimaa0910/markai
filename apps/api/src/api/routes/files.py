import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.file_asset import FileAsset
from api.schemas.file_asset import FileAssetResponse
from api.services.storage_service import MinIOService
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

router = APIRouter(prefix="/files", tags=["files"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@router.post("/", response_model=FileAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    file_id = uuid.uuid4()
    original_filename = file.filename or "file"
    extension = original_filename.split(".")[-1] if "." in original_filename else ""
    local_filename = f"{file_id}.{extension}" if extension else f"{file_id}"
    
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    # Upload directly to MinIO
    MinIOService.upload_file(
        file_bytes=file_bytes,
        object_name=local_filename,
        content_type=file.content_type or "application/octet-stream"
    )
    
    # Generate presigned access URL
    storage_url = MinIOService.get_presigned_url(local_filename)
    
    # Create DB entry
    file_asset = FileAsset(
        id=file_id,
        filename=original_filename,
        file_type=extension.upper() or "BINARY",
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_url=storage_url,
        organization_id=membership.organization_id,
    )
    
    db.add(file_asset)
    db.commit()
    db.refresh(file_asset)
    return file_asset


@router.get("/", response_model=List[FileAssetResponse])
def list_files(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
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
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
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
        
    asset_name = file_asset.filename or ""
    extension = asset_name.split(".")[-1] if "." in asset_name else ""
    local_filename = f"{file_id}.{extension}" if extension else f"{file_id}"
    
    # Remove from MinIO storage
    MinIOService.delete_file(local_filename)
        
    db.delete(file_asset)
    db.commit()


@router.get("/{file_id}/download")
def download_file(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
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
    
    try:
        content_bytes = MinIOService.download_file_bytes(local_filename)
        return Response(
            content=content_bytes,
            media_type=file_asset.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file_asset.filename}"'}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File physical copy missing in MinIO: {e}"
        )
