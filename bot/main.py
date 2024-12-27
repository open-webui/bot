import asyncio
import socketio
from env import WEBUI_URL, TOKEN
from utils import send_message, send_typing

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
            await send_typing(sio, data["channel_id"])
            await asyncio.sleep(1)  # Simulate a delay
            await send_message(data["channel_id"], "Pong!")


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
