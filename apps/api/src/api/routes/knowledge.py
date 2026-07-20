import os
import uuid
import shutil
import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func, text

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.knowledge import (
    KnowledgeCollection,
    KnowledgeFolder,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeProcessingJob,
    KnowledgeSearchHistory,
    KnowledgeSavedSearch,
    KnowledgePermission,
    DocumentChunk,
)
from api.schemas.knowledge import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
    DocumentVersionResponse,
    VersionCompareResponse,
    ProcessingJobResponse,
    KnowledgePermissionCreate,
    KnowledgePermissionResponse,
    KnowledgeSearchRequest,
    SearchResultItem,
    SearchHistoryResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    KnowledgeDashboardResponse,
    KnowledgeStatsResponse,
    TopCollectionStats,
    RecentUploadItem,
)
from api.services.document_processing import DocumentProcessingService
from api.services.rag_engine import RAGEngineService
from api.services.vector_store import VectorStore
from api.worker.celery_app import process_document_pipeline_task

router = APIRouter(prefix="/ai/knowledge", tags=["ai-knowledge"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

# ─────────────────────────────────────────────────────────────────────────────
# 1. COLLECTIONS CRUD ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    col_in: CollectionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    col = KnowledgeCollection(
        name=col_in.name,
        description=col_in.description,
        parent_id=col_in.parent_id,
        visibility=col_in.visibility,
        organization_id=membership.organization_id,
        created_by=str(current_user.id),
        updated_by=str(current_user.id),
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.get("/collections", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(KnowledgeCollection)
        .filter(
            KnowledgeCollection.organization_id == membership.organization_id,
            KnowledgeCollection.is_archived == False,
            KnowledgeCollection.deleted_at.is_(None),
        )
        .all()
    )


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    col = (
        db.query(KnowledgeCollection)
        .filter(
            KnowledgeCollection.id == collection_id,
            KnowledgeCollection.organization_id == membership.organization_id,
            KnowledgeCollection.deleted_at.is_(None),
        )
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    return col


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: uuid.UUID,
    col_in: CollectionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    col = (
        db.query(KnowledgeCollection)
        .filter(
            KnowledgeCollection.id == collection_id,
            KnowledgeCollection.organization_id == membership.organization_id,
            KnowledgeCollection.deleted_at.is_(None),
        )
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    for field, value in col_in.model_dump(exclude_unset=True).items():
        setattr(col, field, value)
        
    col.updated_by = str(current_user.id)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    col = (
        db.query(KnowledgeCollection)
        .filter(
            KnowledgeCollection.id == collection_id,
            KnowledgeCollection.organization_id == membership.organization_id,
            KnowledgeCollection.deleted_at.is_(None),
        )
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    col.deleted_at = datetime.datetime.utcnow()
    db.commit()


@router.post("/collections/{collection_id}/archive", response_model=CollectionResponse)
def archive_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    col = db.query(KnowledgeCollection).filter(KnowledgeCollection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    col.is_archived = not col.is_archived
    db.commit()
    db.refresh(col)
    return col


@router.post("/collections/{collection_id}/favorite", response_model=CollectionResponse)
def favorite_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    col = db.query(KnowledgeCollection).filter(KnowledgeCollection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    col.is_favorite = not col.is_favorite
    db.commit()
    db.refresh(col)
    return col


@router.post("/collections/{collection_id}/pin", response_model=CollectionResponse)
def pin_collection(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    col = db.query(KnowledgeCollection).filter(KnowledgeCollection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    col.is_pinned = not col.is_pinned
    db.commit()
    db.refresh(col)
    return col

# ─────────────────────────────────────────────────────────────────────────────
# 2. FOLDERS CRUD ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder_in: FolderCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    fld = KnowledgeFolder(
        name=folder_in.name,
        collection_id=folder_in.collection_id,
        parent_id=folder_in.parent_id,
        organization_id=membership.organization_id,
        created_by=str(current_user.id),
        updated_by=str(current_user.id),
    )
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


@router.get("/folders", response_model=List[FolderResponse])
def list_folders(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(KnowledgeFolder)
        .filter(
            KnowledgeFolder.organization_id == membership.organization_id,
            KnowledgeFolder.deleted_at.is_(None),
        )
        .all()
    )


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: uuid.UUID,
    fld_in: FolderUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    fld = (
        db.query(KnowledgeFolder)
        .filter(
            KnowledgeFolder.id == folder_id,
            KnowledgeFolder.organization_id == membership.organization_id,
            KnowledgeFolder.deleted_at.is_(None),
        )
        .first()
    )
    if not fld:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    for field, value in fld_in.model_dump(exclude_unset=True).items():
        setattr(fld, field, value)
        
    fld.updated_by = str(current_user.id)
    db.commit()
    db.refresh(fld)
    return fld


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    fld = (
        db.query(KnowledgeFolder)
        .filter(
            KnowledgeFolder.id == folder_id,
            KnowledgeFolder.organization_id == membership.organization_id,
            KnowledgeFolder.deleted_at.is_(None),
        )
        .first()
    )
    if not fld:
        raise HTTPException(status_code=404, detail="Folder not found")
    fld.deleted_at = datetime.datetime.utcnow()
    db.commit()

# ─────────────────────────────────────────────────────────────────────────────
# 3. DOCUMENTS CRUD & INGESTION PIPELINE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.organization_id == membership.organization_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        .all()
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == membership.organization_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.patch("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def update_document(
    document_id: uuid.UUID,
    doc_in: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    doc = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == membership.organization_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    for field, value in doc_in.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
        
    doc.updated_by = str(current_user.id)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    doc = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == membership.organization_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.deleted_at = datetime.datetime.utcnow()
    db.commit()


@router.post("/documents/{document_id}/archive", response_model=KnowledgeDocumentResponse)
def archive_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_archived = not doc.is_archived
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/documents/{document_id}/favorite", response_model=KnowledgeDocumentResponse)
def favorite_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_favorite = not doc.is_favorite
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/documents/{document_id}/pin", response_model=KnowledgeDocumentResponse)
def pin_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_pinned = not doc.is_pinned
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/documents/{document_id}/duplicate", response_model=KnowledgeDocumentResponse)
def duplicate_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    dup = KnowledgeDocument(
        title=f"Copy of {doc.title}",
        file_type=doc.file_type,
        file_size=doc.file_size,
        storage_url=doc.storage_url,
        organization_id=membership.organization_id,
        collection_id=doc.collection_id,
        folder_id=doc.folder_id,
        tags=doc.tags,
        category=doc.category,
        department=doc.department,
        owner_id=current_user.id,
        status="completed",
        progress=100.0,
    )
    db.add(dup)
    db.commit()
    db.refresh(dup)
    
    # Duplicate vector chunks
    for chunk in doc.chunks:
        dup_chunk = DocumentChunk(
            document_id=dup.id,
            organization_id=membership.organization_id,
            content=chunk.content,
            embedding=chunk.embedding,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
        )
        db.add(dup_chunk)
    db.commit()
    return dup


@router.post("/upload", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_and_index_document(
    file: UploadFile = File(...),
    collection_id: Optional[uuid.UUID] = Form(None),
    folder_id: Optional[uuid.UUID] = Form(None),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(100),
    strategy: str = Form("recursive"),
    embedding_model: str = Form("text-embedding-3-small"),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Standard upload and vector indexing route. Saves locally and triggers background task.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    doc_id = uuid.uuid4()
    ext = file.filename.split(".")[-1] if "." in file.filename else "TXT"
    local_filename = f"{doc_id}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)

    # 1. Create document
    doc = KnowledgeDocument(
        id=doc_id,
        title=file.filename,
        file_type=ext.upper(),
        file_size=file_size,
        storage_url=f"/api/v1/files/{doc_id}/download",
        organization_id=membership.organization_id,
        collection_id=collection_id,
        folder_id=folder_id,
        status="pending",
        progress=0.0,
        owner_id=current_user.id,
        created_by=str(current_user.id),
        updated_by=str(current_user.id),
    )
    db.add(doc)
    db.flush()

    # 2. Add version history
    ver = KnowledgeDocumentVersion(
        document_id=doc_id,
        version=1,
        title=file.filename,
        file_type=ext.upper(),
        file_size=file_size,
        storage_url=f"/api/v1/files/{doc_id}/download",
        change_summary="Initial upload",
    )
    db.add(ver)

    # 3. Add processing job
    job = KnowledgeProcessingJob(
        document_id=doc_id,
        organization_id=membership.organization_id,
        status="QUEUED",
        step="VIRUS_SCAN",
        progress=5.0,
    )
    db.add(job)
    db.commit()
    db.refresh(doc)

    # 4. Dispatch Celery Ingestion task
    task = process_document_pipeline_task.delay(
        document_id_str=str(doc_id),
        file_path=file_path,
        organization_id_str=str(membership.organization_id),
        user_id_str=str(current_user.id),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy,
        embedding_model=embedding_model,
    )
    
    # Save Celery Task ID in job record
    job.task_id = task.id
    db.commit()

    return doc


@router.post("/bulk-upload", status_code=status.HTTP_202_ACCEPTED)
def bulk_upload_documents(
    files: List[UploadFile] = File(...),
    collection_id: Optional[uuid.UUID] = Form(None),
    folder_id: Optional[uuid.UUID] = Form(None),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(100),
    strategy: str = Form("recursive"),
    embedding_model: str = Form("text-embedding-3-small"),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    jobs = []
    for file in files:
        doc = upload_and_index_document(
            file=file,
            collection_id=collection_id,
            folder_id=folder_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy,
            embedding_model=embedding_model,
            db=db,
            membership=membership,
            current_user=current_user,
        )
        jobs.append({"id": str(doc.id), "title": doc.title})
    return {"success": True, "queued_jobs": jobs}

# ─────────────────────────────────────────────────────────────────────────────
# 4. PROCESSING QUEUE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/queue", response_model=List[ProcessingJobResponse])
def list_processing_queue(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(KnowledgeProcessingJob)
        .filter(KnowledgeProcessingJob.organization_id == membership.organization_id)
        .order_by(desc(KnowledgeProcessingJob.created_at))
        .all()
    )


@router.post("/queue/{job_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_processing_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    job = (
        db.query(KnowledgeProcessingJob)
        .filter(
            KnowledgeProcessingJob.id == job_id,
            KnowledgeProcessingJob.organization_id == membership.organization_id,
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
        
    if job.task_id:
        from api.worker.celery_app import celery_app
        celery_app.control.revoke(job.task_id, terminate=True)
        
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == job.document_id).first()
    
    job.status = "CANCELLED"
    job.progress = 0.0
    if doc:
        doc.status = "cancelled"
        
    db.commit()
    return {"success": True, "message": "Ingestion job revoked successfully"}


@router.post("/queue/{job_id}/retry", status_code=status.HTTP_200_OK)
def retry_processing_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    job = (
        db.query(KnowledgeProcessingJob)
        .filter(
            KnowledgeProcessingJob.id == job_id,
            KnowledgeProcessingJob.organization_id == membership.organization_id,
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
        
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == job.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Source document not found")
        
    ext = doc.title.split(".")[-1] if "." in doc.title else "TXT"
    file_path = os.path.join(UPLOAD_DIR, f"{doc.id}.{ext}")
    
    # Dispatch again
    task = process_document_pipeline_task.delay(
        document_id_str=str(doc.id),
        file_path=file_path,
        organization_id_str=str(membership.organization_id),
        user_id_str=str(current_user.id),
    )
    
    job.status = "QUEUED"
    job.task_id = task.id
    job.progress = 5.0
    doc.status = "queued"
    db.commit()
    
    return {"success": True, "message": "Re-queued ingestion pipeline job."}

# ─────────────────────────────────────────────────────────────────────────────
# 5. VERSIONS HISTORIES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/documents/{document_id}/versions", response_model=List[DocumentVersionResponse])
def get_document_versions(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.organization_id == membership.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.versions


@router.post("/documents/{document_id}/versions/{version}/restore", response_model=KnowledgeDocumentResponse)
def restore_document_version(
    document_id: uuid.UUID,
    version: int,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.organization_id == membership.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    ver = db.query(KnowledgeDocumentVersion).filter(
        KnowledgeDocumentVersion.document_id == document_id,
        KnowledgeDocumentVersion.version == version
    ).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Re-apply text state content or references
    doc.title = ver.title
    doc.file_size = ver.file_size
    doc.storage_url = ver.storage_url
    
    # Save a new version increment
    new_version_num = doc.current_version + 1
    new_ver = KnowledgeDocumentVersion(
        document_id=document_id,
        version=new_version_num,
        title=ver.title,
        file_type=ver.file_type,
        file_size=ver.file_size,
        storage_url=ver.storage_url,
        content=ver.content,
        change_summary=f"Restored from version {version}",
    )
    db.add(new_ver)
    doc.current_version = new_version_num
    
    # Trigger parsing of content chunks again
    if ver.content:
        # Repopulate document chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        # For simplicity, split into single chunk or re-trigger pipeline. Here we re-slice in place.
        slices = DocumentProcessingService.split_text(ver.content, 500, 100, "recursive")
        gateway = AIGateway()
        for idx, s_text in enumerate(slices):
            vector = gateway.embeddings(db, s_text, membership.organization_id, membership.user_id)
            c = DocumentChunk(
                document_id=document_id,
                organization_id=membership.organization_id,
                content=s_text,
                embedding=vector,
                chunk_index=idx,
            )
            db.add(c)
            
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documents/{document_id}/versions/compare", response_model=VersionCompareResponse)
def compare_document_versions(
    document_id: uuid.UUID,
    version_a: int,
    version_b: int,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    ver_a = db.query(KnowledgeDocumentVersion).filter(
        KnowledgeDocumentVersion.document_id == document_id,
        KnowledgeDocumentVersion.version == version_a
    ).first()
    ver_b = db.query(KnowledgeDocumentVersion).filter(
        KnowledgeDocumentVersion.document_id == document_id,
        KnowledgeDocumentVersion.version == version_b
    ).first()
    if not ver_a or not ver_b:
        raise HTTPException(status_code=404, detail="Version instances not found")
        
    diff_chars = len(ver_b.content or "") - len(ver_a.content or "")
    summary = f"Content length changed by {diff_chars} characters. "
    if ver_a.title != ver_b.title:
        summary += f"Title renamed from '{ver_a.title}' to '{ver_b.title}'."
    else:
        summary += "Title remains identical."
        
    return VersionCompareResponse(
        version_a=version_a,
        version_b=version_b,
        title_changed=(ver_a.title != ver_b.title),
        size_diff_bytes=(ver_b.file_size - ver_a.file_size),
        diff_summary=summary,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 6. VECTOR SEARCH & RAG ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/search", response_model=List[SearchResultItem])
def search_vector_base(
    req: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    # 1. Embed query
    gateway = AIGateway()
    query_embedding = gateway.embeddings(db, req.query_text, membership.organization_id, current_user.id)
    
    # 2. Search Store
    filters_dict = req.filters.model_dump(exclude_unset=True) if req.filters else {}
    if req.search_type == "HYBRID":
        results = VectorStore.hybrid_search(db, req.query_text, query_embedding, membership.organization_id, filters_dict, req.limit * 2)
    elif req.search_type == "KEYWORD":
        results = VectorStore.keyword_search(db, req.query_text, membership.organization_id, filters_dict, req.limit * 2)
    else:
        results = VectorStore.semantic_search(db, query_embedding, membership.organization_id, filters_dict, req.limit * 2)
        
    # 3. MMR Rerank
    reranked = VectorStore.mmr_rerank(results, query_embedding, 0.6, req.limit)
    
    final_payload = []
    for sim, chunk in reranked:
        doc = chunk.document
        col_name = doc.collection.name if doc and doc.collection else None
        fld_name = doc.folder.name if doc and doc.folder else None
        
        final_payload.append(SearchResultItem(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=doc.title if doc else "Untitled",
            file_type=doc.file_type if doc else "TXT",
            content=chunk.content,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            similarity_score=sim,
            collection_name=col_name,
            folder_name=fld_name,
        ))
    return final_payload


@router.post("/rag", response_model=RAGQueryResponse)
def execute_rag_pipeline(
    req: RAGQueryRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    RAG endpoint resolving enterprise cognitive answers.
    """
    filters_dict = req.filters.model_dump(exclude_unset=True) if req.filters else {}
    res = RAGEngineService.execute_rag_flow(
        db=db,
        query_text=req.query_text,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        conversation_id=req.conversation_id,
        limit=req.limit,
        search_type=req.search_type,
        filters=filters_dict,
        collection_prompt=req.collection_prompt,
        organization_prompt=req.organization_prompt,
        system_prompt=req.system_prompt,
    )
    return res


@router.get("/search/history", response_model=List[SearchHistoryResponse])
def get_search_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    return (
        db.query(KnowledgeSearchHistory)
        .filter(
            KnowledgeSearchHistory.organization_id == membership.organization_id,
            KnowledgeSearchHistory.user_id == current_user.id
        )
        .order_by(desc(KnowledgeSearchHistory.created_at))
        .limit(30)
        .all()
    )


@router.post("/search/saved", response_model=SavedSearchResponse)
def save_search_query(
    req: SavedSearchCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    saved = KnowledgeSavedSearch(
        name=req.name,
        query_text=req.query_text,
        search_type=req.search_type,
        filters_applied=req.filters_applied,
        organization_id=membership.organization_id,
        user_id=current_user.id,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.get("/search/saved", response_model=List[SavedSearchResponse])
def list_saved_searches(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    return (
        db.query(KnowledgeSavedSearch)
        .filter(
            KnowledgeSavedSearch.organization_id == membership.organization_id,
            KnowledgeSavedSearch.user_id == current_user.id
        )
        .all()
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. DASHBOARD & STATISTICS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=KnowledgeDashboardResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    org_id = membership.organization_id
    
    doc_count = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == org_id, KnowledgeDocument.deleted_at.is_(None)).count()
    col_count = db.query(KnowledgeCollection).filter(KnowledgeCollection.organization_id == org_id, KnowledgeCollection.deleted_at.is_(None)).count()
    folder_count = db.query(KnowledgeFolder).filter(KnowledgeFolder.organization_id == org_id, KnowledgeFolder.deleted_at.is_(None)).count()
    
    total_bytes = db.query(func.sum(KnowledgeDocument.file_size)).filter(KnowledgeDocument.organization_id == org_id, KnowledgeDocument.deleted_at.is_(None)).scalar() or 0
    completed_count = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == org_id, KnowledgeDocument.status == "completed", KnowledgeDocument.deleted_at.is_(None)).count()
    indexed_ratio = (completed_count / doc_count * 100.0) if doc_count > 0 else 100.0

    stats = KnowledgeStatsResponse(
        document_count=doc_count,
        collection_count=col_count,
        folder_count=folder_count,
        total_storage_bytes=total_bytes,
        storage_allocated_kb=round(total_bytes / 1024.0, 2),
        indexed_ratio=round(indexed_ratio, 2)
    )

    # Top collections stats
    collections = db.query(KnowledgeCollection).filter(KnowledgeCollection.organization_id == org_id, KnowledgeCollection.deleted_at.is_(None)).limit(5).all()
    top_collections = []
    for col in collections:
        doc_c = len([d for d in col.documents if d.deleted_at is None])
        queries_c = db.query(KnowledgeSearchHistory).filter(
            KnowledgeSearchHistory.organization_id == org_id,
            text("filters_applied->>'collection_id' = :cid")
        ).params(cid=str(col.id)).count()
        top_collections.append(TopCollectionStats(
            id=col.id,
            name=col.name,
            document_count=doc_c,
            queries_count=queries_c
        ))

    # Recent uploads
    recent_docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == org_id,
        KnowledgeDocument.deleted_at.is_(None)
    ).order_by(desc(KnowledgeDocument.created_at)).limit(5).all()
    
    recent_uploads = [
        RecentUploadItem(
            id=d.id,
            title=d.title,
            file_type=d.file_type,
            file_size=d.file_size or 0,
            created_at=d.created_at
        ) for d in recent_docs
    ]

    # Growth history
    growth_history = [
        {"date": "Jul 11", "storage_kb": round((total_bytes * 0.7) / 1024.0, 2), "queries": 34},
        {"date": "Jul 12", "storage_kb": round((total_bytes * 0.8) / 1024.0, 2), "queries": 45},
        {"date": "Jul 13", "storage_kb": round((total_bytes * 0.9) / 1024.0, 2), "queries": 50},
        {"date": "Jul 14", "storage_kb": round(total_bytes / 1024.0, 2), "queries": 62},
    ]

    return KnowledgeDashboardResponse(
        stats=stats,
        top_collections=top_collections,
        recent_uploads=recent_uploads,
        storage_growth_history=growth_history
    )


@router.post("/", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_legacy(
    doc_in: Any = Body(...), # Use generic to avoid import compile order issues, parsed dynamically
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    # Resolve import dynamically
    from api.schemas.ai import KnowledgeUploadRequest
    from pydantic import ValidationError
    
    try:
        # Pydantic validation
        if isinstance(doc_in, dict):
            doc_in = KnowledgeUploadRequest(**doc_in)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    doc_id = uuid.uuid4()
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(doc_in.content)
        
    doc = KnowledgeDocument(
        id=doc_id,
        title=doc_in.title,
        file_type=doc_in.file_type.upper(),
        file_size=len(doc_in.content),
        storage_url=f"/api/v1/files/{doc_id}/download",
        organization_id=membership.organization_id,
        status="pending",
        progress=0.0,
        owner_id=current_user.id,
    )
    db.add(doc)
    db.flush()

    # Add version history
    ver = KnowledgeDocumentVersion(
        document_id=doc_id,
        version=1,
        title=doc_in.title,
        file_type=doc_in.file_type.upper(),
        file_size=len(doc_in.content),
        storage_url=f"/api/v1/files/{doc_id}/download",
        change_summary="Initial upload",
        content=doc_in.content,
    )
    db.add(ver)

    # Add job
    job = KnowledgeProcessingJob(
        document_id=doc_id,
        organization_id=membership.organization_id,
        status="QUEUED",
        step="VIRUS_SCAN",
        progress=5.0,
    )
    db.add(job)
    db.commit()
    db.refresh(doc)
    
    # Run synchronously to preserve legacy expected behavior
    DocumentProcessingService.run_ingestion_pipeline(
        db=db,
        document_id=doc_id,
        file_path=file_path,
        organization_id=membership.organization_id,
        user_id=current_user.id,
    )
    db.refresh(doc)
    return doc


@router.post("/query", response_model=Any)
def query_similar_chunks_legacy(
    query_in: Any = Body(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    from api.schemas.ai import QuerySimilarChunksRequest
    from api.ai.gateway.coordinator import AIGateway
    
    # Simple parse
    if isinstance(query_in, dict):
        query_in = QuerySimilarChunksRequest(**query_in)
        
    gateway = AIGateway()
    query_embedding = gateway.embeddings(db, query_in.query_text, membership.organization_id, current_user.id)
    results = VectorStore.semantic_search(db, query_embedding, membership.organization_id, limit=query_in.limit or 3)
    
    return [
        {
            "id": chunk.id,
            "content": chunk.content,
            "document_id": chunk.document_id,
            "organization_id": chunk.organization_id,
        }
        for sim, chunk in results
    ]


@router.post("/documents/{document_id}/rebuild", response_model=KnowledgeDocumentResponse)
def rebuild_document_embeddings(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.organization_id == membership.organization_id,
        KnowledgeDocument.deleted_at.is_(None)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    ext = doc.file_type.lower()
    file_path = os.path.join(UPLOAD_DIR, f"{doc.id}.{ext}")
    
    # If the raw local file is missing, re-generate it from the latest version's content
    if not os.path.exists(file_path):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Fetch latest version
        latest_ver = db.query(KnowledgeDocumentVersion).filter(
            KnowledgeDocumentVersion.document_id == document_id
        ).order_by(desc(KnowledgeDocumentVersion.version)).first()
        
        content = latest_ver.content if latest_ver else ""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    # Reset status
    doc.status = "pending"
    doc.progress = 0.0
    
    # Create or update processing job
    job = db.query(KnowledgeProcessingJob).filter(
        KnowledgeProcessingJob.document_id == document_id
    ).first()
    if not job:
        job = KnowledgeProcessingJob(
            document_id=document_id,
            organization_id=membership.organization_id,
        )
        db.add(job)
        
    job.status = "QUEUED"
    job.step = "VIRUS_SCAN"
    job.progress = 5.0
    db.commit()
    
    task = process_document_pipeline_task.delay(
        document_id_str=str(document_id),
        file_path=file_path,
        organization_id_str=str(membership.organization_id),
        user_id_str=str(current_user.id),
        chunk_size=500,
        chunk_overlap=100,
        strategy="recursive",
        embedding_model="text-embedding-3-small",
    )
    job.task_id = task.id
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/collections/{collection_id}/rebuild", response_model=Dict[str, Any])
def rebuild_collection_embeddings(
    collection_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    col = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id,
        KnowledgeCollection.organization_id == membership.organization_id,
        KnowledgeCollection.deleted_at.is_(None)
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.collection_id == collection_id,
        KnowledgeDocument.deleted_at.is_(None)
    ).all()
    
    triggered_count = 0
    for doc in docs:
        ext = doc.file_type.lower()
        file_path = os.path.join(UPLOAD_DIR, f"{doc.id}.{ext}")
        if not os.path.exists(file_path):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            latest_ver = db.query(KnowledgeDocumentVersion).filter(
                KnowledgeDocumentVersion.document_id == doc.id
            ).order_by(desc(KnowledgeDocumentVersion.version)).first()
            content = latest_ver.content if latest_ver else ""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        doc.status = "pending"
        doc.progress = 0.0
        
        job = db.query(KnowledgeProcessingJob).filter(
            KnowledgeProcessingJob.document_id == doc.id
        ).first()
        if not job:
            job = KnowledgeProcessingJob(
                document_id=doc.id,
                organization_id=membership.organization_id,
            )
            db.add(job)
            
        job.status = "QUEUED"
        job.step = "VIRUS_SCAN"
        job.progress = 5.0
        db.commit()
        
        task = process_document_pipeline_task.delay(
            document_id_str=str(doc.id),
            file_path=file_path,
            organization_id_str=str(membership.organization_id),
            user_id_str=str(current_user.id),
            chunk_size=500,
            chunk_overlap=100,
            strategy="recursive",
            embedding_model="text-embedding-3-small",
        )
        job.task_id = task.id
        db.commit()
        triggered_count += 1
        
    return {"message": f"Successfully triggered rebuilding for {triggered_count} documents in collection."}


@router.get("/search/autocomplete", response_model=List[str])
def search_autocomplete_suggestions(
    q: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if not q or len(q) < 2:
        return []
    # Match query term against document titles
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == membership.organization_id,
        KnowledgeDocument.title.ilike(f"%{q}%"),
        KnowledgeDocument.deleted_at.is_(None)
    ).limit(8).all()
    
    suggestions = [doc.title for doc in docs]
    
    # Also search saved searches
    saved = db.query(KnowledgeSavedSearch).filter(
        KnowledgeSavedSearch.organization_id == membership.organization_id,
        KnowledgeSavedSearch.name.ilike(f"%{q}%")
    ).limit(5).all()
    suggestions.extend([s.name for s in saved])
    
    # Return unique values
    return list(set(suggestions))
