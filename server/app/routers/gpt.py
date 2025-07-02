# app/routers/gpt.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.routers.stats.analytics import ml_best_price_search
from app.schemas.gpt import GPTAskRequest, GPTAskResponse
from app.services.gpt import GPTClient, log_gpt_prompt, get_chat_history, get_user_filters

router = APIRouter()
gpt_client = GPTClient()

@router.post("/ask", response_model=GPTAskResponse)
async def gpt_ask(request: GPTAskRequest, db: AsyncSession=Depends(get_db)):
    """
    Ask a question to the GPT model and get response.
    """
    history_logs = await get_chat_history(db, request.user_id)
    history_messages = []
    for log in history_logs:
        history_messages.append({"role": "user", "content": log.gpt_prompt})
        history_messages.append({"role": "assistant", "content": log.gpt_response})

    context = request.context
    filters = {}
    filters = context.get('filters', filters)
    if filters == {}:
        print(f"No filters found in request context")
    
    ml_response = await (ml_best_price_search(request.user_id, db))
    best_price_offer = ml_response["top_offers"]

    try:
        gpt_response = await gpt_client.start_gpt(history_messages, filters, best_price_offer, request.gpt_prompt)
        await log_gpt_prompt(db, request.user_id, request.gpt_prompt, gpt_response)
        return GPTAskResponse(
            user_id=request.user_id,
            gpt_prompt=request.gpt_prompt,
            gpt_response=gpt_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={f"OPENAI GPT ERROR": str(e)})