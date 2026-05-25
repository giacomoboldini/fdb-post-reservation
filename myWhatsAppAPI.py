from datetime import datetime
import json
import logging
import requests
import os
from connection import WhatsAppConnection

API_VERSION = "v25.0"

logging.basicConfig(filename='wp_api.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class MyWhatsAppAPI:
    def __init__(self, connection: WhatsAppConnection, api_version: str = API_VERSION):
        """
        Initialize the WhatsApp API.

        Args:
            connection (WhatsAppConnection): Connection object containing credentials.
            api_version (str): API version to use.
        """
        self.api_version = api_version
        self.access_token = connection.get_access_token()
        self.phone_number_id = connection.get_phone_number_id()
        logging.info(
            f"WhatsApp API initialized for phone number "
            f"{connection.get_phone_number_key()} with API version {self.api_version}"
        )

    def upload_media(self, file_path: str, file_media_type: str) -> str:
        """
        Upload media to WhatsApp and return the media ID.

        Args:
            file_path (str): Path to the media file.
            file_media_type (str): Type of media file.

        Returns:
            str: ID of the uploaded media file or None if the upload failed.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/media"
        headers = {'Authorization': f'Bearer {self.access_token}'}

        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file, file_media_type)}
            data = {'messaging_product': 'whatsapp', 'type': file_media_type}

            try:
                response = requests.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                media_id = response.json().get('id')
                logging.info(f"Media uploaded successfully: {media_id}")
                with open('wp_media_uploads.log', 'a') as log_file:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_file.write(
                        f"{timestamp} - {self.phone_number_id} - {file_path} - {media_id}\n"
                    )
                return media_id
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to upload media: {e}")
                return None

    def send_media_template(self, to_phone_number: str, media_id: str,
                            template_media_type: str, template_name: str,
                            language_code: str,
                            template_parameters: list[dict[str, str]]) -> bool:
        """
        Send a WhatsApp media message using a template.

        Args:
            to_phone_number (str): Phone number to send the message to.
            media_id (str): ID of the uploaded media file.
            template_media_type (str): Media type ('IMAGE', 'VIDEO', etc.).
            template_name (str): Name of the WhatsApp template.
            language_code (str): Language code of the template.
            template_parameters (list): Body parameters for the template.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": template_media_type.lower(),
                                template_media_type.lower(): {"id": media_id}
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": template_parameters
                    }
                ]
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            logging.info(
                f"Media message ({template_media_type}:{media_id}) "
                f"sent successfully to {to_phone_number}"
            )
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send media message: {e}")
            return False

    def send_text_template(self, to_phone_number: str, template_name: str,
                           language_code: str,
                           template_header_parameters: list[dict[str, str]],
                           template_body_parameters: list[dict[str, str]]) -> bool:
        """
        Send a WhatsApp text template message with header and body parameters.

        Args:
            to_phone_number (str): Phone number to send the message to.
            template_name (str): Name of the WhatsApp template.
            language_code (str): Language code of the template.
            template_header_parameters (list): Parameters for the header component.
            template_body_parameters (list): Parameters for the body component.

        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [
                    {"type": "header", "parameters": template_header_parameters},
                    {"type": "body", "parameters": template_body_parameters}
                ]
            }
        }

        try:
            logging.info(f"Sending template message to {to_phone_number}")
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            logging.info(f"Template message sent successfully to {to_phone_number}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send template message to {to_phone_number}: {e}")
            return False
