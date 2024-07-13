
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tkinter import messagebox




def google_login(creds_file='google_secrets.json',
                 token_file='sheets.googleapis.com-python.json'):
    """
    Try a login to Google services using an already saved token. If the
    token is expired, the user will be asked to login again and the new
    token will be saved.

    Args:
        creds_file (str): The path to the client secrets file.
        token_file (str): The path to the token file.

    Returns:
        Credentials: The authenticated credentials.
    """
    # Authorization for both Google Sheets and Google Drive (like pygsheets).
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']

    creds = None

    # Load credentials from token file if it exists.
    if os.path.exists(token_file):
        # Ask with a message box if the user wants to login again.
        # If the user says no, return the existing credentials.
        login_again = messagebox.askyesno("Google Login", "Do you want to login to Google again?")
        if not login_again:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        else:
            os.remove(token_file)

    message = "You are going to be prompted in the browser.\nFollow the instructions and authorize the app."
    messagebox.showinfo("OAuth Login", message)

    # If there are no valid credentials, prompt the user to log in.
    # Add instructions to the message box not in the terminal.
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


def check_google_login(token_file='sheets.googleapis.com-python.json'):
    """
    Check if the user is already logged in to Google services.

    Args:
        token_file (str): The path to the token file.

    Returns:
        bool: True if the user is already logged in, False otherwise.
    """
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file)
        return creds.valid
    return False
