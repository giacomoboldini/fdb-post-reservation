
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession, Request



def google_login(creds_file='secrets.json',
                token_file='sheets.googleapis.com-python.json'):
    """
    Try a login to Google services using an already saved token (by pygsheets).
    If the token is expired, the user will be asked to login again and the
    new token will be saved.

    Args:
        creds_file (str): The path to the client secrets file.
        token_file (str): The path to the token file.

    Returns:
        Credentials: The authenticated credentials.
    """
    # Same scopes as pygsheets.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive']

    creds = None

    # Load credentials from token file if it exists.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file,
                                                            SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds
