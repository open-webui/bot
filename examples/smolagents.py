# WARNING: This might not work in the future. Do NOT use this in production.

import asyncio
import socketio
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool


from env import WEBUI_URL, TOKEN
from utils import send_message, send_typing

search_tool = DuckDuckGoSearchTool()

MODEL_ID = "llama3.2:latest"

model = LiteLLMModel(
    model_id=f"openai/{MODEL_ID}", api_base=f"{WEBUI_URL}/api/", api_key=TOKEN
)
agent = CodeAgent(
    tools=[search_tool], model=model, additional_authorized_imports=["requests", "bs4"]
)


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
def events(user_id):
    @sio.on("channel-events")
    async def channel_events(data):
        if data["user"]["id"] == user_id:
            # Ignore events from the bot itself
            return

        if data["data"]["type"] == "message":
            print(f'{data["user"]["name"]}: {data["data"]["data"]["content"]}')

            # Send typing events every second while processing the input
            async def simulate_typing(channel_id):
                try:
                    while not processing_event.is_set():
                        await send_typing(sio, channel_id)
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass

            # Create an asyncio.Event to manage typing simulation
            processing_event = asyncio.Event()
            typing_task = asyncio.create_task(simulate_typing(data["channel_id"]))

            try:
                # Run the blocking agent.run in a non-blocking way using asyncio
                loop = asyncio.get_running_loop()
                output = await loop.run_in_executor(
                    None, agent.run, data["data"]["data"]["content"]
                )
            finally:
                # Signal that typing simulation should stop
                processing_event.set()
                # Wait for the typing task to finish
                await typing_task

            # Send the generated output as a message
            await send_message(data["channel_id"], f"{output}")


# Define an async function for the main workflow
async def main():
    try:
        print(f"Connecting to {WEBUI_URL}...")
        await sio.connect(
            WEBUI_URL, socketio_path="/ws/socket.io", transports=["websocket"]
        )
        print("Connection established!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Callback function for user-join
    async def join_callback(data):
        events(data["id"])  # Attach the event handlers dynamically

    # Authenticate with the server
    await sio.emit("user-join", {"auth": {"token": TOKEN}}, callback=join_callback)

    # Wait indefinitely to keep the connection open
    await sio.wait()


# Actually run the async `main` function using `asyncio`
if __name__ == "__main__":
    asyncio.run(main())
