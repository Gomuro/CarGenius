# app/services/gpt.py
import asyncio
from openai import OpenAI
from app.core.config import OPENAI_KEY
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.gpt import GPTPromptLog


class GPTClient:
    def __init__(self, api_key=OPENAI_KEY):
        self.client = OpenAI(api_key=api_key)

    async def start_gpt(self, prompt):
        response = await asyncio.to_thread(
            lambda: self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
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




    # def create_task_object(self, user_feedback, feedback_id=None):
    #     task_title = self.generate_task_title(user_feedback)
    #     description = self.generate_task_description(user_feedback)
    #     priority = self.generate_priority(user_feedback)
    #     return task_title, description, priority
    #
    # def generate_task_title(self, feedback):
    #     response = self.start_gpt(f"Generate a task title line based on the feedback provided: {feedback}.")
    #     return response
    #
    # def generate_task_description(self, feedback):
    #     prompt = f"Generate a task based on the following feedback:{feedback}"
    #     response = self.start_gpt(prompt)
    #     return response
    #
    # def generate_priority(self, feedback):
    #     priority_list = ["High", "Low", "Medium", "Urgent"]
    #     prompt = f"Based on the urgency of the feedback ({feedback}), First of laa return one word response about priority {priority_list}"
    #     response = self.start_gpt(prompt)
    #     return response


if __name__ == "__main__":
    client = GPTClient()

