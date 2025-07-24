# app/routers/gpt.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.routers.stats.analytics import ml_best_price_search
from app.schemas.gpt import GPTAskRequest, GPTAskResponse
from app.services.gpt import GPTClient, log_gpt_prompt, get_chat_history, clear_chat_history
from typing import List, Dict, Any

router = APIRouter()
gpt_client = GPTClient()


@router.get("/history/{user_id}")
async def get_user_chat_history(user_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Get chat history for a specific user.
    """
    try:
        history_logs = await get_chat_history(db, user_id, limit)
        history_messages = []
        for log in history_logs:
            history_messages.append(
                {"role": "user", "content": log.gpt_prompt, "timestamp": log.created_at.isoformat()})
            history_messages.append(
                {"role": "assistant", "content": log.gpt_response, "timestamp": log.created_at.isoformat()})

        return {
            "user_id": user_id,
            "history": history_messages,
            "count": len(history_messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")


@router.delete("/history/{user_id}")
async def clear_user_chat_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Clear all chat history for a specific user.
    """
    try:
        deleted_count = await clear_chat_history(db, user_id)

        return {
            "user_id": user_id,
            "message": "Chat history cleared successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")


@router.post("/ask", response_model=GPTAskResponse)
async def gpt_ask(request: GPTAskRequest, db: AsyncSession = Depends(get_db)):
    """
    Ask a question to the GPT model and get response.
    """
    history_logs = await get_chat_history(db, request.user_id)
    history_messages = []
    for log in history_logs:
        history_messages.append({"role": "user", "content": log.gpt_prompt})
        history_messages.append({"role": "assistant", "content": log.gpt_response})

    context = request.context
    car = context.get('car', {})
    filters = {}
    filters = context.get('filters', filters)
    if filters == {}:
        print(f"No filters found in request context")
        best_price_offer = {}
    else:

        ml_response = await ml_best_price_search(request.user_id, db, filters)
        if isinstance(ml_response, dict) and "top_offers" in ml_response:
            best_price_offer = ml_response["top_offers"]
        else:
            best_price_offer = {}

    try:
        gpt_response = await gpt_client.start_gpt(car, history_messages, filters, best_price_offer, request.gpt_prompt)
        await log_gpt_prompt(db, request.user_id, request.gpt_prompt, gpt_response)
        return GPTAskResponse(
            user_id=request.user_id,
            gpt_prompt=request.gpt_prompt,
            gpt_response=gpt_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={f"OPENAI GPT ERROR": str(e)})
