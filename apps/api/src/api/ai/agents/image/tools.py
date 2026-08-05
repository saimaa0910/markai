import uuid
from typing import Any, Dict, List
from api.ai.tools import BaseTool, ToolInput, ToolResult


class ImageGenerateTool(BaseTool):
    """Tool allowing agents to programmatically generate marketing images."""

    @property
    def name(self) -> str:
        return "image_generate_tool"

    @property
    def description(self) -> str:
        return "Generates visual assets and marketing product pictures from detailed prompts and design style presets."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Visual details and objects of the image."},
                "style": {"type": "string", "description": "Style presets: e.g. apple, minimal, modern saas, clay."},
                "aspect_ratio": {"type": "string", "description": "Layout sizes: e.g. 1:1, 16:9, 9:16."},
            },
            "required": ["prompt"],
        }

    def execute(self, tool_input: ToolInput, db: Any) -> ToolResult:
        params = tool_input.params
        prompt = params.get("prompt", "")
        style = params.get("style")
        aspect_ratio = params.get("aspect_ratio")

        try:
            from api.ai.agents.image.executor import ImageExecutor
            executor = ImageExecutor(
                db=db,
                org_id=uuid.UUID(tool_input.organization_id),
                user_id=uuid.UUID(tool_input.user_id)
            )
            res = executor.generate(
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio
            )
            return ToolResult(
                success=True,
                tool_name=self.name,
                output=res
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=f"Image generation failed: {str(e)}"
            )


class ImageEditTool(BaseTool):
    """Tool allowing agents to modify or vary images."""

    @property
    def name(self) -> str:
        return "image_edit_tool"

    @property
    def description(self) -> str:
        return "Edits or generates a visual variation of an existing image asset with a prompt context."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "Source image URL to edit."},
                "prompt": {"type": "string", "description": "Modification details instruction."},
            },
            "required": ["image_url", "prompt"],
        }

    def execute(self, tool_input: ToolInput, db: Any) -> ToolResult:
        params = tool_input.params
        image_url = params.get("image_url")
        prompt = params.get("prompt", "")

        try:
            from api.ai.agents.image.executor import ImageExecutor
            executor = ImageExecutor(
                db=db,
                org_id=uuid.UUID(tool_input.organization_id),
                user_id=uuid.UUID(tool_input.user_id)
            )
            res = executor.edit(image_url=image_url, prompt=prompt)
            return ToolResult(
                success=True,
                tool_name=self.name,
                output=res
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=f"Image edit failed: {str(e)}"
            )


class ImageUpscaleTool(BaseTool):
    """Tool allowing agents to upscale images."""

    @property
    def name(self) -> str:
        return "image_upscale_tool"

    @property
    def description(self) -> str:
        return "Upscales an existing image asset to a higher resolution."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "Source image URL to upscale."},
                "scale": {"type": "number", "description": "Multiplier factor (e.g. 2.0)."},
            },
            "required": ["image_url"],
        }

    def execute(self, tool_input: ToolInput, db: Any) -> ToolResult:
        params = tool_input.params
        image_url = params.get("image_url")
        scale = params.get("scale", 2.0)

        try:
            from api.ai.agents.image.executor import ImageExecutor
            executor = ImageExecutor(
                db=db,
                org_id=uuid.UUID(tool_input.organization_id),
                user_id=uuid.UUID(tool_input.user_id)
            )
            res = executor.upscale(image_url=image_url, scale=scale)
            return ToolResult(
                success=True,
                tool_name=self.name,
                output=res
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=f"Image upscale failed: {str(e)}"
            )
