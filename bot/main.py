import asyncio
import socketio
import aiohttp
import json
from env import WEBUI_URL, TOKEN, OPENROUTER_API_KEY, OPENROUTER_API_URL
from utils import send_message, send_typing

# Create a single session for all API calls
session = None

async def get_session():
    global session
    if session is None:
        session = aiohttp.ClientSession()
    return session

async def cleanup():
    global session
    if session:
        await session.close()
        session = None

async def call_openrouter(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8080",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": message}]
    }
    
    try:
        session = await get_session()
        async with session.post(OPENROUTER_API_URL, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                print(f"OpenRouter API error: {error_text}")
                return f"Error: Unable to get response from AI (Status {response.status})"
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return "Error: Unable to connect to AI service"

# Create an asynchronous Socket.IO client instance
sio = socketio.AsyncClient(logger=False, engineio_logger=False)


# Event handlers
@sio.event
async def connect():
    print("Connected!")


@sio.event
async def disconnect():
    print("Disconnected from the server!")


# Define a function to handle channel events
# Keep track of processed message IDs to avoid duplicates
processed_messages = set()

@sio.on("channel-events")
async def on_channel_event(data):
    try:
        print(f"Received event: {data}")
        
        if not isinstance(data, dict) or "data" not in data:
            return
            
        if data["data"]["type"] == "message":
            message_id = data["data"]["data"].get("id")
            if message_id in processed_messages:
                print(f"Skipping already processed message: {message_id}")
                return
                
            # Get the message content and channel ID
            message_content = data["data"]["data"]["content"]
            channel_id = data["channel_id"]
            
            # Debug logging
            print(f"Received message: {message_content}")
            print(f"From user ID: {data['user']['id']}")
            print(f"Bot ID: {sio.user_id}")
            print(f"Ends with AI: {message_content.strip().upper().endswith('AI')}")
            
            # Only respond to messages ending with AI (case-insensitive)
            if (message_content and channel_id and 
                "user" in data and 
                data["user"]["id"] != sio.user_id and
                message_content.strip().upper().endswith("AI")):
                
                print(f'Processing AI request from {data["user"]["name"]}: {message_content}')
                print(f'Responding in channel: {channel_id}')
                
                # Remove the "AI" suffix and any trailing whitespace
                query = message_content.strip()[:-2].strip()
                if query:  # Only proceed if there's a message after removing "AI"
                    await send_typing(sio, channel_id)
                try:
                    response = await call_openrouter(query)
                    await send_message(channel_id, response)
                except Exception as e:
                    print(f"Error calling OpenRouter API: {e}")
                    await send_message(channel_id, "Sorry, I'm unable to get a response from the AI service right now. Please try again later.")
            
            if message_id:
                processed_messages.add(message_id)
    except Exception as e:
        print(f"Error handling event: {e}")


# Define an async function for the main workflow
async def main():
    try:
        print(f"Connecting to {WEBUI_URL}...")
        await sio.connect(
            WEBUI_URL, socketio_path="/ws/socket.io", transports=["websocket"]
        )
        print("Connection established!")
        
        # Authenticate with the server
        print("Authenticating with server...")
        response = await sio.call("user-join", {"auth": {"token": TOKEN}})
        sio.user_id = response["id"]  # Store user ID for later use
        print(f"Authentication successful. User ID: {sio.user_id}")
        
        # Wait indefinitely to keep the connection open
        await sio.wait()
    except Exception as e:
        print(f"Failed to connect/authenticate: {e}")
        return


# Actually run the async `main` function using `asyncio`
if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Ensure we clean up the session
        if session:
            asyncio.run(cleanup())
