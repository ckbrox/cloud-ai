from google.cloud import secretmanager
import json
import requests
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


class WorkdayDemoClient:
    def __init__(self, secret_id='workday-demo'):
        self.secret_id = secret_id

        self._secret: dict = None
        self._api_access_token: str = None


    def pp(self, obj):
        print(json.dumps(obj, indent=4, default=str))

    @property
    def secret(self) -> dict:
        '''
        Retrieves the Oauth secret from Google Cloud Secret Manager.
        '''
        if not self._secret:
            self._secret = get_secret(secret_id=self.secret_id) 
        return self._secret
    
    @property
    def tenant(self) -> str:
        return self.secret['tenant']
  
    @property
    def api_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_access_token}',
            'Content-Type': 'application/json'
        }
    
    @property
    def api_endpoint(self) -> str:
        return self.secret["rest_api_endpoint"]
    
    @property
    def assistant_endpoint(self) -> str:
        return self.secret['assistant_endpoint']
    

    @property
    def api_access_token(self):
        if not self._api_access_token:
            print(f'getting api access token')            
            try:
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.secret["refresh_token"],
                    'client_id': self.secret["client_id"],
                    'client_secret': self.secret["client_secret"]
                }
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                response = requests.post(self.secret["token_endpoint"], headers=headers, data=data)
                response.raise_for_status()  # Raise an exception for bad status codes

                token_data = response.json()
                self._api_access_token = token_data.get('access_token')
            except requests.exceptions.RequestException as e:
                print(f"Error fetching api access token: {e}")
                return None
        return self._api_access_token
    

    def rest_request(self, method, service, version, path, raw=False, pp=False, **kwargs):
        r = requests.request(
            method=method,
            url=f'{self.api_endpoint}/{service}/{version}/{self.tenant}/{path}',
            headers=self.api_headers,
            **kwargs
        )
        if not r.ok:
            print(r.status_code)
            self.pp(r.json())
            # r.raise_for_status()
        if raw:
            return r
        
        if pp:
            self.pp(r.json())
        try:
            return r.json()
        except:
            return r.text
