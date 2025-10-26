from googleapiclient.discovery import build, Resource
from google_cloud import GoogleCloudService
import mistune
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
from googleapiclient.errors import HttpError
from .google_drive_service import GoogleDriveFile
import json 
from google.genai import types
import requests
from uuid import uuid4



class PresentationPageElement:
    def __init__(self, presentation_page: 'PresentationPage', **kwargs):
        self.presentation_page = presentation_page
        self._kwargs = kwargs
        self._placeholder_data: dict = {}

    @property
    def id(self) -> str:
        return self._kwargs.get('objectId', None)

    @property
    def shape(self) -> dict:
        return self._kwargs.get('shape', {})
    
    @property
    def shape_type(self) -> str:
        return self.shape.get('shapeType', None)
    
    @property
    def shape_properties(self) -> dict:
        return self.shape.get('shapeProperties', {})
    
    @property
    def text(self) -> dict:
        return self.shape.get('text', {})
    
    @property
    def placeholder(self) -> dict:
        return self.shape.get('placeholder', {})
    
    @property
    def placeholder_type(self) -> str:
        return self.placeholder.get('type', None)
    
    
    
class PresentationPage:
    def __init__(self, presentation: 'Presentation', **kwargs):
        self.presentation = presentation
        self._kwargs = kwargs
        self._thumbnail: io.BytesIO = None
        self._pdf: io.BytesIO = None


    @property
    def id(self):
        return self._kwargs.get('objectId', None)

    @property
    def page_elements(self) -> list[PresentationPageElement]:
        return [PresentationPageElement(presentation_page=self, **page) for page in self._kwargs.get('pageElements', [])]
    
    @property
    def placeholder_elements(self):
        return [page for page in self.page_elements if page.placeholder]
    

    @property
    def thumbnail(self) -> io.BytesIO:
        if not self._thumbnail:
            thumbnail_response = self.presentation.drive_file.google_workspace_service.slides.presentations().pages().getThumbnail(
                presentationId=self.presentation.id,
                pageObjectId=self.id,
                thumbnailProperties_mimeType='PNG', # Or 'JPEG'
                thumbnailProperties_thumbnailSize='LARGE' # Options: 'SMALL', 'MEDIUM', 'LARGE'
            ).execute()

            print(thumbnail_response)

            content_url = thumbnail_response.get('contentUrl', None)

            r = requests.get(url=content_url)
            self._thumbnail = io.BytesIO(r.content)
        self._thumbnail.seek(0)
        return self._thumbnail
    
    def save_thumbnail(self, file_path:str):
        with open(file_path, 'wb') as f:
            f.write(self.thumbnail.read())

    @property
    def generative_schema(self):
        schema = {
            "type": "object",
            "properties": {}
        }

        for element in self.placeholder_elements:
            schema['properties'][element.id] = {
                "type": "string",
                "description": element.placeholder_type
            }
        
        schema['required'] = [element.id for element in self.placeholder_elements]
        return schema
    

    def make_placeholder_data(self, prompt:str) -> dict:
        if not self.placeholder_elements:
            return {}
        
        response = self.presentation.drive_file.google_workspace_service.gc.genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                f'# Slide Layout:\n{self._kwargs}'
                f'# Prompt:\n{prompt}'
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=self.generative_schema
            )
        )
        return json.loads(response.text)
    



class Presentation:
    def __init__(self, drive_file: GoogleDriveFile, **kwargs):
        self.drive_file = drive_file
        self._kwargs = kwargs
        self._pdf: io.BytesIO = None
        self._layout_contents: list[types.Part] = None

    @classmethod
    def from_drive_file(cls, drive_file: GoogleDriveFile, **kwargs):
        presentation = drive_file.google_workspace_service.slides.presentations().get(presentationId=drive_file.id).execute()
        return cls(drive_file=drive_file, **presentation)
    
    @property
    def id(self):
        return self._kwargs.get('presentationId', None)
    
    @property
    def url(self):
        return f"https://docs.google.com/presentation/d/{self.id}"

    @property
    def title(self):
        return self._kwargs.get('title', None)
    
    @property
    def masters(self) -> list[PresentationPage]:
        masters = self._kwargs.get('masters', [])
        return [PresentationPage(presentation=self, **master) for master in masters]
    
    @property
    def notesMaster(self) -> PresentationPage:
        notes_master = self._kwargs.get('notesMaster', None)
        return PresentationPage(presentation=self, **notes_master) if notes_master else None
    
    @property
    def slides(self) -> list[PresentationPage]:
        slides = self._kwargs.get('slides', [])
        return [PresentationPage(presentation=self, **slide) for slide in slides]
    
    @property
    def layouts(self) -> list[PresentationPage]:
        return [PresentationPage(presentation=self, **layout) for layout in self._kwargs.get('layouts', [])]
    
    @property
    def layout_id_enum(self) -> list[str]:
        return [layout.id for layout in self.layouts]
    
    
    @property
    def layout_contents(self):
        if not self._layout_contents:
            contents = []
            for layout in self.layouts:
                layout_properties: dict = layout._kwargs.get('layoutProperties', {})
                display_name = layout_properties.get('displayName', None)
                contents.append(types.Content(
                    parts = [
                        types.Part.from_text(text=f'Layout Name: {display_name}'),
                        types.Part.from_text(text=f'Layout ID: {layout.id}'),
                        types.Part.from_bytes(data=layout.thumbnail.read(), mime_type='image/png')
                    ],
                    role='model'
                ))
                
            self._layout_contents = contents
        return self._layout_contents


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
    

    def get_layout_page(self, layout_id:str) -> 'PresentationPage':
        return [layout for layout in self.layouts if layout.id == layout_id][0]
    
    
    def generate_slides_from_layouts(self, prompt:str):
        # Generate Slides Layout
        response = self.drive_file.google_workspace_service.gc.genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=self.layout_contents + [
                types.Content(
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_text(text=f'Generate a list of layout slides to be included in the deck')
                    ],
                    role='user'
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "object",
                    "properties": {
                        "slides": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "layout_id": {
                                        "type": "string",
                                        "enum": self.layout_id_enum
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "the title of the slide"
                                    }
                                },
                                "required": ["layout_id", "title"]
                            }
                        }
                    },
                    "required": ["slides"]
                }
            )
        )

        slides = json.loads(response.text).get('slides', [])
        print(json.dumps(slides, indent=4))  

        presentation_outline = '\n'.join(list(map(lambda slide: slide['title'], slides)))
        presentation_content = {slide['title']: {} for slide in slides}

        model_contents = []
        for slide in slides:
            layout = self.get_layout_page(slide['layout_id'])
            title = slide['title']

            response = self.drive_file.google_workspace_service.gc.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_text(text=f'{prompt}')
                        ],
                        role='user'
                    ),
                    types.Content(
                        parts=[
                            types.Part.from_text(text=f'Presentation Outline: {presentation_outline}'),
                            types.Part.from_text(text=f'Presentation Current Content: {presentation_content}'),
                        ],
                        role='model'
                    ),
                    types.Content(
                        parts=[
                            types.Part.from_text(text=f'Layout: {layout._kwargs}'),
                            types.Part.from_bytes(data=layout.thumbnail.read(), mime_type='image/png')
                        ],
                        role='model'
                    ),
                    types.Content(
                        parts=[
                            types.Part.from_text(text=f'Slide Title: {title}\nSlide Layout ID: {layout.id}'),
                            types.Part.from_text(text="Generate content for this particular slide.")
                        ],
                        role='user'
                    )
                
                    # f'# Slide Layout:\n{self._kwargs}'
                    # f'# Prompt:\n{prompt}'
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=layout.generative_schema
                )
            )

            placeholder_data = json.loads(response.text)
            presentation_content[title] = placeholder_data

            print(json.dumps(placeholder_data, indent=4))
            data = {
            "requests": [
                {
                "createSlide": {
                    # "objectId": '1234',
                    "slideLayoutReference": {
                    "layoutId": layout.id
                    },
                    "placeholderIdMappings": [],
                }
                },
            ]
            }

            for placeholder in layout.placeholder_elements:
                # if 'TITLE' not in placeholder.placeholder_type:
                #     continue
                temp_id = str(uuid4())
                data['requests'][0]['createSlide']['placeholderIdMappings'].append({
                    'layoutPlaceholder': placeholder.placeholder,
                    'objectId': temp_id
                })
                data['requests'].append({
                    'insertText': {
                        'objectId': temp_id,
                        'text': placeholder_data.get(placeholder.id),
                    }
                })

            try:
                result = self.drive_file.google_workspace_service.slides.presentations().batchUpdate(
                    presentationId=self.id,
                    body=data
                ).execute()
            except Exception as e:
                print(json.dumps(data, indent=4))
                raise e
                print(f'\n\nERRRORRRR')
                for placeholder in layout.placeholder_elements:
                    print(placeholder.placeholder_type)




          

