# app/services/gpt.py
import asyncio
from openai import OpenAI
from sqlalchemy import desc
from sqlalchemy.future import select

from app.core.config import OPENAI_KEY
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import BASE_SYSTEM_PROMPT
from app.models.gpt import GPTPromptLog
from app.models.license import LicenseKey


class GPTClient:
    def __init__(self, api_key=OPENAI_KEY):
        self.client = OpenAI(api_key=api_key)

    async def start_gpt(self, history: list[dict], filters: list[dict], best_price_offer: dict[dict, dict],
                        prompt: str):
        system_message = {
            "role": "system",
            "content": f"{BASE_SYSTEM_PROMPT}"
                       f"\nUser preferences: {filters}"
                       f"\nTop 10 car deals: {best_price_offer}"
        }
        messages = [system_message] + history + [{"role": "user", "content": prompt}]

        response = await asyncio.to_thread(
            lambda: self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
        )
        return response.choices[0].message.content


async def log_gpt_prompt(db: AsyncSession, user_id: str, gpt_prompt: str, gpt_response: str):
    """ Log the GPT prompt and response to the database. """
    gpt_log = GPTPromptLog(
        user_id=user_id,
        gpt_prompt=gpt_prompt,
        gpt_response=gpt_response
    )
    db.add(gpt_log)
    await db.commit()
    await db.refresh(gpt_log)
    return gpt_log


async def get_chat_history(db: AsyncSession, user_id: str, limit: int = 5):
    """ Retrieve the chat history for a user. """
    if not user_id:
        return {
            "history": [],
            "message": "user_id is required to retrieve chat history."
        }
    stmt = (
        select(GPTPromptLog)
        .where(GPTPromptLog.user_id == user_id)
        .order_by(GPTPromptLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = list(result.scalars().all())
    logs.reverse()  # Reverse to show the oldest first
    return logs  # returning the list of logs


async def clear_chat_history(db: AsyncSession, user_id: str):
    """ Clear all chat history for a user. """
    if not user_id:
        return 0
    
    # Get count of records to be deleted
    count_stmt = select(GPTPromptLog).where(GPTPromptLog.user_id == user_id)
    count_result = await db.execute(count_stmt)
    records_to_delete = count_result.scalars().all()
    deleted_count = len(records_to_delete)
    
    # Delete all records for the user
    for record in records_to_delete:
        await db.delete(record)
    
    await db.commit()
    return deleted_count


async def get_user_filters(db: AsyncSession, user_id: str):
    """ Retrieve the filters for a user. """
    if not user_id:
        return {
            "filters": [],
            "message": "user_id is required to retrieve filters."
        }
    stmt = select(LicenseKey).where(LicenseKey.key == user_id)
    result = await db.execute(stmt)
    license_data = result.scalar_one_or_none()
    return {
        "filters": license_data.filters if license_data and license_data.filters else []}  # returning the filters list


if __name__ == "__main__":
    client = GPTClient()
