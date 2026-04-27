import base64
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDENTIALS_FILE = "credentials.json"
GMAIL_USER = "margariti@yourdomain.com"  # the Gmail address to impersonate
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    delegated = creds.with_subject(GMAIL_USER)
    return build("gmail", "v1", credentials=delegated)


def decode_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    return "(no readable body)"


def read_latest_email():
    service = get_gmail_service()

    results = service.users().messages().list(userId="me", maxResults=1, labelIds=["INBOX"]).execute()
    messages = results.get("messages", [])
    if not messages:
        print("Inbox is empty.")
        return

    msg_id = messages[0]["id"]
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    sender = headers.get("From", "(unknown sender)")
    subject = headers.get("Subject", "(no subject)")
    body = decode_body(msg["payload"])

    print(f"From:    {sender}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")


read_latest_email()
