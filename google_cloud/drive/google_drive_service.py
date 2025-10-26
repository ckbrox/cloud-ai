from google_cloud import GoogleCloudService
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import os
import json
from typing import Generator
from pymediainfo import MediaInfo
from datetime import datetime, UTC


class GoogleWorkspaceService:
    def __init__(self, gc: GoogleCloudService = None):
        self.gc: GoogleCloudService = gc or GoogleCloudService()
        self._service_account: dict = None
        self.scopes: list[str] = ["https://www.googleapis.com/auth/drive"]
        
        self._drive: Resource = None
        self._docs: Resource = None
        self._slides: Resource = None

    
    @property
    def service_account(self) -> dict:
        if not self._service_account:
            self._service_account = self.gc.get_secret('docs-sa')
        return self._service_account
    
    @property
    def service_account_email(self) -> str:
        return self.service_account.get('client_email', None)
    
    @property
    def credentials(self):
        return service_account.Credentials.from_service_account_info(
            self.service_account, scopes=self.scopes
        )

    @property
    def drive(self) -> Resource:
        if not self._drive:
            creds = service_account.Credentials.from_service_account_info(
                self.service_account, scopes=self.scopes
            )
            self._drive = build('drive', 'v3', credentials=creds)
        return self._drive
    
    @property
    def docs(self) -> Resource:
        if not self._docs:
            creds = service_account.Credentials.from_service_account_info(
                self.service_account, scopes=self.scopes
            )
            self._docs = build('docs', 'v1', credentials=creds)
        return self._docs
    
    @property
    def slides(self) -> Resource:
        if not self._slides:
            self._slides = build('slides', 'v1', credentials=self.credentials)
        return self._slides
    
    
    def get_file(self, file_id: str) -> 'GoogleDriveFile':
        return GoogleDriveFile.from_file_id(google_workspace_service=self, file_id=file_id)
    
    def get_files(self, folder_id: str) -> list['GoogleDriveFile']:
        query_string = f"'{folder_id}' in parents"
        files = self.drive.files().list(q=query_string, fields="nextPageToken, files(id, name, mimeType, description, createdTime)").execute()
        return [GoogleDriveFile(google_workspace_service=self, **file) for file in files.get('files', [])]
    
    def get_files_with_query(self, query_string: str) -> list['GoogleDriveFile']:
        files = self.drive.files().list(q=query_string, fields="nextPageToken, files(id, name, mimeType, description, createdTime)").execute()
        return [GoogleDriveFile(google_workspace_service=self, **file) for file in files.get('files', [])]

    def download_chunks(self, file_id: str) -> Generator[bytes, None, None]:
        """
        Lazily downloads a file from Google Drive, yielding it in chunks.

        The download is performed as you iterate over the returned generator,
        making it memory-efficient for large files.

        Args:
            file_id: The ID of the file to download.

        Yields:
            bytes: Chunks of the file's content.
        """
        request = self.drive.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
            yield fh.getvalue()
            # Reset the buffer for the next chunk.
            fh.seek(0)
            fh.truncate(0)


    def download_file(self, file_id) -> io.BytesIO:
        request = self.drive.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        
        fh.seek(0)
        return fh
    
    
    def create_google_doc_from_markdown(self, title:str, markdown: str, email_address: str):
        from .google_doc import GoogleDoc
        return GoogleDoc.new_from_markdown(self.credentials, self.drive, title, markdown, email_address)
    
    
    


class GoogleDriveFile:
    def __init__(self, google_workspace_service: GoogleWorkspaceService, **kwargs):
        self.google_workspace_service: GoogleWorkspaceService = google_workspace_service
        self._kwargs = kwargs

        self._file: io.BytesIO = None
        self._resolution: tuple[int, int] = None

        self._slide = None


    def format_file_id(file_id_or_uri:str):
        if '/d/' in file_id_or_uri:
            return file_id_or_uri.split('/d/')[1].split('/')[0]
        return file_id_or_uri
    
    
    @classmethod
    def from_file_id(cls, google_workspace_service: GoogleWorkspaceService, file_id: str):
        file_id = cls.format_file_id(file_id)
        file = google_workspace_service.drive.files().get(fileId=file_id).execute()
        return cls(google_workspace_service=google_workspace_service, **file)
    
    @property
    def id(self) -> str:
        return self._kwargs.get('id', None)

    @property
    def name(self) -> str:
        return self._kwargs.get('name', None)

    @property
    def mime_type(self) -> str:
        return self._kwargs.get('mimeType', None)
    
    @property
    def created_time(self) -> datetime:
        date_string = self._kwargs.get('createdTime')
        if date_string:
            date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
            return date.astimezone(UTC)
    
    @property
    def doc(self):
        if self.mime_type == 'application/vnd.google-apps.document':
            from .google_doc import GoogleDoc
            return GoogleDoc(self)

    @property
    def sheet(self):
        if self.mime_type == 'application/vnd.google-apps.spreadsheet':
            from .google_sheet import GoogleSheet
            return GoogleSheet(self)
        
    @property
    def slide(self):
        from .google_slide import Presentation
        if not self._slide:
            if self.mime_type == 'application/vnd.google-apps.presentation':
                self._slide = Presentation.from_drive_file(self)
        return self._slide


    @property
    def video(self):
        return

    def __repr__(self):
        return f'DriveFile(id={self.id}, name={self.name}, mime_type={self.mime_type})'
    
    @property
    def file(self) -> io.BytesIO:
        if not self._file:
            if self.mime_type == 'application/vnd.google-apps.document':
                self._file = self.download_google_doc_as_pdf()
            elif self.mime_type == 'application/vnd.google-apps.spreadsheet':
                self._file = self.download_google_spreadsheet_as_csv()
            else:
                request = self.google_workspace_service.drive.files().get_media(fileId=self.id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download %d%%." % int(status.progress() * 100))
                
                fh.seek(0)
                self._file = fh
        self._file.seek(0)
        return self._file
    
    
    @property
    def file_mime_type(self) -> str:
        if self.mime_type == 'application/vnd.google-apps.document':
            return 'application/pdf'
        elif self.mime_type == 'application/vnd.google-apps.spreadsheet':
            return 'text/csv'
        return self.mime_type

    
    
    
    def upload_file(self, file_bytes:bytes, mime_type:str, share_with_email: str = None):
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype=mime_type,
            resumable=True,
        )
        file = (
            self.google_workspace_service.drive.files()
            .create(body=self._kwargs, media_body=media, fields="id")
            .execute()
        )
        file_id = file.get("id")

        try:
            permission = {"type": "user", "role": "writer", "emailAddress": share_with_email}
            self.google_workspace_service.drive.permissions().create(fileId=file_id, body=permission).execute()
            print(f"Shared the file with {share_with_email}")
        except HttpError as error:
            print(f"An error occurred while sharing the file: {error}")
        
        return file_id