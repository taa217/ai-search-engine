"""
Session/context manager for agentic search. Maintains per-user conversational context.
"""
import uuid
from typing import Any, Dict

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.sessions:
            self.sessions[user_id] = {"id": str(uuid.uuid4()), "history": []}
        return self.sessions[user_id]

    def update_session(self, user_id: str, query: str, response: Dict[str, Any]):
        session = self.get_session(user_id)
        session["history"].append({"query": query, "response": response})
