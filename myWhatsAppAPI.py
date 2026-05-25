from datetime import datetime
import logging
import requests
import os
from connection import WhatsAppConnection

_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


class MyWhatsAppAPI:
    def __init__(self, connection: WhatsAppConnection,
                 api_version: str = "v25.0",
                 log_file: str = "wp_api.log",
                 media_log_file: str = "wp_media_uploads.log"):
        """
        Initialize the WhatsApp API.

        Args:
            connection (WhatsAppConnection): Active connection with credentials.
            api_version (str): Meta Graph API version (e.g. "v25.0").
            log_file (str): Path for the API call log file.
            media_log_file (str): Path for the media upload log file.
        """
        self.api_version = api_version
        self.media_log_file = media_log_file
        self.access_token = connection.get_access_token()
        self.phone_number_id = connection.get_phone_number_id()

        self.logger = logging.getLogger("whatsapp_api")
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.logger.info(
            f"WhatsApp API initialised for {connection.get_phone_number_key()} "
            f"— API {self.api_version}"
        )

    def upload_media(self, file_path: str, file_media_type: str) -> str | None:
        """
        Upload media to WhatsApp and return the media ID.

        Args:
            file_path (str): Path to the media file.
            file_media_type (str): MIME type (e.g. "image/png").

        Returns:
            str: Media ID, or None on failure.
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
                self.logger.info(f"Media uploaded: {media_id}")
                with open(self.media_log_file, 'a') as log_file:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_file.write(
                        f"{timestamp} - {self.phone_number_id}"
                        f" - {file_path} - {media_id}\n"
                    )
                return media_id
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to upload media: {e}")
                return None

    def send_media_template(self, to_phone_number: str, media_id: str,
                            template_media_type: str, template_name: str,
                            language_code: str,
                            template_parameters: list[dict[str, str]]) -> bool:
        """
        Send a WhatsApp media template message.

        Args:
            to_phone_number (str): Recipient phone number (with country code).
            media_id (str): ID of the previously uploaded media.
            template_media_type (str): Media type ('IMAGE', 'VIDEO', etc.).
            template_name (str): Name of the approved WhatsApp template.
            language_code (str): Language code (e.g. "it").
            template_parameters (list): Body parameters for the template.

        Returns:
            bool: True if sent successfully.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
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
                                template_media_type.lower(): {"id": media_id},
                            }
                        ],
                    },
                    {"type": "body", "parameters": template_parameters},
                ],
            },
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            self.logger.info(
                f"Media template '{template_name}' sent to {to_phone_number}"
            )
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send media template to {to_phone_number}: {e}")
            return False

    def send_text_template(self, to_phone_number: str, template_name: str,
                           language_code: str,
                           template_header_parameters: list[dict[str, str]],
                           template_body_parameters: list[dict[str, str]]) -> bool:
        """
        Send a WhatsApp text template message with header and body parameters.

        Args:
            to_phone_number (str): Recipient phone number (with country code).
            template_name (str): Name of the approved WhatsApp template.
            language_code (str): Language code (e.g. "it").
            template_header_parameters (list): Header component parameters.
            template_body_parameters (list): Body component parameters.

        Returns:
            bool: True if sent successfully.
        """
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
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
                    {"type": "body",   "parameters": template_body_parameters},
                ],
            },
        }
        try:
            self.logger.info(f"Sending text template '{template_name}' to {to_phone_number}")
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            self.logger.info(f"Text template sent to {to_phone_number}")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Failed to send text template to {to_phone_number}: {e}"
            )
            return False
