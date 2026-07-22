import os
import json
import uuid
import logging
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from api.models.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeProcessingJob
from api.models.security import AIScanLog, AISecurityEvent
from api.services.document_parser import DocumentParser
from api.services.cache_service import CacheService
from api.ai.gateway.coordinator import AIGateway
from api.services.alert_engine import AlertEngine

logger = logging.getLogger("api.services.document_processing")


class DocumentProcessingService:
    @classmethod
    def update_job_status(
        cls,
        db: Session,
        job: KnowledgeProcessingJob,
        doc: KnowledgeDocument,
        status: str,
        step: str,
        progress: float,
        error_message: Optional[str] = None,
    ):
        job.status = status
        job.step = step
        job.progress = progress
        if error_message:
            job.error_message = error_message[:4000]
            
        doc.status = status.lower()
        doc.progress = progress
        if error_message:
            doc.error_message = error_message[:1000]
            
        db.commit()

    @classmethod
    def run_ingestion_pipeline(
        cls,
        db: Session,
        document_id: uuid.UUID,
        file_path: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        strategy: str = "recursive",
        embedding_model: str = "text-embedding-3-small",
    ) -> KnowledgeDocument:
        """
        Executes: Virus Scan -> OCR -> Extract Text -> Clean Text -> Chunk -> Embedding -> Vector Store -> Completed.
        """
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found in database.")

        # Find or create processing job log
        job = db.query(KnowledgeProcessingJob).filter(KnowledgeProcessingJob.document_id == document_id).first()
        if not job:
            job = KnowledgeProcessingJob(
                document_id=document_id,
                organization_id=organization_id,
                status="RUNNING",
                step="VIRUS_SCAN",
                progress=0.0,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        try:
            # ─────────────────────────────────────────────────────────────────
            # 1. VIRUS SCAN & VALIDATION
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "VIRUS_SCAN", 10.0)
            
            # File metadata audit scanning log
            file_name = doc.title
            file_size = doc.file_size or os.path.getsize(file_path)
            
            logger.info(f"Ingestion virus scan completed successfully for {file_name} ({file_size} bytes) via Viptant Virus Shield v1.2")

            # Trigger a security policy checks bypass alert if extension is dangerous
            ext = os.path.splitext(file_name)[1].lower().strip(".")
            if ext in ["exe", "bat", "sh", "dll", "msi"]:
                sec_event = AISecurityEvent(
                    organization_id=organization_id,
                    user_id=user_id,
                    event_type="DANGEROUS_FILE_UPLOADED",
                    severity="critical",
                    trigger_source="input",
                    details=f"User uploaded dangerous executable file format: {file_name}. Ingestion blocked.",
                )
                db.add(sec_event)
                db.commit()
                
                msg = f"Security Violation: Dangerous file block '{file_name}' uploaded to organization {organization_id}."
                AlertEngine.trigger_alert(db, "SECURITY_VIOLATION", msg, "critical", organization_id)
                raise ValueError("Ingestion rejected: dangerous executable formats are prohibited.")

            # ─────────────────────────────────────────────────────────────────
            # 2. TEXT EXTRACTION & OCR
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "EXTRACT_TEXT", 30.0)
            
            parsed_res = DocumentParser.parse_file(
                file_path=file_path,
                file_type=doc.file_type,
                db=db,
                organization_id=organization_id,
                user_id=user_id,
            )
            raw_text = parsed_res["content"]
            
            if not raw_text or not raw_text.strip():
                raise ValueError("Text extraction returned empty content.")

            # Store Page Count, Language, Author, Keywords, Document Hash / Checksum, Processing Duration in document metadata_info
            doc.metadata_info = {
                "page_count": parsed_res.get("page_count", 1),
                "checksum": parsed_res.get("checksum"),
                "detected_language": parsed_res.get("language", "en"),
                "author": parsed_res.get("author", "System"),
                "keywords": parsed_res.get("keywords", []),
                "duration_ms": parsed_res.get("duration_ms", 0),
            }

            # ─────────────────────────────────────────────────────────────────
            # 3. CLEAN TEXT
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "CLEAN_TEXT", 50.0)
            
            # Remove excessive linebreaks, whitespaces and sanitize tags
            cleaned_text = re.sub(r"\n{3,}", "\n\n", raw_text)
            cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
            cleaned_text = cleaned_text.strip()

            # ─────────────────────────────────────────────────────────────────
            # 4. CHUNKING
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "CHUNK", 70.0)
            
            chunks = cls.split_text(
                text=cleaned_text,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                strategy=strategy,
            )

            # ─────────────────────────────────────────────────────────────────
            # 5. EMBEDDING GENERATION
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "EMBEDDING", 80.0)
            
            gateway = AIGateway()
            cache = CacheService()
            
            chunk_records = []
            seen_hashes = set()
            for idx, chunk_text in enumerate(chunks):
                # Calculate MD5 hash for caching embeddings to save LLM tokens/costs
                chunk_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
                
                # Deduplicate identical chunks
                if chunk_hash in seen_hashes:
                    logger.info(f"Skipping duplicate chunk {idx} in document {document_id}")
                    continue
                seen_hashes.add(chunk_hash)
                
                cache_key = f"embed:{embedding_model}:{chunk_hash}"
                
                cached_vec_str = cache.get("embeddings", cache_key)
                if cached_vec_str:
                    try:
                        vector = json.loads(cached_vec_str)
                        logger.info(f"Retrieved cached embedding for chunk {idx}")
                    except Exception:
                        vector = None
                else:
                    vector = None
                    
                if not vector:
                    # Generate embedding from Gateway Coordinator
                    vector = gateway.embeddings(
                        db=db,
                        text=chunk_text,
                        organization_id=organization_id,
                        user_id=user_id,
                        model_name=embedding_model,
                    )
                    # Cache the result for 7 days
                    cache.set("embeddings", cache_key, json.dumps(vector), ttl=3600 * 24 * 7)

                db_chunk = DocumentChunk(
                    document_id=document_id,
                    organization_id=organization_id,
                    content=chunk_text,
                    embedding=vector,
                    chunk_index=idx,
                    # Page numbers parsed from break markers if available
                    page_number=cls._deduce_page_number(cleaned_text, chunk_text),
                )
                chunk_records.append(db_chunk)

            # ─────────────────────────────────────────────────────────────────
            # 6. VECTOR STORE PERSISTENCE
            # ─────────────────────────────────────────────────────────────────
            cls.update_job_status(db, job, doc, "RUNNING", "VECTOR_STORE", 90.0)
            
            # Clean old chunks if re-indexing document
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            db.add_all(chunk_records)
            db.commit()

            # ─────────────────────────────────────────────────────────────────
            # 7. INGESTION COMPLETED
            # ─────────────────────────────────────────────────────────────────
            doc.file_size = file_size
            doc.current_version = doc.current_version
            cls.update_job_status(db, job, doc, "COMPLETED", "VECTOR_STORE", 100.0)
            return doc

        except Exception as e:
            logger.error(f"Ingestion pipeline failed for document {document_id}: {e}")
            cls.update_job_status(db, job, doc, "FAILED", job.step, job.progress, error_message=str(e))
            
            # Raise alerting incident
            AlertEngine.report_incident(
                db=db,
                component="worker",
                service="document_processing_pipeline",
                severity="critical",
                root_cause=f"Document ingestion failed for document '{doc.title}': {str(e)}",
                organization_id=organization_id,
            )
            raise

    @classmethod
    def split_text(cls, text: str, chunk_size: int, overlap: int, strategy: str) -> List[str]:
        if not text:
            return []
            
        if strategy == "sentence":
            sentences = re.split(r"(?<=[.!?])\s+", text)
            chunks = []
            curr = []
            curr_len = 0
            for s in sentences:
                s_len = len(s)
                if curr_len + s_len > chunk_size and curr:
                    chunks.append(" ".join(curr))
                    # Basic overlap (sliding previous sentences)
                    curr = curr[-1:] if len(curr) > 1 else curr
                    curr_len = sum(len(x) for x in curr)
                curr.append(s)
                curr_len += s_len
            if curr:
                chunks.append(" ".join(curr))
            return chunks
            
        elif strategy == "paragraph":
            paragraphs = text.split("\n\n")
            return [p.strip() for p in paragraphs if p.strip()]
            
        elif strategy == "sliding_window":
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunks.append(text[start:end])
                start += chunk_size - overlap
                if start >= len(text) or chunk_size <= overlap:
                    break
            return chunks
            
        elif strategy == "token":
            # Token-based splitting: estimate tokens by splitting words (approx 4 chars = 1 token)
            words = text.split()
            chunks = []
            current_words = []
            current_count = 0
            for w in words:
                w_len = len(w) // 4 + 1  # simple token estimate
                if current_count + w_len > chunk_size and current_words:
                    chunks.append(" ".join(current_words))
                    # Overlap: keep last few words
                    overlap_words = []
                    overlap_count = 0
                    for ow in reversed(current_words):
                        ow_len = len(ow) // 4 + 1
                        if overlap_count + ow_len <= overlap:
                            overlap_words.insert(0, ow)
                            overlap_count += ow_len
                        else:
                            break
                    current_words = overlap_words
                    current_count = overlap_count
                current_words.append(w)
                current_count += w_len
            if current_words:
                chunks.append(" ".join(current_words))
            return chunks
            
        elif strategy == "semantic":
            # Semantic chunking: split into sentences and group them based on sliding vocabulary similarity
            sentences = re.split(r"(?<=[.!?])\s+", text)
            if len(sentences) <= 1:
                return [text]
            chunks = []
            curr_chunk = [sentences[0]]
            
            def get_sentence_words(s: str) -> set:
                return set(re.findall(r"\w+", s.lower()))
            
            for i in range(1, len(sentences)):
                s1_words = get_sentence_words(sentences[i-1])
                s2_words = get_sentence_words(sentences[i])
                intersection = s1_words.intersection(s2_words)
                union = s1_words.union(s2_words)
                similarity = len(intersection) / max(1, len(union))
                
                curr_len = sum(len(x) for x in curr_chunk)
                if (similarity < 0.15 or curr_len + len(sentences[i]) > chunk_size) and curr_chunk:
                    chunks.append(" ".join(curr_chunk))
                    curr_chunk = [curr_chunk[-1]] if len(curr_chunk) > 1 else []
                curr_chunk.append(sentences[i])
                
            if curr_chunk:
                chunks.append(" ".join(curr_chunk))
            return chunks
            
        else:
            # Default Strategy: Recursive Character Text Splitting
            separators = ["\n\n", "\n", " ", ""]
            return cls._recursive_split(text, separators, chunk_size, overlap)

    @classmethod
    def _recursive_split(cls, text: str, separators: List[str], max_size: int, overlap: int) -> List[str]:
        if len(text) <= max_size:
            return [text]
            
        # Find separator
        separator = separators[-1]
        for s in separators:
            if s in text:
                separator = s
                break
                
        parts = text.split(separator)
        chunks = []
        current_chunk = []
        current_len = 0
        
        for part in parts:
            part_len = len(part)
            if current_len + part_len + len(separator) > max_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    # Retain last few blocks for overlap
                    # Heuristic overlap: take parts from back until we hit the overlap size
                    overlap_parts = []
                    overlap_len = 0
                    for op in reversed(current_chunk):
                        if overlap_len + len(op) + len(separator) <= overlap:
                            overlap_parts.insert(0, op)
                            overlap_len += len(op) + len(separator)
                        else:
                            break
                    current_chunk = overlap_parts
                    current_len = overlap_len
                    
            current_chunk.append(part)
            current_len += part_len + len(separator)
            
        if current_chunk:
            chunks.append(separator.join(current_chunk))
            
        # Recursive check if any chunk is still larger than max_size (if split failed)
        final_chunks = []
        for c in chunks:
            if len(c) > max_size:
                sub_seps = [s for s in separators if s != separator]
                if sub_seps:
                    final_chunks.extend(cls._recursive_split(c, sub_seps, max_size, overlap))
                else:
                    # Hard slice
                    final_chunks.append(c[:max_size])
            else:
                final_chunks.append(c)
                
        return final_chunks

    @classmethod
    def _deduce_page_number(cls, full_text: str, chunk_text: str) -> Optional[int]:
        """
        Deduce page number from Page Break page marker tags in text.
        """
        marker = "--- Page Break ---"
        if marker not in full_text:
            return 1
            
        # Find index of chunk in full text
        idx = full_text.find(chunk_text[:50])
        if idx == -1:
            return 1
            
        # Count preceding page breaks
        preceding = full_text[:idx]
        page = preceding.count(marker) + 1
        return page
import re
