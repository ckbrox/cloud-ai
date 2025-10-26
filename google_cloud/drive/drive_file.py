from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
from pymediainfo import MediaInfo
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from google.genai import Client, types

class GoogleDriveFile:
    def __init__(self, credentials:Credentials, drive: Resource, **kwargs):
        self._kwargs = kwargs
        self.crendentials = credentials
        self.drive: Resource = drive
        self._file: io.BytesIO = None
        self._resolution: tuple[int, int] = None

        self._docs_client: Resource = None
        self._sheets_client: Resource = None
        self._slides_client: Resource = None


    def format_file_id(file_id_or_uri:str):
        if '/d/' in file_id_or_uri:
            return file_id_or_uri.split('/d/')[1].split('/')[0]
        return file_id_or_uri
    
    @property
    def slides_client(self) -> Resource:
        if not self._slides_client:
            self._slides_client = build('slides', 'v1', credentials=self.crendentials)
        return self._slides_client
    
    @property
    def docs_client(self) -> Resource:
        if not self._docs_client:
            self._docs_client = build('docs', 'v1', credentials=self.crendentials)
        return self._docs_client

    
    @property
    def sheets_client(self) -> Resource: 
        if not self._sheets_client:
            self._sheets_client = build('sheets', 'v4', credentials=self.crendentials)
        return self._sheets_client
    
    @classmethod
    def from_file_id(cls, credentials:Credentials, drive: Resource, file_id: str):
        file_id = cls.format_file_id(file_id)
        file = drive.files().get(fileId=file_id).execute()
        return cls(credentials=credentials, drive=drive, **file)
    
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
        if self.mime_type == 'application/vnd.google-apps.presentation':
            from .google_slide import Presentation
            return Presentation(self)

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
                request = self.drive.files().get_media(fileId=self.id)
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
    

    def download_google_doc_as_pdf(self) -> io.BytesIO:
        if self.mime_type != 'application/vnd.google-apps.document':
            raise ValueError("File is not a Google Doc.")
        
        request = self.drive.files().export_media(fileId=self.id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        
        fh.seek(0)
        return fh
    
    def download_google_spreadsheet_as_csv(self) -> io.BytesIO:
        if self.mime_type != 'application/vnd.google-apps.spreadsheet':
            raise ValueError("File is not a Google Spreadsheet.")
        request = self.drive.files().export_media(fileId=self.id, mimeType='text/csv')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        
        fh.seek(0)
        return fh
    
    @property
    def resolution(self) -> tuple[int, int]:
        if not self._resolution:
            try:
                # Parse the media information from the stream
                media_info = MediaInfo.parse(self.file)

                # Find the video track and get the resolution
                for track in media_info.video_tracks:
                    if track.width and track.height:
                        self._resolution = (track.width, track.height)

            except Exception as e:
                print(f"An error occurred: {e}")
                print("This could be due to incomplete or invalid MP4 data.")
        return self._resolution
    
    def upload_file(self, file_bytes:bytes, mime_type:str, share_with_email: str = None):
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype=mime_type,
            resumable=True,
        )
        file = (
            self.drive.files()
            .create(body=self._kwargs, media_body=media, fields="id")
            .execute()
        )
        file_id = file.get("id")

        try:
            permission = {"type": "user", "role": "writer", "emailAddress": share_with_email}
            self.drive.permissions().create(fileId=file_id, body=permission).execute()
            print(f"Shared the file with {share_with_email}")
        except HttpError as error:
            print(f"An error occurred while sharing the file: {error}")
        
        return file_id
    
    

    # def resize(self):
    #     try:
    #         # 1. Set up the input stream from a pipe (our bytes)
    #         process_input = ffmpeg.input(
    #             'pipe:0',
    #             probesize='50M',         # Let's try 50 Megabytes
    #             analyzeduration='20M'
    #         )

    #         # 2. Define the output stream and its compression options
    #         process_output = ffmpeg.output(
    #             process_input,
    #             'pipe:1',
    #             f='mp4',          # Specify the output format is mp4
    #             vcodec='libx264',   # Use the standard H.264 video codec
    #             crf=28,           # Constant Rate Factor (lower value = higher quality/size). 23-28 is a good range.
    #             preset='medium',  # A balance between encoding speed and compression efficiency.
    #             vf='scale=-2:720', # Video filter to scale the height to 720p, maintaining aspect ratio.
    #             movflags='frag_keyframe+empty_moov+faststart',
    #             acodec='aac' 
    #         )

    #         # 3. Execute the FFmpeg command, feeding our bytes to stdin and reading from stdout
    #         out_bytes, err = ffmpeg.run(
    #             process_output,
    #             capture_stdout=True,
    #             capture_stderr=True,
    #             input=self.file.read()
    #         )

    #         if err:
    #             print("FFmpeg Error:", err.decode('utf8'))

    #         print(f"Compressed size: {len(out_bytes) / 1024 / 1024:.2f} MB")

    #         file = io.BytesIO(out_bytes)
    #         file.seek(0)
    #         self._file = file



    #         # # Now 'out_bytes' holds your smaller MP4 file content, which you can save or use.
    #         # with open("output_compressed.mp4", "wb") as f:
    #         #     f.write(out_bytes)
    #         # print("Compressed file saved as 'output_compressed.mp4'")

    #     except ffmpeg.Error as e:
    #         print('ffmpeg error:', e.stderr.decode())
