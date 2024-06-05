import asyncio
import contextlib
import json
import operator
import os
import asyncio
import re
import textwrap

import typing
from collections import deque
from io import BytesIO

import aiohttp
from PIL import Image
from openai import AsyncOpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion

from utils.buttons import SingleURLButton
from utils.format import human_join, durationdisplay, proper_userf, print_exception

from main import dvvt
import discord
from discord.ext import commands, tasks
import pytesseract

ID_REGEX = re.compile(r"([0-9]{15,20})")

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

model = "gpt-3.5-turbo-0125"

# class AnalysisResultView(discord.ui.View):


class GPTMessageAnalysisException(Exception):
    def __init__(self, original_error, response: typing.Optional[ChatCompletion] =None):
        """
        Initialize the exception with the original error and optional response object.

        Args:
            original_error (Exception): The original error that caused the exception.
            response (Optional[OpenAIResponse]): The OpenAI response object, if available.
        """
        self.original_error = original_error
        self.response = response

        # Combine error message and response details (if available) for informative output
        message = f"Error during message moderation: {str(original_error)}"
        if response:
            message += f"\nOpenAI Response (if available): {response}"
        super().__init__(message)


def return_emoji(truefalse: bool):
    if truefalse:
        return "<:DVB_True:887589686808309791> "
    else:
        return "<:DVB_False:887589731515392000>"


async def extract_text_from_image(url):
    async with aiohttp.ClientSession(headers={"User-Agent": "PostmanRuntime/7.36.3"}) as session:
        async with session.get(url) as response:
            if response.status == 200:
                img_data = await response.read()
                img = Image.open(BytesIO(img_data))
                return pytesseract.image_to_string(img)
            else:
                return ""

async def process_attachments_and_links(message: discord.Message):
    content_addition = ""

    # Process attachments
    for attachment in message.attachments:
        print("Attachment detected")
        if attachment.url.endswith(('png', 'jpg', 'jpeg')):
            img_text = await extract_text_from_image(attachment.url)
            content_addition += f" {img_text}"

    # Process links
    for word in message.content.split():
        if word.startswith("http://") or word.startswith("https://"):
            print(f"Link detected ({word})")
            if any(word.endswith(ext) for ext in ('png', 'jpg', 'jpeg')):
                img_text = await extract_text_from_image(word)
                content_addition += f" {img_text}"

    if content_addition:
        content_addition = "; IMAGECONTENTS: " + content_addition

    return content_addition


class AIMessageModeration(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.plana_messages = deque(maxlen=3)
        self.openai_api_key = os.getenv("DVB_OPENAI_API_KEY")
        if self.openai_api_key is None:
            print("No OpenAI API key found")

    async def moderate_messages(self, messages: typing.List[discord.Message]):
        openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        messages_content = "\n".join([f"{i+1}. \"{msg}\"" for i, msg in enumerate(messages)])
        prompt = (
            "You are a content moderation assistant. Your job is to detect if a member is talking about, advertising, or promoting a Discord server. "
            "Analyze the following messages and determine the overall likelihood that they are talking about, advertising, or promoting a Discord server, or their own Discord server. The messages may be sent in a way to evade detection, so any mention of a server should be considered. "
            "There may be text recovered from images sent in the message, which will be included with the actual message content. They will be appended after the actual message content following the phrase 'IMAGECONTENTS'. You may use the image text contents if it is relevant. "
            "Provide a percentage score from 0 to 100, where 0 means 'not at all likely' and 100 means 'extremely likely'. Assume any mention of a server equates to a Discord server. "
            "If any message has any presence of the word 'enlight' (the vanity link for their Discord server), it is IMMEDIATELY a 100 score. "
            "Consider the following as potential indicators of talking about, advertising, or promoting a Discord server: "
            "- Direct invitations (e.g., 'join my server', 'check out this server') "
            "- Implicit invitations (e.g., 'we have a great community', 'lots of fun here') "
            "- Discussion of happenings in their server (e.g., 'pride month is happening in our server') "
            "- Sharing of server links or codes "
            "- References to server-specific activities or events (e.g., 'we have movie nights on our server') "
            "When in doubt, lean towards a higher likelihood if there's any indication of promoting a server. "
            "When unclear if a 'server' is mentioned, infer that it is referring to a Discord server."
            "Then, provide short reasons for your assessment in point form.\n\n"
            f"Messages:\n{messages_content}\n\n"
            "Use the format below for your output (without the backticks):\n\n"
            "```<whole number from 0 to 100>\\n\\nREASONS\\n- <reasons>```\n"
            "Reasons should be in point form with dash symbols."
        )

        try:
            print(f"Prompt: \n==========\n{prompt}\n==========")
            response = await openai_client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=model
            )
            try:
                answer = response.choices[0].message.content.strip()
                lines = answer.split("\n")
                probability_line = lines[0].strip().replace("%", "").replace("```", "")
                probability = float(probability_line)
                reason_lines = answer.split("REASONS")[-1]
                usage = response.usage
                return probability, reason_lines, usage
            except Exception as e:
                raise GPTMessageAnalysisException(e, response)
        except Exception as e:
            raise GPTMessageAnalysisException(e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.client.wait_until_ready()
        plana_user_id = os.getenv("PLANA_USER_ID")
        plana_guild_id = os.getenv("PLANA_MONITORING_GUILD_ID")
        try:
            plana_user_id = int(plana_user_id)
            plana_guild_id = int(plana_guild_id)
        except:
            plana_user_id = 0
            plana_guild_id = 0
        if plana_user_id == message.author.id and message.guild.id == plana_guild_id:
            content = message.content
            content_addition = await process_attachments_and_links(message)
            if content_addition:
                content += content_addition
            self.plana_messages.append(content)
            print("Detected a message from target")
            probability, reasons, usage = await self.moderate_messages(list(self.plana_messages))
            if probability > 20:
                print("PROBABILITY HIGHER THAN 20")
                embed = discord.Embed(title="Possible server advertising detected", description=f"## Probability: {probability}%\n\n> {content}", color=discord.Color.red())
                embed.set_author(name=proper_userf(message.author), icon_url=message.author.display_avatar.with_size(128).url)
                embed.add_field(name="Reasons", value=reasons)
                cid = os.getenv("CHATGPT_OUTPUT_CHANNEL_ID")
                footer = f"Tokens used: Completion {usage.completion_tokens}, Prompt {usage.prompt_tokens}; Model: {model};"
                embed.set_footer(text=footer, icon_url="https://i.imgur.com/OcUsi8s.png")
                try:
                    cid = int(cid)
                except Exception as e:
                    cid = None
                if cid is not None:
                    c = self.client.get_channel(cid)
                    await c.send(embed=embed, view=SingleURLButton(message.jump_url, "Jump to message"))

                print(f"Probability: {probability}\n\nReasons: \n\n{reasons}")
            else:
                print("PROBABILITY LOWER THAN 20")

    def cog_unload(self) -> None:
        pass
