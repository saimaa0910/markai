"""
Conversational & Episodic Memory Manager.
"""

from typing import List, Dict, Any


class ConversationalMemoryBuffer:
    """
    Stateful conversational memory window manager.
    """
    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to memory buffer.
        """
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retrieve messages in buffer.
        """
        return self.messages
