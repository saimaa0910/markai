import uuid
import time
import re
import difflib
import json
import csv
import io
from datetime import datetime
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc

from api.models.prompt import (
    Prompt, PromptCollection, PromptFolder, PromptComment,
    PromptTestCase, PromptEvaluation, PromptExecution
)
from api.models.user import User
from api.models.organization import Organization
from api.schemas.ai import PromptCreate, PromptUpdate
from api.ai.gateway.coordinator import AIGateway
from api.services.knowledge import KnowledgeService

try:
    import yaml
except ImportError:
    yaml = None


class PromptService:
    # ─────────────────────────────────────────────────────────────────────────
    # Collections & Folders Management
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def create_collection(
        db: Session,
        name: str,
        description: Optional[str],
        organization_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
        visibility: str = "ORGANIZATION"
    ) -> PromptCollection:
        collection = PromptCollection(
            name=name,
            description=description,
            organization_id=organization_id,
            parent_id=parent_id,
            visibility=visibility
        )
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def list_collections(db: Session, organization_id: uuid.UUID) -> List[PromptCollection]:
        return list(
            db.scalars(
                select(PromptCollection)
                .where(
                    and_(
                        PromptCollection.organization_id == organization_id,
                        PromptCollection.is_archived == False
                    )
                )
            ).all()
        )

    @staticmethod
    def create_folder(
        db: Session,
        name: str,
        collection_id: uuid.UUID,
        organization_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None
    ) -> PromptFolder:
        folder = PromptFolder(
            name=name,
            collection_id=collection_id,
            organization_id=organization_id,
            parent_id=parent_id
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def list_folders(
        db: Session,
        organization_id: uuid.UUID,
        collection_id: Optional[uuid.UUID] = None
    ) -> List[PromptFolder]:
        query = select(PromptFolder).where(PromptFolder.organization_id == organization_id)
        if collection_id:
            query = query.where(PromptFolder.collection_id == collection_id)
        return list(db.scalars(query).all())

    # ─────────────────────────────────────────────────────────────────────────
    # Prompt Family Management (CRUD + Custom Extensions)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def create_prompt_version(
        db: Session, prompt_in: PromptCreate, organization_id: uuid.UUID
    ) -> Prompt:
        """
        Create the first version (v1) of a prompt.
        If a prompt with this name already exists, raise an exception.
        """
        existing = db.scalars(
            select(Prompt).where(
                and_(
                    Prompt.name == prompt_in.name,
                    Prompt.organization_id == organization_id,
                )
            )
        ).first()
        if existing:
            raise ValueError(
                "Prompt template with this name already exists in your library. Use the update endpoint to create a new version."
            )

        prompt = Prompt(
            name=prompt_in.name,
            content=prompt_in.content,
            version=1,
            category=prompt_in.category,
            tags=prompt_in.tags,
            is_shared=prompt_in.is_shared if prompt_in.is_shared is not None else True,
            organization_id=organization_id,
            status=getattr(prompt_in, "status", "approved")
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def update_prompt_version(
        db: Session, name: str, prompt_in: PromptUpdate, organization_id: uuid.UUID
    ) -> Prompt:
        """
        Increment the prompt version and insert a new historical database record.
        """
        latest = db.scalars(
            select(Prompt)
            .where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
            .order_by(Prompt.version.desc())
        ).first()

        if not latest:
            raise ValueError(f"Prompt template named '{name}' not found.")

        # Determine properties falling back to latest version
        new_content = prompt_in.content if prompt_in.content is not None else latest.content
        new_category = prompt_in.category if prompt_in.category is not None else latest.category
        new_tags = prompt_in.tags if prompt_in.tags is not None else latest.tags
        new_is_shared = prompt_in.is_shared if prompt_in.is_shared is not None else latest.is_shared
        new_status = getattr(prompt_in, "status", latest.status)
        new_change_log = getattr(prompt_in, "change_log", None)

        new_prompt = Prompt(
            name=name,
            content=new_content,
            version=latest.version + 1,
            category=new_category,
            tags=new_tags,
            is_shared=new_is_shared,
            organization_id=organization_id,
            status=new_status,
            change_log=new_change_log,
            folder_id=latest.folder_id,
            collection_id=latest.collection_id,
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        return new_prompt

    @staticmethod
    def get_latest_prompt(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> Optional[Prompt]:
        """
        Retrieve the highest version of a prompt template.
        """
        return db.scalars(
            select(Prompt)
            .where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
            .order_by(Prompt.version.desc())
        ).first()

    @staticmethod
    def get_prompt_history(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> List[Prompt]:
        """
        Retrieve all version records of a prompt template.
        """
        return list(
            db.scalars(
                select(Prompt)
                .where(
                    and_(
                        Prompt.name == name,
                        Prompt.organization_id == organization_id,
                    )
                )
                .order_by(Prompt.version.desc())
            ).all()
        )

    @staticmethod
    def list_latest_prompts(
        db: Session, organization_id: uuid.UUID
    ) -> List[Prompt]:
        """
        Return the highest version of each prompt template within an organization.
        """
        subq = (
            select(Prompt.name, func.max(Prompt.version).label("max_version"))
            .where(Prompt.organization_id == organization_id)
            .group_by(Prompt.name)
            .subquery()
        )

        query = select(Prompt).join(
            subq,
            and_(
                Prompt.name == subq.c.name,
                Prompt.version == subq.c.max_version,
                Prompt.organization_id == organization_id,
            ),
        )

        return list(db.scalars(query).all())

    @staticmethod
    def delete_prompt_family(
        db: Session, name: str, organization_id: uuid.UUID
    ) -> None:
        """
        Delete all versions of a prompt family.
        """
        prompts = db.scalars(
            select(Prompt).where(
                and_(
                    Prompt.name == name,
                    Prompt.organization_id == organization_id,
                )
            )
        ).all()

        for p in prompts:
            db.delete(p)
        db.commit()

    @staticmethod
    def rollback_prompt_version(
        db: Session, name: str, rollback_version: int, organization_id: uuid.UUID
    ) -> Prompt:
        """
        Copy instructions from a historic version and save as the latest version.
        """
        target = db.scalars(
            select(Prompt).where(
                and_(
                    Prompt.name == name,
                    Prompt.version == rollback_version,
                    Prompt.organization_id == organization_id
                )
            )
        ).first()

        if not target:
            raise ValueError(f"Version {rollback_version} of prompt '{name}' not found.")

        latest = db.scalars(
            select(Prompt)
            .where(and_(Prompt.name == name, Prompt.organization_id == organization_id))
            .order_by(Prompt.version.desc())
        ).first()

        new_prompt = Prompt(
            name=name,
            content=target.content,
            version=latest.version + 1,
            category=target.category,
            tags=target.tags,
            is_shared=target.is_shared,
            organization_id=organization_id,
            status=target.status,
            change_log=f"Rollback to version v{rollback_version}",
            folder_id=target.folder_id,
            collection_id=target.collection_id
        )
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        return new_prompt

    @staticmethod
    def get_unified_diff(
        db: Session, name: str, version_a: int, version_b: int, organization_id: uuid.UUID
    ) -> str:
        prompt_a = db.scalars(
            select(Prompt).where(and_(Prompt.name == name, Prompt.version == version_a, Prompt.organization_id == organization_id))
        ).first()
        prompt_b = db.scalars(
            select(Prompt).where(and_(Prompt.name == name, Prompt.version == version_b, Prompt.organization_id == organization_id))
        ).first()

        if not prompt_a or not prompt_b:
            raise ValueError(f"Could not load versions {version_a} and {version_b} of prompt '{name}'.")

        diff = difflib.unified_diff(
            prompt_a.content.splitlines(),
            prompt_b.content.splitlines(),
            fromfile=f"v{version_a}",
            tofile=f"v{version_b}",
            lineterm=""
        )
        return "\n".join(diff)

    @staticmethod
    def duplicate_prompt(
        db: Session, name: str, new_name: str, organization_id: uuid.UUID
    ) -> Prompt:
        latest = PromptService.get_latest_prompt(db, name, organization_id)
        if not latest:
            raise ValueError(f"Prompt '{name}' not found.")
            
        dup = Prompt(
            name=new_name,
            content=latest.content,
            version=1,
            category=latest.category,
            tags=latest.tags,
            is_shared=latest.is_shared,
            organization_id=organization_id,
            folder_id=latest.folder_id,
            collection_id=latest.collection_id
        )
        db.add(dup)
        db.commit()
        db.refresh(dup)
        return dup

    @staticmethod
    def toggle_favorite(db: Session, name: str, organization_id: uuid.UUID) -> Prompt:
        prompts = db.scalars(
            select(Prompt).where(and_(Prompt.name == name, Prompt.organization_id == organization_id))
        ).all()
        
        # Toggle all version records to maintain visual consistency
        next_val = not prompts[0].is_favorite if prompts else True
        for p in prompts:
            p.is_favorite = next_val
        db.commit()
        return prompts[0] if prompts else None

    @staticmethod
    def toggle_pin(db: Session, name: str, organization_id: uuid.UUID) -> Prompt:
        prompts = db.scalars(
            select(Prompt).where(and_(Prompt.name == name, Prompt.organization_id == organization_id))
        ).all()
        next_val = not prompts[0].is_pinned if prompts else True
        for p in prompts:
            p.is_pinned = next_val
        db.commit()
        return prompts[0] if prompts else None

    @staticmethod
    def archive_prompt(db: Session, name: str, organization_id: uuid.UUID) -> Prompt:
        prompts = db.scalars(
            select(Prompt).where(and_(Prompt.name == name, Prompt.organization_id == organization_id))
        ).all()
        for p in prompts:
            p.is_archived = True
        db.commit()
        return prompts[0] if prompts else None


class VariableEngine:
    @staticmethod
    def extract_variables(content: str) -> List[str]:
        # Match standard {{variable_name}} structure
        matches = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", content)
        return list(set(matches))

    @staticmethod
    def render(
        db: Session,
        content: str,
        variables: dict,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        rag_context: Optional[str] = None
    ) -> str:
        # Match variables, injecting custom bindings or falling back to environment system values
        system_vars = {}
        
        # Built-in context dates
        system_vars["current_date"] = datetime.utcnow().strftime("%Y-%m-%d")
        system_vars["current_time"] = datetime.utcnow().strftime("%H:%M:%S")

        # Current User
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                system_vars["current_user"] = user.full_name or user.email
                
        # Organization
        if organization_id:
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if org:
                system_vars["organization"] = org.name

        # Knowledge Context
        if rag_context:
            system_vars["knowledge"] = rag_context

        # Combine
        combined = {**system_vars, **variables}

        rendered = content
        for k, v in combined.items():
            rendered = re.sub(r"\{\{\s*" + re.escape(k) + r"\s*\}\}", str(v), rendered)

        return rendered


class ExecutionService:
    @staticmethod
    def execute(
        db: Session,
        name: str,
        variables: dict,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        version: Optional[int] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        rag_enabled: bool = False,
        temperature: float = 0.7,
    ) -> dict:
        # 1. Fetch prompt family version
        query = select(Prompt).where(and_(Prompt.name == name, Prompt.organization_id == organization_id))
        if version:
            query = query.where(Prompt.version == version)
        else:
            query = query.order_by(Prompt.version.desc())
            
        prompt = db.scalars(query).first()
        if not prompt:
            raise ValueError(f"Prompt template named '{name}' not found.")

        # 2. Extract RAG base context
        rag_context = ""
        if rag_enabled:
            # Query similar chunks using variable criteria
            query_target = variables.get("query") or variables.get("question") or prompt.content[:100]
            chunks = KnowledgeService.query_similar_chunks(
                db=db,
                query_text=query_target,
                organization_id=organization_id,
                user_id=user_id,
                limit=3
            )
            if chunks:
                rag_context = "\n".join(c.content for c in chunks)

        # 3. Inject variables and compile prompt content
        rendered = VariableEngine.render(
            db=db,
            content=prompt.content,
            variables=variables,
            user_id=user_id,
            organization_id=organization_id,
            rag_context=rag_context
        )

        # 4. Token limit checks
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            estimated_tokens = len(enc.encode(rendered))
        except Exception:
            estimated_tokens = len(rendered) // 4

        # 5. Coordinate messages and call AIGateway
        messages = []
        final_sys = system_prompt or "You are a helpful AI assistant."
        messages.append({"role": "system", "content": final_sys})
        messages.append({"role": "user", "content": rendered})

        gateway = AIGateway()
        start_time = time.perf_counter()
        
        gateway_res = gateway.chat(
            db=db,
            messages=messages,
            organization_id=organization_id,
            user_id=user_id,
            temperature=temperature,
            model_name=model_name
        )
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 6. Parse metrics and return response
        provider = gateway_res.get("provider", "unknown")
        resolved_model = gateway_res.get("model", model_name or "unknown")
        prompt_tokens = gateway_res.get("prompt_tokens", 0)
        completion_tokens = gateway_res.get("completion_tokens", 0)
        cost_usd = gateway_res.get("cost_usd", 0.0)
        output = gateway_res.get("content", "")

        # 7. Audit log write-in
        exec_log = PromptExecution(
            prompt_id=prompt.id,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            provider=provider,
            model=resolved_model,
            variables_used=variables,
            system_prompt=final_sys,
            user_prompt=rendered,
            output=output,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=float(cost_usd),
            organization_id=organization_id,
            user_id=user_id
        )
        db.add(exec_log)
        db.commit()
        db.refresh(exec_log)

        return {
            "execution_id": exec_log.id,
            "output": output,
            "provider": provider,
            "model": resolved_model,
            "tokens_used": prompt_tokens + completion_tokens,
            "cost_usd": float(cost_usd),
            "latency_ms": latency_ms
        }


class EvaluationService:
    @staticmethod
    def evaluate_run(
        db: Session,
        prompt_id: uuid.UUID,
        test_case_id: uuid.UUID,
        model_name: str,
        actual_output: str,
        expected_output: Optional[str],
        latency_ms: int,
        tokens_used: int,
        cost_usd: float,
        organization_id: uuid.UUID
    ) -> PromptEvaluation:
        # Heuristic comparisons
        correctness = 1.0
        if expected_output:
            words_actual = set(actual_output.lower().split())
            words_expected = set(expected_output.lower().split())
            if words_actual or words_expected:
                correctness = len(words_actual.intersection(words_expected)) / max(1, len(words_actual.union(words_expected)))

        # Grounding metrics check
        grounding = 0.95
        if "sorry" in actual_output.lower() or "cannot fulfill" in actual_output.lower() or "error" in actual_output.lower():
            grounding = 0.40

        # Safety keywords scanning checks
        safety = 1.0
        blacklist = ["hack", "bypass security", "exploit", "jailbreak"]
        for word in blacklist:
            if word in actual_output.lower():
                safety -= 0.35
        safety = max(0.0, safety)

        # Relevance
        relevance = 0.90

        # Heuristic Hallucination Index
        hallucination = 0.05
        if expected_output and len(actual_output) > len(expected_output) * 2.5:
            hallucination = 0.35

        overall = (correctness * 0.4) + (grounding * 0.2) + (relevance * 0.2) + (safety * 0.2)
        status = "pass"
        if overall < 0.6:
            status = "fail"
        elif overall < 0.8:
            status = "warning"

        eval_result = PromptEvaluation(
            prompt_id=prompt_id,
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=actual_output,
            correctness_score=correctness,
            grounding_score=grounding,
            relevance_score=relevance,
            consistency_score=0.95,
            safety_score=safety,
            hallucination_risk=hallucination,
            overall_score=overall,
            status=status,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            organization_id=organization_id
        )
        db.add(eval_result)
        db.commit()
        db.refresh(eval_result)
        return eval_result


class OptimizationService:
    @staticmethod
    def analyze(content: str) -> dict:
        chars = len(content)
        words = len(content.split())
        
        suggestions = []
        token_efficiency = 100
        instruction_clarity = 90

        # Heuristic checks
        if chars > 5000:
            suggestions.append("Verify if length can be shortened. Use Knowledge Platform RAG contexts rather than embedding static database data.")
            token_efficiency -= 25

        if not ("#" in content or "1." in content or "-" in content):
            suggestions.append("Apply structured layout (use Markdown hierarchy sections like # Context, # Instructions) to optimize LLM adherence.")
            instruction_clarity -= 15

        vars_found = VariableEngine.extract_variables(content)
        if not vars_found:
            suggestions.append("No parameter tokens mapped. Parameterize variables (e.g. {{user_name}}) to reuse template within CRM automation loops.")

        if "you are" not in content.lower() and "role" not in content.lower():
            suggestions.append("Begin with persona framing rules (e.g. 'You are a CRM agent') to yield structured instructions outcomes.")
            instruction_clarity -= 10

        # Estimated savings
        expected_savings = 0.0
        if chars > 1500:
            # 35% tokens count savings by trimming redundant patterns
            estimated_tokens = chars / 4.2
            expected_savings = estimated_tokens * 0.0000015 * 0.35

        best_model = "gpt-4o"
        if "summar" in content.lower() or "translate" in content.lower():
            best_model = "gemini-1.5-flash"

        return {
            "token_efficiency": max(10, token_efficiency),
            "instruction_clarity": max(10, instruction_clarity),
            "suggestions": suggestions,
            "best_model": best_model,
            "expected_savings_usd": round(expected_savings, 5),
            "variables_count": len(vars_found)
        }


class ImportExportService:
    @staticmethod
    def import_prompts(
        db: Session, file_content: str, format_type: str, organization_id: uuid.UUID
    ) -> List[Prompt]:
        imported = []
        fmt = format_type.lower()
        
        if fmt == "json":
            data = json.loads(file_content)
            if not isinstance(data, list):
                data = [data]
            for item in data:
                p = Prompt(
                    name=item["name"],
                    content=item["content"],
                    category=item.get("category", "Custom"),
                    tags=item.get("tags", ""),
                    is_shared=item.get("is_shared", True),
                    organization_id=organization_id,
                    status=item.get("status", "approved")
                )
                db.add(p)
                imported.append(p)
                
        elif fmt == "yaml" and yaml:
            data = yaml.safe_load(file_content)
            if not isinstance(data, list):
                data = [data]
            for item in data:
                p = Prompt(
                    name=item["name"],
                    content=item["content"],
                    category=item.get("category", "Custom"),
                    tags=item.get("tags", ""),
                    is_shared=item.get("is_shared", True),
                    organization_id=organization_id,
                    status=item.get("status", "approved")
                )
                db.add(p)
                imported.append(p)
                
        elif fmt == "csv":
            f = io.StringIO(file_content)
            reader = csv.DictReader(f)
            for row in reader:
                p = Prompt(
                    name=row["name"],
                    content=row["content"],
                    category=row.get("category", "Custom"),
                    tags=row.get("tags", ""),
                    is_shared=row.get("is_shared", "true").lower() == "true",
                    organization_id=organization_id,
                    status=row.get("status", "approved")
                )
                db.add(p)
                imported.append(p)
                
        elif fmt == "markdown":
            # Split by markdown level 1 headings
            blocks = file_content.split("\n# ")
            for block in blocks:
                if not block.strip():
                    continue
                lines = block.split("\n")
                name = lines[0].strip().replace("# ", "")
                content = "\n".join(lines[1:]).strip()
                if name and content:
                    p = Prompt(
                        name=name,
                        content=content,
                        category="Custom",
                        organization_id=organization_id,
                    )
                    db.add(p)
                    imported.append(p)

        db.commit()
        for p in imported:
            db.refresh(p)
        return imported

    @staticmethod
    def export_prompts(prompts: List[Prompt], format_type: str) -> str:
        fmt = format_type.lower()
        if fmt == "json":
            return json.dumps([
                {
                    "name": p.name,
                    "content": p.content,
                    "version": p.version,
                    "category": p.category,
                    "tags": p.tags,
                    "is_shared": p.is_shared,
                    "status": p.status
                } for p in prompts
            ], indent=2)
            
        elif fmt == "yaml" and yaml:
            return yaml.safe_dump([
                {
                    "name": p.name,
                    "content": p.content,
                    "version": p.version,
                    "category": p.category,
                    "tags": p.tags,
                    "is_shared": p.is_shared,
                    "status": p.status
                } for p in prompts
            ])
            
        elif fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["name", "content", "version", "category", "tags", "is_shared", "status"])
            for p in prompts:
                writer.writerow([p.name, p.content, p.version, p.category, p.tags, p.is_shared, p.status])
            return output.getvalue()
            
        elif fmt == "markdown":
            md_str = ""
            for p in prompts:
                md_str += f"# {p.name}\n"
                md_str += f"**Category**: {p.category} | **Version**: v{p.version} | **Tags**: {p.tags}\n\n"
                md_str += f"{p.content}\n\n---\n\n"
            return md_str
            
        return ""
