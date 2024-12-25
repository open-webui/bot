import requests
from env import WEBUI_URL, TOKEN


def send_message(channel_id: str, message: str):
    url = f"{WEBUI_URL}/api/v1/channels/{channel_id}/messages/post"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    data = {"content": message}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()
