# connection.py

import json
import os
import pickle
from tkinter import messagebox
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from googleapiclient.discovery import build


class Connection:
    """
    Base class to manage the state of the connection.
    """
    def __init__(self):
        self.state = False
        self.message = ""

    def login(self):
        raise NotImplementedError("Subclasses should implement this method")

    def connect(self):
        raise NotImplementedError("Subclasses should implement this method")

    def get_state(self):
        self.login()
        return self.state

    def get_message(self):
        self.login()
        return self.message


class GoogleConnection(Connection):
    """
    Handle Google OAuth login and connection status.
    """
    def __init__(self, creds_file='google_secrets.json', token_file='token.json'):
        super().__init__()
        self.creds_file = creds_file
        self.token_file = token_file
        self.scopes = ['openid',
                       'https://www.googleapis.com/auth/userinfo.email',
                       'https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive']
        self.creds = None
        self.account = None

    def set_creds_file(self, creds_file):
        """
        Setter for the credentials file path.
        """
        self.creds_file = creds_file

    def get_creds_file(self):
        """
        Getter for the credentials file path.
        """
        return self.creds_file

    def set_token_file(self, token_file):
        """
        Setter for the token file path.
        """
        self.token_file = token_file

    def get_token_file(self):
        """
        Getter for the token file path.
        """
        return self.token_file

    def get_credentials(self):
        """
        Getter for the Google credentials.
        """
        return self.creds

    def login(self, creds_file=None, token_file=None):
        """
        Handle Google login using OAuth2 and update the connection state and message.
        Allows overriding of creds_file and token_file.
        """
        creds_file = creds_file or self.creds_file
        token_file = token_file or self.token_file

        try:
            # Check if token exists and is valid
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            else:
                self.creds = None

            if self.creds and self.creds.valid:
                self.state = True
                user_info_service = build('oauth2', 'v2', credentials=self.creds)
                self.account = user_info_service.userinfo().get().execute().get('email')
                self.message = "Connected as " + self.account
            elif not self.creds or not self.creds.valid:
                # Refresh the token if expired
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    # Save the refreshed credentials
                    with open(token_file, 'wb') as token:
                        pickle.dump(self.creds, token)
                    self.state = True
                    self.message = "Successfully refreshed Google credentials."
            else:
                self.state = False
                self.message = "Google connection failed."

        except Exception as e:
            self.state = False
            self.message = f"An error occurred during Google login: {str(e)}"

    def connect(self, creds_file=None, token_file=None):
        """
        Attempts the login and relaunches the login process if it fails.
        Updates the connection state and message based on the result.
        Allows overriding of creds_file and token_file.
        """
        creds_file = creds_file or self.creds_file
        token_file = token_file or self.token_file

        # First attempt to log in with existing credentials
        self.login(creds_file, token_file)

        if self.state:
            # If the login is successful, show the success message
            message = f"Successfully connected to Google as {self.account}."
            messagebox.showinfo("Google Connection", message)
            return

        # If login failed, prompt for the OAuth login process
        message = "You are going to be prompted in the browser.\n" \
                "Follow the instructions and authorize the app."
        messagebox.showinfo("OAuth Login", message)

        try:
            # Start the OAuth flow to authenticate the user
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, self.scopes)
            self.creds = flow.run_local_server(port=0)

            # Save the new credentials to the token file for future use
            with open(token_file, 'wb') as token:
                pickle.dump(self.creds, token)
                print(f"Credentials saved to {token_file}")

            self.state = True
            user_info_service = build('oauth2', 'v2', credentials=self.creds)
            self.account = user_info_service.userinfo().get().execute().get('email')
            self.message = "Connected as " + self.account

            # Save the new file paths (in case they were changed)
            self.set_creds_file(creds_file)
            self.set_token_file(token_file)

        except Exception as e:
            # Handle any errors during the OAuth flow or token saving
            self.state = False
            self.message = f"An error occurred during Google login: {str(e)}"
            messagebox.showerror("OAuth Error", self.message)


class WhatsAppConnection(Connection):
    """
    Handle WhatsApp API login and connection status.
    """
    def __init__(self, token_file='whatsapp_secrets.json', phone_number_key='test'):
        super().__init__()
        self.token_file = token_file
        self.phone_number_key = phone_number_key
        self.access_token = None
        self.phone_number_id = None

    def set_token_file(self, token_file):
        """
        Setter for the WhatsApp token file path.
        """
        self.token_file = token_file

    def get_token_file(self):
        """
        Getter for the WhatsApp token file path.
        """
        return self.token_file

    def set_phone_number_key(self, phone_number_key):
        """
        Setter for the phone number key in the token file.
        """
        self.phone_number_key = phone_number_key

    def get_phone_number_key(self):
        """
        Getter for the phone number key in the token file.
        """
        return self.phone_number_key

    def login(self, token_file=None, phone_number_key=None):
        """
        Handle WhatsApp login and update the connection state and message.
        Allows overriding of token_file and phone_number_key.
        """

        token_file = token_file or self.token_file
        phone_number_key = phone_number_key or self.phone_number_key

        try:
            # Load the secrets from the token file
            with open(self.token_file, 'r') as f:
                secrets = json.load(f)

            self.access_token = secrets.get('access_token')
            self.phone_number_id = secrets.get('phone_number_id', {}).get(self.phone_number_key)

            # Check if both access token and phone number ID are present
            if not self.access_token or not self.phone_number_id:
                self.state = False
                self.message = "Missing access token or phone number ID in secrets file."
                return

            # Make an API call to check login status
            url = f'https://graph.facebook.com/v20.0/{self.phone_number_id}/whatsapp_business_profile?fields=about,address,description,email,profile_picture_url,websites,vertical'

            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    self.state = True
                    self.message = "Login successful."
                    self.set_token_file(token_file)
                    self.set_phone_number_key(phone_number_key)
                else:
                    self.state = False
                    self.message = "Unexpected response format."
            else:
                self.state = False
                self.message = f"API request failed with status code {response.status_code}: {response.text}"

        except FileNotFoundError:
            self.state = False
            self.message = "Secrets file not found."
        except json.JSONDecodeError:
            self.state = False
            self.message = "Error decoding secrets file."
        except Exception as e:
            self.state = False
            self.message = f"An error occurred during WhatsApp login: {str(e)}"

    def connect(self, token_file=None, phone_number_key=None):
        """
        Attempts to login and relaunches the login process if it fails.
        Updates the connection state and message based on the result.
        Allows overriding of token_file and phone_number_key.
        """
        token_file = token_file or self.token_file
        phone_number_key = phone_number_key or self.phone_number_key

        self.login(token_file, phone_number_key)

        if self.state:
            self.state = True
            self.message = "WhatsApp connection successful."
            return

        # If login failed, prompt for the configuration message
        message = "You need to configure WhatsApp API and then create a JSON file in the format:\n" + \
                  "{\n" + \
                  "  \"access_token\": \"[access_token]\"\n" + \
                  "  \"account_id\": \"[account_id]\"\n" + \
                  "  \"phone_number_id\": {\n" + \
                  "    \"id1\": \"[phone_number_id1]\"\n" + \
                  "    ...\n" + \
                  "  }\n" + \
                  "}"
        messagebox.showinfo("WhatsApp API", message)

        self.state = False
        self.message = "WhatsApp connection failed. Please check your credentials."
