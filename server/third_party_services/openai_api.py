from openai import OpenAI
import ast

from app.core.config import OPENAI_KEY


class GPTClient:
    def __init__(self, api_key=OPENAI_KEY):
        self.client = OpenAI(api_key=api_key)

    def create_task_object(self, user_feedback, feedback_id=None):
        task_title = self.generate_task_title(user_feedback)
        description = self.generate_task_description(user_feedback)
        priority = self.generate_priority(user_feedback)

        return task_title, description, priority

    
    def start_gpt(self, prompt):
        response = self.client.chat.completions.create(model="gpt-4-turbo", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    
    def generate_task_title(self, feedback):
        response = self.start_gpt(f"Generate a task title line based on the feedback provided: {feedback}.")
        return response

    def generate_task_description(self, feedback):
        prompt = f"Generate a task based on the following feedback:{feedback}"
        response = self.start_gpt(prompt)
        return response

    def generate_priority(self, feedback):
        priority_list = [ "High", "Low", "Medium", "Urgent" ]
        prompt = f"Based on the urgency of the feedback ({feedback}), First of laa return one word response about priority {priority_list}"
        response = self.start_gpt(prompt)
        return response

    
if __name__ == "__main__":
    client = GPTClient()

    feedback = "The app crashes when I click on the login button. Please fix it as soon as possible."
    title, desc, priority = client.create_task_object(feedback, 1)

    print("Title:", title)
    print("Description:", desc)
    print("Priority:", priority)
