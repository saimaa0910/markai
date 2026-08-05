"""
Users Service Business Logic.
"""

from typing import Optional, Dict, Any


class UserService:
    """
    Users domain business logic.
    """
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        # TODO: Retrieve user profile from repository
        return {"id": user_id}


user_service = UserService()
