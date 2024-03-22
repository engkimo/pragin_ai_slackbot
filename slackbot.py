import logging
import os
import json
import asyncio
import concurrent.futures
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv
from openai import OpenAI

class SlackBot:
    def __init__(self):
        load_dotenv()
        self.app = AsyncApp(token=os.environ['SLACK_BOT_TOKEN'])
        self.openai_client = OpenAI()
        self.assistant_id = os.environ["ASSISTANT_ID"]
        with open('answer_blocks.json', 'r') as f:
            self.answer_blocks_template = f.read()

    async def event_test(self, event, say):
        await say(f"Hi there, <@{event['user']}>! Please use the /pragin-ai command to ask me a question.")

    async def handle_message_events(self, event, say):
        await say(f"Hi there, <@{event['user']}>! Please use the /pragin-ai command to ask me a question.")

    async def faq_command(self, ack, body):
        logging.info(f"User {body['user_name']} called /pragin-ai with payload \"{body['text']}\"")
        if not body['text'].strip():
            response = "Please provide a question after the /pragin-ai command."
            await ack(f"{response}")
        else:
            asyncio.create_task(self.handle_faq(body))
            response = f"*Your question:* _{body['text']}_ \nLet me see if I can answer that..."
            await ack(f"{response}")

    async def handle_faq(self, body):
        response = await self.ask_llm(body['text'])
        await self.send_dm(body['user_id'], body['channel_id'], body['text'], response)

    async def ask_llm(self, payload):
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            thread = await loop.run_in_executor(pool, self.openai_client.beta.threads.create)
            await loop.run_in_executor(pool, lambda: self.openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=payload
            ))
            run = await loop.run_in_executor(pool, lambda: self.openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
            ))
            await asyncio.sleep(2)
            while True:
                run = await loop.run_in_executor(pool, lambda: self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                ))
                if run.status == 'completed':
                    break
                await asyncio.sleep(3)
            messages = await loop.run_in_executor(pool, lambda: self.openai_client.beta.threads.messages.list(
                thread_id=thread.id
            ))
            return (messages.data[0].content[0].text.value)

    async def send_dm(self, user_id, channel_id, question, response):
        question_escaped = question.replace("\n", "\\n").replace("\r", "\\r")
        response_escaped = response.replace("\n", "\\n").replace("\r", "\\r")
        blocks = str(self.answer_blocks_template).replace("{question}", question_escaped).replace("{answer}", response_escaped)
        blocks = json.loads(blocks)
        await self.app.client.chat_postEphemeral(
            blocks=blocks,
            user=user_id,
            channel=channel_id,
            text="Here is what I found in the FAQ: _response_"
        )

    async def start(self):
        self.app.event("app_mention")(self.event_test)
        self.app.event("message")(self.handle_message_events)
        self.app.command("/pragin-ai")(self.faq_command)
        handler = AsyncSocketModeHandler(self.app, os.environ['SLACK_APP_TOKEN'])
        await handler.start_async()

if __name__ == "__main__":
    slack_bot = SlackBot()
    asyncio.run(slack_bot.start())

