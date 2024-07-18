
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tkinter import messagebox
import requests


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

    # Check if the user is already logged in.
    google_login, _ = check_google_login(token_file)
    if google_login:
        login_again = messagebox.askyesno("Google Login", "Do you want to login to Google again?")
        if not login_again:
            return None

    creds = None

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


def check_google_login(token_file='sheets.googleapis.com-python.json') -> (bool, str):
    """
    Check if the user is already logged in to Google services.

    Args:
        token_file (str): The path to the token file.

    Returns:
        tuple: (bool, str) True and account if the login is successful. False
        and error message otherwise.
    """
    print("Checking Google login... " + token_file)
    if not os.path.exists(token_file):
        print("Token file not found.")
        return False, "Token file not found."

    try:
        creds = Credentials.from_authorized_user_file(token_file)
        print("Credentials loaded:", creds)

        if creds and creds.valid:
            print("Credentials are valid.")
            return True, creds.account
        else:
            print("Credentials are invalid.")
            return False, "Login failed: Invalid credentials."
    except Exception as e:
        print("Error loading credentials:", str(e))
        return False, f"Login failed: {str(e)}"


def check_whatsapp_login(token_file='whatsapp_secrets.json', phone_number_key='test'):
    """
    Check if the user is logged in to WhatsApp Business API by requesting the business profile.

    Args:
        secrets_file (str): The path to the secrets file.

    Returns:
        tuple: (bool, str) True if the login is successful, and an error message otherwise.
    """
    try:
        # Load the secrets
        with open(token_file, 'r') as f:
            secrets = json.load(f)

        access_token = secrets.get('access_token')
        phone_number_id = secrets.get('phone_number_id')[phone_number_key]

        if not access_token or not phone_number_id:
            return False, "Missing access token or phone number ID in secrets file."

        url = f'https://graph.facebook.com/v20.0/{phone_number_id}/whatsapp_business_profile?fields=about,address,description,email,profile_picture_url,websites,vertical'

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return True, "Login successful."
            else:
                return False, "Unexpected response format."
        else:
            return False, f"API request failed with status code {response.status_code}: {response.text}"

    except FileNotFoundError:
        return False, "Secrets file not found."
    except json.JSONDecodeError:
        return False, "Error decoding secrets file."
    except Exception as e:
        return False, str(e)