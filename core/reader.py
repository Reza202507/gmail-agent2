# core/reader.py

import base64
from googleapiclient.errors import HttpError


def get_latest_emails(service, max_results=6, query=None):
    """
    Fetches the latest emails from the Gmail inbox (optionally filtered by a query),
    and returns a list of dicts containing message_id, thread_id, sender, subject, body.
    """
    try:
        # Prepare the list request
        list_kwargs = {'userId': 'me', 'labelIds': ['INBOX'], 'maxResults': max_results}
        if query:
            list_kwargs['q'] = query

        response = service.users().messages().list(**list_kwargs).execute()
        messages = response.get('messages', [])
        emails = []

        for msg in messages:
            # Retrieve full message
            msg_detail = service.users().messages().get(
                userId='me', id=msg['id'], format='full'
            ).execute()

            # Extract headers
            payload = msg_detail.get('payload', {})
            headers = payload.get('headers', [])
            subject = ''
            sender = ''
            for header in headers:
                name = header.get('name', '').lower()
                if name == 'subject':
                    subject = header.get('value', '')
                elif name == 'from':
                    sender = header.get('value', '')

            # Extract body (text/plain)
            body = ''
            parts = payload.get('parts', [])
            if parts:
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            # Append the email record with both message_id and thread_id
            emails.append({
                'message_id': msg_detail.get('id'),
                'thread_id': msg_detail.get('threadId'),
                'subject': subject,
                'body': body,
                'sender': sender
            })

        return emails

    except HttpError as error:
        print(f"⚠️ An error occurred in get_latest_emails: {error}")
        return []
