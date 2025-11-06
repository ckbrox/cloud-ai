


import json
import google.auth
from google.cloud import resourcemanager_v3
from google.auth.credentials import Credentials
from google.cloud import secretmanager


class GoogleCloudService:
    def __init__(self, oauth_secret_id='ckb-google-oauth', oauth_creds_secret_id='ckb-google-oauth-creds', **kwargs):
        self._kwargs = kwargs
        self._oauth_secret_id = oauth_secret_id
        self._oauth_creds_secret_id = oauth_creds_secret_id
        self._access_token = None
        self._credentials, self.project_id = google.auth.default()
        self._project_number = None

        self._ckb_oauth_credentials: dict = None
    
    def pp(self, obj):
        print(json.dumps(obj, indent=4, default=str))

    @property
    def credentials(self) -> Credentials:
        return self._credentials
    

    @property
    def oauth_credentials(self) -> dict:
        if not self._ckb_oauth_credentials:
            self._ckb_oauth_credentials = self.get_secret(self._oauth_secret_id)['web']
        return self._ckb_oauth_credentials
    
    def update_oauth_credentials(self, oauth_credentials: dict):
        return self.add_secret_version(self._oauth_creds_secret_id, oauth_credentials)
    
    @property
    def access_token(self):
        if not self._access_token:
            # Can i generate an access token using the google auth library?
            if self.credentials and self.credentials.valid:
                self.credentials.refresh(google.auth.transport.requests.Request())
                self._access_token = self.credentials.token
            elif self.credentials and not self.credentials.valid and self.credentials.expired:
                 self.credentials.refresh(google.auth.transport.requests.Request())
                 self._access_token = self.credentials.token
        return self._access_token

    @property
    def project_number(self):
        if not self._project_number:
            client = resourcemanager_v3.ProjectsClient(credentials=self.credentials)

            # The project name is the "display_name" in the API
            query = f'displayName:"{self.project_id}"'
            request = resourcemanager_v3.SearchProjectsRequest(query=query)
            
            project_found = None
            for project in client.search_projects(request=request):
                if project.display_name == self.project_id:
                    project_found = project
                    break # Found the exact match

            if project_found:
                # The project number is part of the full resource name 'projects/PROJECT_NUMBER'
                self._project_number = project_found.name.split('/')[-1]
            else:
                return None
        return self._project_number
    

    def get_secret(self, secret_id, version_id="latest") -> dict:
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
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        data =  response.payload.data.decode("UTF-8")
        try: 
            return json.loads(data)
        except:
            return data
        

    def add_secret_version(self, secret_id, secret_value: dict):
        """
        Add a new version of a secret to Google Cloud Secret Manager.
        """
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}"
        secret_value = json.dumps(secret_value)
        response = client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        return response
        

 