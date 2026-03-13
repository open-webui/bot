"""
Open WebUI Channel AI Bot Example
Validated against Open WebUI version: 0.5.10

This script demonstrates how to create a simple AI assistant that listens
to Open WebUI channel events and responds when a message begins with "AI:".

The bot connects to the Open WebUI websocket, authenticates using a JWT,
listens for channel events, fetches recent channel history for context,
and sends prompts to the Open WebUI `/api/chat/completions` endpoint.

Trigger format in a channel:

    AI: your question here

Example:

    AI: summarize this thread

Requirements
------------
Open WebUI Version:
    Tested with Open WebUI 0.5.10

Environment Variables:
    WEBUI_URL=<your_openwebui_url>
    TOKEN=<jwt_token>

Notes
-----
- This bot requires a JWT token for websocket authentication.
- API keys (sk-...) will not work for websocket channel participation.
- The bot listens for the `events:channel` websocket event.
- Messages not beginning with "AI:" are ignored.
- The bot fetches the last HISTORY_LIMIT messages from the channel to
  provide context and will cite relevant parts of the discussion.
"""

import asyncio
import aiohttp
import socketio

from env import WEBUI_URL, TOKEN
from utils import send_message, send_typing

MODEL_ID = "your-model-id"
HISTORY_LIMIT = 50

sio = socketio.AsyncClient(logger=False, engineio_logger=False)


@sio.event
async def connect():
    print("Connected to Open WebUI.")


@sio.event
async def disconnect():
    print("Disconnected from Open WebUI.")


async def get_channel_messages(channel_id: str, limit: int = HISTORY_LIMIT) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{WEBUI_URL}/api/v1/channels/{channel_id}/messages",
            headers={"Authorization": f"Bearer {TOKEN}"},
            params={"limit": limit},
        ) as response:
            if response.status == 200:
                data = await response.json()
                # API returns messages newest-first; reverse for chronological order
                messages = data if isinstance(data, list) else data.get("messages", [])
                return list(reversed(messages))
            print(f"Failed to fetch channel history: HTTP {response.status}")
            return []


def format_history(messages: list) -> str:
    lines = []
    for msg in messages:
        user = msg.get("user", {})
        name = user.get("name") or user.get("username") or msg.get("user_id", "unknown")
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(f"{name}: {content}")
    return "\n".join(lines)


async def openai_chat_completion(messages):
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "stream": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{WEBUI_URL}/api/chat/completions",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json=payload,
        ) as response:
            if response.status == 200:
                return await response.json()

            return {
                "error": await response.text(),
                "status": response.status,
            }


def register_events():
    @sio.on("events:channel")
    async def handle_channel_event(data):
        event_data = data.get("data", {})

        if event_data.get("type") != "message":
            return

        message_data = event_data.get("data", {})
        content = (message_data.get("content") or "").strip()
        channel_id = data.get("channel_id")

        if not channel_id:
            return

        if not content.lower().startswith("ai:"):
            return

        prompt = content[3:].strip()

        if not prompt:
            return

        async def send_typing_until_complete(target_channel_id, coro):
            task = asyncio.create_task(coro)

            try:
                while not task.done():
                    await send_typing(sio, target_channel_id)
                    await asyncio.sleep(1)

                return await task

            except Exception:
                task.cancel()
                raise

        history = await get_channel_messages(channel_id)
        history_text = format_history(history)

        system_content = (
            "You are a helpful assistant responding in a shared team channel. "
            "Be concise and clear.\n\n"
            "When answering, use the conversation history below as context. "
            "If any prior messages are relevant to your answer, quote or cite them "
            "directly (e.g. \"As [Name] mentioned: '...'\").\n\n"
            f"--- Recent channel history ({len(history)} messages) ---\n"
            f"{history_text}\n"
            "--- End of history ---"
        )

        completion_task = openai_chat_completion(
            [
                {
                    "role": "system",
                    "content": system_content,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        try:
            response = await send_typing_until_complete(channel_id, completion_task)

            if response.get("choices"):
                completion = response["choices"][0]["message"]["content"]
                await send_message(channel_id, completion)

            else:
                await send_message(
                    channel_id,
                    f"Request failed. Response was: {response}",
                )

        except Exception as exc:
            await send_message(
                channel_id,
                f"Something went wrong while processing your request: {str(exc)}",
            )


async def connect_and_run():
    """Attempt a single connect + auth + wait cycle. Raises on failure."""
    if sio.connected:
        await sio.disconnect()

    print(f"Connecting to {WEBUI_URL}...")
    await sio.connect(
        WEBUI_URL,
        socketio_path="/ws/socket.io",
        transports=["websocket"],
    )
    print("Connection established.")

    await sio.call("user-join", {"auth": {"token": TOKEN}}, timeout=10)
    print("Authentication successful.")

    await sio.wait()  # blocks until disconnected


async def main():
    register_events()

    delay = 5
    max_delay = 300  # cap backoff at 5 minutes

    while True:
        try:
            await connect_and_run()
            delay = 5  # reset backoff after a successful connection
        except Exception as exc:
            print(f"Connection lost: {exc}")

        print(f"Reconnecting in {delay}s...")
        await asyncio.sleep(delay)
        delay = min(delay * 2, max_delay)


if __name__ == "__main__":
    asyncio.run(main())
