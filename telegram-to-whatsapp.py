import os
import pickle
import io
import asyncio
import re
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from telethon import TelegramClient, events

# Load environment variables
load_dotenv()

credentials = {
    "installed": {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "redirect_uris": ["http://localhost"]
    }
}

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
WHATSAPP_CHAT_ID = os.getenv('WHATSAPP_CHAT_ID')

# If modifying these SCOPES, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Function to authenticate with Google Drive
def get_gdrive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

# Function to download the session file from Google Drive
def download_file_from_drive(service, file_id, destination_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    print(f"Session file downloaded to {destination_path}")

# Function to upload the session file to Google Drive
def upload_file_to_drive(service, file_name, file_path, mime_type='application/octet-stream'):
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File {file_name} uploaded to Drive with ID: {file.get('id')}")
    return file.get('id')

# Initialize Google Drive service
service = get_gdrive_service()
session_file_id = "1DAbwCF2pep_F5d4V8hilhJzouCgKGBrI"  # Replace with your actual session file ID in Google Drive
session_file_path = 'session.session'  # Modify this as needed

# Check if session file exists locally, if not download it from Google Drive
if os.path.exists(session_file_path):
    print("Session file found locally.")
else:
    print("Session file not found locally. Downloading from Google Drive.")
    download_file_from_drive(service, session_file_id, session_file_path)

# Initialize Telegram client
client = TelegramClient(session_file_path, API_ID, API_HASH)

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
    print(f"Match: {match}")

    if match:
        link_text = match.group(1)
        link_url = match.group(2)
        formatted_link = f"*{link_text}*\n{link_url}"
        print(f"Formatted link: {formatted_link}")
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

    try:
        await client.run_until_disconnected()
    finally:
        # Upload the session file back to Google Drive
        upload_file_to_drive(service, 'session.session', session_file_path)

if __name__ == '__main__':
    asyncio.run(main())
