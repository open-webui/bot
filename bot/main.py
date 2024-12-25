import socketio
from env import WEBUI_URL, TOKEN
from utils import send_message

# Create a Socket.IO client instance
sio = socketio.Client(logger=False, engineio_logger=False)


# Event handlers
@sio.event
def connect():
    print("Connected!")


@sio.event
def disconnect():
    print("Disconnected from the server!")


def events(sio, user_id):
    @sio.on("channel-events")
    def channel_events(data):
        if data["user"]["id"] == user_id:
            # Ignore events from the bot itself
            return

        print("Channel events:", data)
        send_message(data["channel_id"], "Pong!")


try:
    print(f"Connecting to {WEBUI_URL}...")
    sio.connect(WEBUI_URL, socketio_path="/ws/socket.io", transports=["websocket"])
    print("Connection established!")
except Exception as e:
    print(f"Failed to connect: {e}")


def join_callback(data):
    events(sio, data["id"])


# Authenticate with the server
sio.emit("user-join", {"auth": {"token": TOKEN}}, callback=join_callback)
sio.wait()
