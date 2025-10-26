import requests, json
import google.auth
from google.cloud import resourcemanager_v3
from google.auth.credentials import Credentials
from google.cloud import secretmanager
from google.genai import Client, types
from google.cloud.storage import Client as StorageClient
from google.cloud.firestore_v1 import Client as FirestoreClient


class GoogleCloudService:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._access_token = None
        self._credentials, self.project_id = google.auth.default()
        self._project_number = None
        self._genai_client: Client = None
        self._storage_client: StorageClient = None
        self._db: FirestoreClient = None
        
        self._agentspace_config: dict = {}

        self.LITE_MODEL = 'gemini-flash-lite-latest'
        self.MODEL = 'gemini-flash-latest'
        self.PRO_MODEL = 'gemini-2.5-pro'
    
    def pp(self, obj):
        print(json.dumps(obj, indent=4, default=str))

    @property
    def credentials(self) -> Credentials:
        return self._credentials
    
    @property
    def db(self) -> FirestoreClient:
        if not self._db:
            try:
                import firebase_admin
                firebase_admin.initialize_app()
            except:
                pass
            self._db = FirestoreClient()    
        return self._db
    
    @property
    def genai_client(self) -> Client:
        if not self._genai_client:
            self._genai_client = Client(vertexai=True, project=self.project_id, location='global')
        return self._genai_client
    
    @property
    def storage_client(self):
        if not self._storage_client:
            self._storage_client = StorageClient()
        return self._storage_client

    
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
    
    @property
    def agentspace_config(self):
        if not self._agentspace_config:
            agentspace_config = self.db.document(f'agentspace/default').get()
            if agentspace_config.exists:
                self._agentspace_config = agentspace_config.to_dict()
        return self._agentspace_config


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
        

def pp(obj):
    if isinstance(obj, dict) or isinstance(obj, list):
        print(json.dumps(obj, indent=4, default=str))
    elif isinstance(obj, types.GenerateContentResponse):
        print(json.dumps(obj.model_dump(), indent=4, default=str))
    else:
        print(obj)
        

    
 