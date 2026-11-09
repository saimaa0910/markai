import uuid
import logging
import datetime
import socket
import ipaddress
from urllib.parse import urlparse
import requests
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.services.memory_manager import MemoryManager
from api.ai.agents.image.prompts import ImagePromptEngine
from api.ai.agents.image.constants import ASPECT_RATIOS
from api.ai.agents.image.provider_router import ImageProviderRouter
from api.ai.agents.image.asset_manager import AssetManager
from api.ai.agents.image.reflection import image_reflector
from api.ai.agents.image.evaluation import image_evaluator
from api.ai.agents.image.history import AIImageLibrary

logger = logging.getLogger(__name__)


class ImageExecutor:
    """
    Coordinates RAG context checks, Prompt Engine compiling, provider routing,
    asset saving, database history tracking, reflection, and evaluation scoring.
    """

    def __init__(self, db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.db = db
        self.org_id = org_id
        self.user_id = user_id
        self.provider_router = ImageProviderRouter(db, org_id, user_id)
        from api.ai.tools.registry import ToolExecutor
        self.tool_executor = ToolExecutor(db)

    def _query_rag(self, prompt: str, collection_ids: Optional[List[uuid.UUID]]) -> str:
        """Helper to query RAG search knowledge context."""
        if not collection_ids:
            return ""
        try:
            res = self.tool_executor.execute(
                tool_name="knowledge_tool",
                params={
                    "query": prompt,
                    "limit": 2
                },
                organization_id=str(self.org_id),
                user_id=str(self.user_id)
            )
            if res.success and isinstance(res.output, dict):
                docs = res.output.get("documents", [])
                return "\n".join([f"Guideline: {d.get('text', '')}" for d in docs])
        except Exception as e:
            logger.warning("RAG fetch failed (non-fatal): %s", e)
        return ""

    def _is_public_http_url(self, url: str) -> bool:
        """Validate URL scheme/host and block private/internal IP destinations."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return False
            if not parsed.hostname:
                return False

            addrinfo = socket.getaddrinfo(parsed.hostname, None)
            if not addrinfo:
                return False

            for entry in addrinfo:
                ip_str = entry[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_reserved
                    or ip_obj.is_unspecified
                ):
                    return False
            return True
        except Exception:
            return False

    def _download_url(self, url: str) -> bytes:
        """Helper to download image content from URL."""
        if not url:
            return b""
        if not self._is_public_http_url(url):
            logger.warning("Blocked unsafe image URL: %s", url)
            return b""
        try:
            res = requests.get(url, timeout=30, allow_redirects=False)
            res.raise_for_status()
            return res.content
        except Exception as e:
            logger.warning("Failed to download image from %s: %s", url, e)
            return b""

    def generate(
        self,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        campaign_id: Optional[uuid.UUID] = None,
        knowledge_collections: Optional[List[uuid.UUID]] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
        template: Optional[str] = None,
        audience_context: Optional[str] = None,
        seo_keywords: Optional[str] = None,
        content_context: Optional[str] = None,
        typography: Optional[str] = None,
        color_palette: Optional[str] = None,
        composition: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        library_item_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Runs the image generation pipeline."""
        # 1. Fetch Brand guide memories
        brand_voice = ""
        try:
            memories = MemoryManager.get_org_memory(self.db, self.org_id)
            voice_items = [m.value for m in memories if m.key == "brand_voice" or m.category == "brand_voice"]
            brand_voice = "\n".join(voice_items) if voice_items else "Professional, premium branding colors."
        except Exception as e:
            logger.warning("Failed to fetch brand voice memories: %s", e)

        # 2. Query RAG
        rag_context = self._query_rag(prompt, knowledge_collections)

        # 3. Compile prompt via PromptEngine
        brand_ctx = {"brand_voice": brand_voice} if brand_voice else None
        compiled_prompt = ImagePromptEngine.compile_prompt(
            user_prompt=prompt,
            style=style,
            brand_context=brand_ctx,
            campaign_context={"keywords": rag_context[:500]} if rag_context else None,
            template=template,
            audience_context=audience_context,
            seo_keywords=seo_keywords,
            content_context=content_context,
            typography=typography,
            color_palette=color_palette,
            composition=composition
        )
        neg_prompt = ImagePromptEngine.get_negative_prompt(negative_prompt)

        # 4. Resolve aspect ratio size
        dimensions = ASPECT_RATIOS.get(aspect_ratio or "1:1", ASPECT_RATIOS["1:1"])
        w, h = dimensions["width"], dimensions["height"]

        # 5. Call Provider Router
        try:
            image_bytes, provider, resolved_model = self.provider_router.generate_image(
                prompt=compiled_prompt,
                width=w,
                height=h,
                style=style,
                model=model,
                seed=seed,
                negative_prompt=neg_prompt,
                cfg_scale=cfg_scale,
                steps=steps
            )
        except Exception as exc:
            logger.exception("Image generation failed")
            return {
                "id": str(uuid.uuid4()),
                "status": "failed",
                "storage_url": "",
                "provider": "",
                "model": model or "",
                "prompt": prompt,
                "compiled_prompt": compiled_prompt,
                "reflection": {},
                "evaluation": {},
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": str(exc),
                    "details": {"style": style, "aspect_ratio": aspect_ratio, "model": model},
                },
            }

        # 6. Save Asset in database and MinIO
        file_asset = AssetManager.save_image_asset(
            db=self.db,
            image_bytes=image_bytes,
            filename=f"generated_creative_{uuid.uuid4().hex[:8]}.png",
            organization_id=self.org_id
        )

        # 7. Run Reflection and Evaluation
        reflection_res = image_reflector.reflect(
            db=self.db,
            prompt=compiled_prompt,
            style=style,
            brand_voice=brand_voice,
            organization_id=self.org_id,
            user_id=self.user_id
        )

        # Create simulated run ID for evaluation linking
        run_id = uuid.uuid4()
        eval_metrics = image_evaluator.evaluate(
            db=self.db,
            run_id=run_id,
            organization_id=self.org_id,
            reflection=reflection_res
        )

        # Calculate incremental cost values
        cost_usd = 0.04
        try:
            from api.models.ai_platform import AICost, AIUsage
            from api.ai.cost.cost_tracker import cost_tracker
            # Accumulate cost limits
            org_limit = self.db.scalars(
                select(self.db.models.AIOrgLimit if hasattr(self.db, "models") else self.db.query).filter_by(organization_id=self.org_id)
            ).first()
            if org_limit:
                org_limit.credit_used = float(org_limit.credit_used or 0.0) + cost_usd
                self.db.commit()
        except Exception as ec:
            logger.warning("Cost tracker updates failed: %s", ec)

        # 8. Save/Update Generation record in Library
        if library_item_id:
            library_item = self.db.query(AIImageLibrary).filter(AIImageLibrary.id == library_item_id).first()
        else:
            library_item = None

        if library_item:
            library_item.provider = provider
            library_item.model = resolved_model
            library_item.storage_url = file_asset.storage_url
            library_item.file_asset_id = file_asset.id
            library_item.status = "COMPLETED"
            library_item.run_id = run_id
            library_item.seed = seed
            library_item.parent_id = parent_id
            if style:
                library_item.tags = {"preset_style": style}
        else:
            library_item = AIImageLibrary(
                prompt=prompt,
                negative_prompt=neg_prompt,
                provider=provider,
                model=resolved_model,
                seed=seed,
                cfg_scale=cfg_scale,
                steps=steps,
                organization_id=self.org_id,
                user_id=self.user_id,
                campaign_id=campaign_id,
                run_id=run_id,
                storage_url=file_asset.storage_url,
                file_asset_id=file_asset.id,
                parent_id=parent_id,
                status="COMPLETED",
                tags={"preset_style": style or "Minimal"}
            )
            self.db.add(library_item)

        self.db.commit()
        self.db.refresh(library_item)

        return {
            "id": str(library_item.id),
            "storage_url": file_asset.storage_url,
            "provider": provider,
            "model": resolved_model,
            "prompt": prompt,
            "compiled_prompt": compiled_prompt,
            "reflection": reflection_res.model_dump() if hasattr(reflection_res, "model_dump") else str(reflection_res),
            "evaluation": eval_metrics.model_dump() if hasattr(eval_metrics, "model_dump") else str(eval_metrics),
        }

    def edit(
        self,
        image_url: str,
        prompt: str,
        mask_url: Optional[str] = None,
        style: Optional[str] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Runs image-to-image or editing pipeline."""
        image_bytes = self._download_url(image_url)
        mask_bytes = self._download_url(mask_url) if mask_url else None

        edited_bytes, provider, resolved_model = self.provider_router.route_operation(
            operation="edit",
            prompt=prompt,
            image_bytes=image_bytes,
            mask_bytes=mask_bytes,
            style=style,
            model=model,
            seed=seed
        )

        file_asset = AssetManager.save_image_asset(
            db=self.db,
            image_bytes=edited_bytes,
            filename=f"edited_creative_{uuid.uuid4().hex[:8]}.png",
            organization_id=self.org_id
        )

        library_item = AIImageLibrary(
            prompt=prompt,
            provider=provider,
            model=resolved_model,
            seed=seed,
            organization_id=self.org_id,
            user_id=self.user_id,
            storage_url=file_asset.storage_url,
            file_asset_id=file_asset.id,
            status="COMPLETED",
            tags={"preset_style": style or "Edited"}
        )
        self.db.add(library_item)
        self.db.commit()
        self.db.refresh(library_item)

        return {
            "id": str(library_item.id),
            "storage_url": file_asset.storage_url,
            "provider": provider,
            "model": resolved_model,
            "prompt": prompt,
        }

    def variation(
        self,
        image_url: str,
        style: Optional[str] = None,
        model: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Creates image variation."""
        image_bytes = self._download_url(image_url)

        var_bytes, provider, resolved_model = self.provider_router.route_operation(
            operation="variation",
            image_bytes=image_bytes,
            style=style,
            model=model,
            seed=seed
        )

        file_asset = AssetManager.save_image_asset(
            db=self.db,
            image_bytes=var_bytes,
            filename=f"variation_{uuid.uuid4().hex[:8]}.png",
            organization_id=self.org_id
        )

        library_item = AIImageLibrary(
            prompt=f"Variation of {image_url}",
            provider=provider,
            model=resolved_model,
            seed=seed,
            organization_id=self.org_id,
            user_id=self.user_id,
            storage_url=file_asset.storage_url,
            file_asset_id=file_asset.id,
            status="COMPLETED",
            tags={"preset_style": style or "Variation"}
        )
        self.db.add(library_item)
        self.db.commit()
        self.db.refresh(library_item)

        return {
            "id": str(library_item.id),
            "storage_url": file_asset.storage_url,
            "provider": provider,
            "model": resolved_model,
        }

    def upscale(
        self,
        image_url: str,
        scale: float = 2.0,
    ) -> Dict[str, Any]:
        """Upscale image resolution."""
        image_bytes = self._download_url(image_url)

        upscaled_bytes, provider, resolved_model = self.provider_router.route_operation(
            operation="upscale",
            image_bytes=image_bytes,
            scale=scale
        )

        file_asset = AssetManager.save_image_asset(
            db=self.db,
            image_bytes=upscaled_bytes,
            filename=f"upscaled_{uuid.uuid4().hex[:8]}.png",
            organization_id=self.org_id
        )

        library_item = AIImageLibrary(
            prompt=f"Upscaled {scale}x of {image_url}",
            provider=provider,
            model=resolved_model,
            organization_id=self.org_id,
            user_id=self.user_id,
            storage_url=file_asset.storage_url,
            file_asset_id=file_asset.id,
            status="COMPLETED",
            tags={"preset_style": f"Upscale {scale}x"}
        )
        self.db.add(library_item)
        self.db.commit()
        self.db.refresh(library_item)

        return {
            "id": str(library_item.id),
            "storage_url": file_asset.storage_url,
            "provider": provider,
            "model": resolved_model,
        }

    def remove_background(self, image_url: str) -> Dict[str, Any]:
        """Removes background from image."""
        return self.edit(image_url=image_url, prompt="remove background")

    def replace_background(self, image_url: str, background_prompt: str) -> Dict[str, Any]:
        """Replaces background of image."""
        return self.edit(image_url=image_url, prompt=f"replace background with {background_prompt}")

    def inpaint(self, image_url: str, mask_url: str, prompt: str) -> Dict[str, Any]:
        """Inpaints within image mask."""
        return self.edit(image_url=image_url, prompt=prompt, mask_url=mask_url)

    def outpaint(self, image_url: str, mask_url: str, prompt: str) -> Dict[str, Any]:
        """Outpaints expanding image boundaries."""
        return self.edit(image_url=image_url, prompt=f"expand canvas background: {prompt}", mask_url=mask_url)
