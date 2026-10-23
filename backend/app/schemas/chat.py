from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = "user_default_01"
    transaction_id: Optional[str] = None
    case_id: Optional[str] = None
    initial_message: Optional[str] = None

class MessageIn(BaseModel):
    content: str
    user_id: Optional[str] = "user_default_01"
    transaction_id: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = []
    tool_results: Optional[List[Dict[str, Any]]] = []
    metadata_json: Optional[Dict[str, Any]] = {}
    created_at: datetime

class ChatSessionOut(BaseModel):
    id: str
    user_id: str
    transaction_id: Optional[str]
    case_id: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime
    latest_message: Optional[str] = None
    message_count: int = 0
