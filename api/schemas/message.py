# api/schemas/message.py
import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import datetime

# --- Feedback Schema ---
class FeedbackData(BaseModel):
    rating: Literal["up", "down"]
    comment: Optional[str] = None

# --- End Feedback Schema ---

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime.datetime] = None # Kept optional
    file_id: Optional[str] = None  # Reference to a file if one is attached
    feedback_details: Optional[FeedbackData] = None # Added field for feedback

class FileMetadata(BaseModel):
    id: str  # UUID as string
    filename: str
    upload_date: datetime.datetime
    user_id: int
    conversation_id: str

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass # Might add initial messages later

class Conversation(ConversationBase):
    id: str # UUID as string
    user_id: int
    timestamp: datetime.datetime
    messages: List[Message] = []
    files: List[FileMetadata] = []  # List of files attached to this conversation

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None # Client can specify existing convo or let server create one
    file_id: Optional[str] = None  # Reference to a previously uploaded file

class ChatResponse(BaseModel):
    conversation_id: str
    assistant_message: Message
    full_conversation: Optional[List[Message]] = None # Optionally return full history

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    conversation_id: str
    message: str = "File uploaded successfully."


