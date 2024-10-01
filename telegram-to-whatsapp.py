import os
import re
import requests
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
WHATSAPP_CHAT_ID = os.getenv('WHATSAPP_CHAT_ID')

# Initialize Telegram client
client = TelegramClient('session', API_ID, API_HASH)

@client.on(events.NewMessage())
async def handle_new_message(event):
    chat_id = event.chat_id
        
    if chat_id != CHANNEL_ID:
        return
    
    # Print all incoming messages
    message_text = event.message.text
    print(f"Incoming message: {message_text}")
    
    link_pattern = r'\[(.*?)\]\((.*?)\)'
    match = re.search(link_pattern, message_text)
    
    if match:
        link_text = match.group(1)
        link_url = match.group(2)
        formatted_link = f"*{link_text}*\n{link_url}"
        message_to_send = message_text.replace(match.group(0), formatted_link)
        print(f"Message to send: {message_to_send}")
        
    else:
        # No link found; send the original message
        message_to_send = message_text

    # Forward all messages to WhatsApp
    payload = {
        "chatId": WHATSAPP_CHAT_ID,
        "message": message_to_send
    }

    try:
        response = requests.post(WHATSAPP_API_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"Message forwarded. API response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error forwarding message: {e}")

async def main():
    await client.start(phone=PHONE_NUMBER)
    print("Client Created")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
