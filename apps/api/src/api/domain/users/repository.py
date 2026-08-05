"""
Users Domain Data Repository.
"""

from typing import Optional, Any


class UserRepository:
    """
    UserRepository database query interface.
    """
    async def find_by_id(self, user_id: str) -> Optional[Any]:
        # TODO: Execute database SELECT query
        return None


user_repository = UserRepository()
