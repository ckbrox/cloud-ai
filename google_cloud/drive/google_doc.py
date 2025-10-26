from googleapiclient.discovery import build, Resource
from google_cloud import GoogleCloudService
import mistune
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
from googleapiclient.errors import HttpError
from .google_drive_service import GoogleDriveFile

class IndexRange:
    def __init__(self, start: int, end: int=None):
        self.start = start
        self.end = end
    

class GoogleDoc():
    def __init__(self, drive_file: GoogleDriveFile, **kwargs):
        self.drive_file = drive_file
        self._kwargs = kwargs
        self._docs: Resource = None
        self._document: Resource = None
        self._pdf: io.BytesIO = None
        self._markdown: str = None
    
    @property
    def id(self):
        return self.drive_file.id
    
    def refresh_doc(self):
        self._document = None
        self._markdown = None
        self._pdf = None 
        
    @property
    def url(self):
        return f"https://docs.google.com/document/d/{self.drive_file.id}"
    
    @property
    def docs(self) -> Resource:
        return self.drive_file.google_workspace_service.docs
    
        if not self._docs:
            self._docs = build('docs', 'v1', credentials=self.drive_file.crendentials)
        return self._docs
    
    @property
    def document(self) -> dict:
        if not self._document:
            self._document = self.docs.documents().get(documentId=self.drive_file.id).execute()
        return self._document
    
    @property
    def body(self) -> dict:
        return self.document.get('body') or {}
    
    @property
    def content(self) -> list:
        return self.body.get('content') or []
    
    def refresh(self):
        self._document = self.docs.documents().get(documentId=self.drive_file.id).execute()
    
    @property
    def text(self):
        content = self.document.get('body').get('content')
        doc_text = ''
        for value in content:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    if 'textRun' in elem:
                        doc_text += elem.get('textRun').get('content')

        return doc_text

    @property
    def pdf(self) -> io.BytesIO:
        if not self._pdf:
            request = self.drive_file.google_workspace_service.drive.files().export_media(fileId=self.id, mimeType='application/pdf')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%." % int(status.progress() * 100))
            
            fh.seek(0)
            self._pdf = fh
        self._pdf.seek(0)
        return self._pdf
    
    
    @property
    def markdown(self):
        if not self._markdown:
            request = self.drive_file.google_workspace_service.drive.files().export_media(
                fileId=self.id, mimeType="text/markdown"
            )
            markdown_content = request.execute()

            self._markdown = markdown_content.decode("utf-8")
        return self._markdown


    @classmethod 
    def new_from_markdown(cls, credentials, drive: Resource, title:str, markdown: str, email_address: str):
        # Convert To HTMO
        html_content = mistune.html(markdown)
  
        # Create a new Google Doc
        file_metadata = {"name": title, "mimeType": "application/vnd.google-apps.document",}

        media = MediaIoBaseUpload(
            io.BytesIO(html_content.encode("utf-8")),
            mimetype="text/html",
            resumable=True,
        )
        file = (
            drive.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        file_id = file.get("id")
        print(f'File ID: {file_id}')

        try:
            permission = {"type": "user", "role": "writer", "emailAddress": email_address}
            drive.permissions().create(fileId=file_id, body=permission).execute()
            print(f"Shared the file with {email_address}")
        except HttpError as error:
            print(f"An error occurred while sharing the file: {error}")

        doc_uri = f"https://docs.google.com/document/d/{file_id}"
        print(doc_uri)
        return cls(drive_file=GoogleDriveFile(credentials=credentials, drive=drive, **file))
    
    def _batch_update(self, requests: list):
        # Execute the batch update request
        result = self.docs.documents().batchUpdate(
            documentId=self.id,
            body={'requests': requests}
        ).execute()
        return result
    
    
    @property
    def data(self) -> dict:
        return {
            'document_structure': self.document,
            'markdown': self.markdown,
            'title': f'{self.drive_file.name}',
            'google_doc_id': self.id
        }
    
    @property
    def max_index(self):
        body = self.document.get('body')
        content = body.get('content')
        max_index = content[-1]['endIndex']
        return max_index

    def find_and_replace_text(self, replace_text: str, contains_text: str, match_case: bool, search_by_regex: bool):
        """
        Replaces all instances of the specified text.

        Args: 
            replace_text (str): The text that will replace the matched text.
            contains_text (str): The text to search for in the document.
            match_case (bool): Indicates whether the search should respect case:
            search_by_regex (bool): Whether the search text is a regex. True if the find value should be treated as a regular expression. Any backslashes in the pattern should be escaped.

        Returns:
            dict: The result of the batch update operation.

        """
        
        requests = [
            {
                'replaceAllText': {
                    'replaceText': replace_text,
                    'containsText': {
                        'text': contains_text,
                        'matchCase': match_case,
                        'searchByRegex': search_by_regex
                    }
                }
            }
        ]

        # Execute the batch update request
        result = self._batch_update(requests)
        print(result)
        return result
    
    
    def insert_text(self, text, index):
        """
        Inserts text in the document.

        Args:
            text (str): The text to be inserted.
            index (int): The index at which to insert the text.

        Returns
            dict: The result of the batch update operation.        
        """
        
        # TODO: Turn Markdown Text into Google Docs Styles

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': index,  # Insert at the beginning of the document body
                    },
                    'text': text + '\n\n'
                }
            }
        ]
        result = self._batch_update(requests)
        print(result)
        return result
    

    def update(self, text, index=1):
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': index,  # Insert at the beginning of the document body
                    },
                    'text': text + '\n\n'
                }
            }
        ]

        # Execute the batch update request
        result = self.docs.documents().batchUpdate(documentId=self.id, body={'requests': requests}).execute()
        print(result)
        return result
    
    # def update_title(self, title:str):
    #     self.document['title'] = title
    #     self.update(text=title)
    #     return self.document
    
    
    @property
    def insert_indices(self):
        """
        Finds the start and end indices of '$$$START_INSERT$$$' and '$$$END_INSERT$$$'
        in the given data structure.

        Args:
            data: A list of dictionaries representing document content.

        Returns:
            A dictionary containing the start and end indices for both markers.
        """
        start_marker_indices = None
        end_marker_indices = None

        for item in self.content:
            if "paragraph" in item and "elements" in item["paragraph"]:
                for element in item["paragraph"]["elements"]:
                    if "textRun" in element and "content" in element["textRun"]:
                        content = element["textRun"]["content"]
                        if content.strip() == "$$$START_INSERT$$$":
                            start_marker_indices = {
                                "start": element["startIndex"],
                                "end": element["endIndex"]
                            }
                        elif content.strip() == "$$$END_INSERT$$$":
                            end_marker_indices = {
                                "start": element["startIndex"],
                                "end": element["endIndex"]
                            }

        return {
            "start": IndexRange(**start_marker_indices),
            "end": IndexRange(**end_marker_indices)
        }
    
    @property
    def insert_start_index_range(self) -> IndexRange:
        return self.insert_indices.get('start')
    
    @property
    def insert_end_index_range(self) -> IndexRange:
        return self.insert_indices.get('end')
    

    def download_as_pdf(self) -> io.BytesIO:
        if self.mime_type != 'application/vnd.google-apps.document':
            raise ValueError("File is not a Google Doc.")
        
        request = self.drive_file.google_workspace_service.drive.files().export_media(fileId=self.id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        
        fh.seek(0)
        return fh