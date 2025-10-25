from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Stream, Connect
from google.cloud import secretmanager
import json
import google.auth
from google.adk.tools import ToolContext, AgentTool

_, project_id = google.auth.default()

def get_secret(secret_id, version_id="latest") -> dict:
    """
    Get a secret from Google Cloud Secret Manager.

    Args:
        project_id (str): The Google Cloud project ID.
        secret_id (str): The ID of the secret.
        version_id (str): The version of the secret (e.g., "latest", "1").

    Returns:
        str: The secret value.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    data =  response.payload.data.decode("UTF-8")
    try: 
        return json.loads(data)
    except:
        return data


class TwilioClient:
    def __init__(self, twilio_phone_number:str=None):
        self._twilio_secret = {}
        self._twilio_phone_number = twilio_phone_number

    @property
    def twilio_secret(self) -> dict:
        if not self._twilio_secret:
            self._twilio_secret = get_secret('twilio')
        return self._twilio_secret
    
    @property
    def twilio_api_key(self) -> str:
        return self.twilio_secret['api_key']
    
    @property
    def twilio_api_secret(self) -> str:
        return self.twilio_secret['api_secret']
    
    @property
    def twilio_account_sid(self) -> str:
        return self.twilio_secret['account_sid']
    
    @property
    def twilio_phone_number(self) -> str:
        if not self._twilio_phone_number:
            self._twilio_phone_number = self.twilio_secret['phone_number']
        return self._twilio_phone_number
    
    @property
    def client(self) -> Client:
        return Client(self.twilio_api_key, self.twilio_api_secret, self.twilio_account_sid)
    

    async def send_outbound_sms(self, to_number: str, message: str, tool_context: 'ToolContext'):
        """
        Send an SMS message to the specified phone number.

        Args:
            to (str): The phone number to send the message to in E.164 format (e.g., '+14155551234').
            message (str): The message to send.

        Returns:
            dict: A dictionary indicating the status of the operation.
        """
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.twilio_phone_number,
                body=message
            )

            print(f"SMS sent with SID: {message.sid}")
            return {
                'status': 'success',
                'detail': f'SMS sent with SID: {message.sid}'
            }

        except Exception as e:
            print(f"Error sending SMS: {e}")
            return {
                'status': 'error',
                'detail': f'Error sending SMS: {e}'
            }


