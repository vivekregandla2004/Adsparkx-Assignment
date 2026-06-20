"""
Multi-turn conversation memory — maintains a sliding window of recent messages.
"""
from dataclasses import dataclass, field
from src.config import MEMORY_WINDOW


@dataclass
class ConversationMemory:
    """
    Stores the last N conversation turns and provides formatted history
    for use in persona classification and response generation.

    Each message is stored as: {"role": "user"|"assistant", "content": str}
    """
    window: int = MEMORY_WINDOW
    _messages: list[dict] = field(default_factory=list, init=False, repr=False)

    def add(self, role: str, content: str) -> None:
        """Add a message to the memory window."""
        if role not in {"user", "assistant"}:
            raise ValueError(f"Role must be 'user' or 'assistant', got: {role!r}")
        self._messages.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        """Return the most recent N messages (full window)."""
        return self._messages[-self.window * 2 :]  # *2 for user+assistant pairs

    def get_formatted(self) -> str:
        """
        Return a human-readable string of recent conversation history
        for injection into LLM prompts.
        """
        history = self.get_history()
        if not history:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Support Agent"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def get_user_messages(self) -> list[str]:
        """Return only the user messages as a list of strings."""
        return [
            msg["content"]
            for msg in self._messages
            if msg["role"] == "user"
        ]

    def clear(self) -> None:
        """Reset the conversation memory."""
        self._messages = []

    @property
    def message_count(self) -> int:
        """Total number of messages stored (not just the window)."""
        return len(self._messages)

    @property
    def turn_count(self) -> int:
        """Number of user turns stored."""
        return sum(1 for m in self._messages if m["role"] == "user")
