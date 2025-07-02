# app/schemas/gpt.py
from pydantic import BaseModel


class GPTAskRequest(BaseModel):
    user_id: str
    gpt_prompt: str
    context: dict
    chat_history: list

class GPTAskResponse(BaseModel):
    user_id: str
    gpt_prompt: str
    gpt_response: str
