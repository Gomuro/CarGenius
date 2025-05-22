# app/routers/gpt.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.gpt import GPTAskRequest, GPTAskResponse
from app.services.gpt import GPTClient, log_gpt_prompt

router = APIRouter()
gpt_client = GPTClient()

@router.post("/ask", response_model=GPTAskResponse)
async def gpt_ask(request: GPTAskRequest, db: AsyncSession=Depends(get_db)):
    """
    Ask a question to the GPT model and get response.
    """
    try:
        gpt_response = await gpt_client.start_gpt(request.gpt_prompt)
        await log_gpt_prompt(db, request.user_id, request.gpt_prompt, gpt_response)
        return GPTAskResponse(
            user_id=request.user_id,
            gpt_prompt=request.gpt_prompt,
            gpt_response=gpt_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={f"OPENAI GPT ERROR": str(e)})