from googleapiclient.discovery import build, Resource
from google_cloud import GoogleCloudService, google_cloud_client
import mistune
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
from googleapiclient.errors import HttpError
from .google_drive_service import GoogleDriveFile
import gspread
from time import sleep
from google.genai import Client, types
import json
from tqdm import tqdm
from uuid import uuid4

class GoogleSheetWorksheet():
    def __init__(self, google_sheet: 'GoogleSheet', worksheet: gspread.Worksheet, **kwargs):
        self.google_sheet = google_sheet
        self.worksheet: gspread.Worksheet = worksheet
        self._records: list[dict] = []
        self._values: list[list] = []
        self._summary: str = None
        self.genai_client: Client = google_cloud_client.genai_client


    def refresh(self):
        sheet_worksheets = self.google_sheet.spreadsheet.worksheets()
        self.worksheet = list(filter(lambda worksheet: worksheet.id == self.worksheet.id, sheet_worksheets))[0]
        self._records = []
        self._summary = None

    @property
    def title(self) -> str:
        return self.worksheet.title
    
    @property
    def id(self) -> str:
        return self.worksheet.id

    @property
    def records(self) -> list[dict]:
        if not self._records:
            try:
                self._records = self.worksheet.get_all_records()
            except gspread.exceptions.GSpreadException as e:
                print(str(e))
                print(e.args[0])
        return self._records
    
    @property
    def values(self) -> list[list]:
        if not self._values:
            self._values = self.worksheet.get_all_values()
        return self._values
    
    @property
    def indexed_values(self) -> list[dict]:
        new_values = []
        for row_index, row in enumerate(self.values):
            new_row = []
            for index, value in enumerate(row):
                new_values.append({
                    'row_number': row_index+1,
                    'column_number': index+1,
                    'value': value
                })
        return new_values

    @property
    def indexed_records(self):
        return [{'row_number': index+2} | row for index, row in enumerate(self.records)]

    @property
    def indexed_headers(self):
        return [{'column_name': header, 'column_number': index+1} for index, header in enumerate(self.headers)]


    def get_row_by_index(self, row_index) -> dict:
        row_records = list(filter(lambda x: x['row_index'] == row_index, self.indexed_records))
        return row_records[0]
    
    def get_row_by_row_number(self, row_number:int) -> dict:
        row_records = list(filter(lambda x: x['row_number'] == row_number, self.indexed_records))
        return row_records[0]
    

    def get_column_name_by_index(self, column_index) ->str:
        header = list(filter(lambda x: x['column_index'] == column_index, self.indexed_headers))
        return header[0]['column_name']

    def get_column_name_by_column_number(self, column_number) ->str:
        header = list(filter(lambda x: x['column_number'] == column_number, self.indexed_headers))
        return header[0]['column_name']
    

    def get_cell_location_by_description(self, description:str) -> dict:
        res = self.google_sheet.drive_file.google_workspace_service.gc.genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                f'<worksheet>{self.indexed_values}</worksheet>',
                f'Description: {description}'
                f'Based on the description, what is the row number and column number of the cell?'
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "object",
                    "properties": {
                        "row_number": {"type": "integer"},
                        "column_number": {"type": "integer"}
                    },
                    "required": ["row_number", "column_number"]
                }
            )

        )

        data = json.loads(res.text)
        return data
    
    def get_cell_range_by_description(self, description:str) -> dict:
        """
        Get the cell range using a description

        Args:
            description (str): a description of the range to retrieve

        Returns
            dict: the cell range {'first_row_number': int, 'first_column_number': int, 'last_row_number': int, 'last_column_number': int}
        """
        res = self.google_sheet.drive_file.google_workspace_service.gc.genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                f'<worksheet>{self.indexed_values}</worksheet>',
                f'Description: {description}'
                f'Based on the description, what is range of cells?'
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "object",
                    "properties": {
                        "first_row_number": {"type": "integer"},
                        "first_column_number": {"type": "integer"},
                        "last_row_number": {"type": "integer"},
                        "last_column_number": {"type": "integer"}
                    },
                    "required": ["first_row_number", "first_column_number", "last_row_number", "last_column_number"]
                }
            )

        )

        data = json.loads(res.text)
        return data
    
    def clear_range(self, first_row_number:int, first_column_number:int, last_row_number:int, last_column_number:int):
        cells = self.worksheet.range(first_row_number, first_column_number, last_row_number, last_column_number)
        for cell in cells:
            cell.value = ''
        self.worksheet.update_cells(cells)



    def get_column_schema_for_range(self, first_row_number:int, first_column_number:int, last_row_number:int, last_column_number:int):
        rows = [i for i in range(first_row_number, last_row_number+1)]
        columns = [i for i in range(first_column_number, last_column_number+1)]

        res = self.genai_client.models.generate_content(
            model=google_cloud_client.MODEL,
            contents=[
                f'<worksheet_info>\n{self.info}\n<worksheet_info>',
                f'<worksheet_records>\n{self.indexed_values}\n</worksheet_records>',
                f'I will be adding conent for the content in the rows: {rows} and columns: {columns}.',
                f'Generate a schema for the columns. The number of key should be equal to the number of columns that will be added ({len(columns)}).'
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["name", "description"],
                            },
                            "minItems": len(columns),
                            "maxItems": len(columns)
                        }
                    },
                    "required": ["keys"]
                }
            )
        )

        keys = json.loads(res.text)['keys']
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }

        for key in keys:
            schema['properties'][key['name']] = {'type': 'string', 'description': key['description']}
            schema['required'].append(key['name'])

        return schema
    




    @property
    def headers(self) -> list[str]:
        try:
            return list(self.records[0].keys())
        except:
            return []
        
    @property
    def schema(self) -> dict:
        schema = {
            'type': 'object',
            'properties': {},
            'required': self.headers
        }

        for header in self.headers:
            schema['properties'][header] = {'type': 'string'}

        return schema


    @property
    def info(self) -> dict:
        return {
            # 'google_sheet_title': self.worksheet.spreadsheet.title,
            'worksheet_title': self.worksheet.title,
            'worksheet_index': self.worksheet.index,
            'worksheet_id': self.worksheet.id,
            # 'url': self.worksheet.url,
            'column_count': len(self.values[0]) if self.values else 0,
            'row_count': len(self.values) if self.values else 0,
            'headers': self.summary,
        }
    
    @property
    def summary(self) -> str:
        if not self._summary:
            self._summary = self.get_summary()
        return self._summary

    def get_summary(self, prompt=None) -> str:
        res = self.genai_client.models.generate_content(
            model=google_cloud_client.LITE_MODEL,
            contents=[
                f'<worksheet>{self.values}</worksheet>',
                prompt or f'Summarize the worksheet'
            ]
        )
        return res.text
    

    def get_column_range(self, column_index:int) -> list[gspread.Cell]:
        return self.worksheet.range(1,column_index+1,len(self.records)+1, column_index+1)

    def get_row_range(self, row_index:int) -> list[gspread.Cell]:
        return self.worksheet.range(row_index+1,1,row_index+1,len(self.headers))


    def get_column_index_from_name_or_description(self, name_or_description:str) -> int:
        '''
        Gets a column index based on a name or description

        Args:
            name_or_description (str): the name or description of the column that you want the index for. can be the name of the colum or a description of what the column is

        Returns:
            dict ({"index": column_index}): returns the index of the column
        '''

        response = self.genai_client.models.generate_content(
            model=google_cloud_client.LITE_MODEL,
            contents=[
                f'<worksheet_info>\n{self.info}\n<worksheet_info>',
                f'<indexed_columns>\n{self.indexed_headers}\n</indexed_columns>',
                f'Desired column name or description: {name_or_description}',
                f'Based on the desired column name and description, what is the index of the desired column.'
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "object",
                    "properties": {"index": {"type": "integer"}},
                    "required": ["index"]
                }
            )
        )

        return json.loads(response.text)["index"]


    

    def clear_a_column(self, column_index:int) -> dict:
        """
        Clears an entire column leaving only the header

        Args:
            column_index (int): the index of the column to clear

        Returns:
            dict: the status of the operation
        """
        column_cells = self.get_column_range(column_index)[1:]
        for cell in column_cells:
            cell.value = ''
        self.worksheet.update_cells(column_cells)
        return {
            'status': 'success',
            'description': f'cleared the column with indedex {column_index}'
        }


    def update_row(self, row_index: int, column_index: int, prompt=None):
        
        # Get the row gspread.Cell values
        row_cells = self.get_row_range(row_index=row_index)
        
        # Get the row as a dictionary
        row_record = self.get_row_by_index(row_index=row_index)

        header = self.get_column_name_by_index(column_index=column_index)

        prompt = prompt or f"Generate content for this column: {header}. Your reponse should only be the content that will be added to this cell."

        cell_to_update = list(filter(lambda cell_: cell_.col == column_index+1, row_cells))[0]

        response = self.genai_client.models.generate_content(
            model=google_cloud_client.MODEL,
            contents=[
                f'<worksheet_info>\n{self.info}\n<worksheet_info>',
                f'<worksheet_records>\n{self.indexed_records}\n</worksheet_records>',
                f'<row_to_focus_on>\n{row_record}\n</row_to_focus_on>'
                f'<column_to_update>\n{header}\n</column_to_update>',
                f'{prompt}'
            ],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        cell_to_update.value = response.text

        self.worksheet.update_cells([cell_to_update])

        return response.text


    def update_all_rows(self, column_index:int, prompt:str):
        """
        Updates a single column for all rows

        Args:
            column_index (int): the index of the column to update
            prompt (str): instructions for updating the row

        Return:
            After looping through each row and updating that column, the status of the operation
        """
        for index in tqdm(range(1,len(self.records)+1)):
            self.update_row(row_index=index, column_index=column_index, prompt=prompt)

        return {
            'status': 'success',
            'description': 'All of the rows have been updated'
        }

    def update_multiple_columns_of_row(self, row_index:int, column_indexes:list[int], prompt:str):

        # Get the row gspread.Cell values
        row_cells = self.get_row_range(row_index=row_index)
        
        # Get the row as a dictionary
        row_record = self.get_row_by_index(row_index=row_index)

        headers = list(filter(lambda x: x['column_index'] in column_indexes, self.indexed_headers))
        print(headers)
        return

        prompt = prompt or f"Generate content for this column: {header}. Your reponse should only be the content that will be added to this cell."

        cell_to_update = list(filter(lambda cell_: cell_.col == column_index+1, row_cells))[0]

        response = self.genai_client.models.generate_content(
            model=google_cloud_client.MODEL,
            contents=[
                f'<worksheet_info>\n{self.info}\n<worksheet_info>',
                f'<worksheet_records>\n{self.indexed_records}\n</worksheet_records>',
                f'<row_to_focus_on>\n{row_record}\n</row_to_focus_on>'
                f'<column_to_update>\n{header}\n</column_to_update>',
                f'{prompt}'
            ],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        cell_to_update.value = response.text

        self.worksheet.update_cells([cell_to_update])

        return response.text


    def add_additional_row(self):
        schema = {
            'type': 'object',
            'properties': {},
            'required': self.headers
        }

        for header in self.headers:
            schema['properties'][header] = {'type': 'string'}
        
        response = self.genai_client.models.generate_content(
            model=google_cloud_client.MODEL,
            contents=[
                f'<worksheet_info>\n{self.info}\n<worksheet_info>',
                f'<worksheet_records>\n{self.records}\n</worksheet_records>',
                f'Create a new record'
            ],
            config=types.GenerateContentConfig(
                # tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type='application/json',
                response_schema=schema,
                max_output_tokens=64000
            )
        )

        record = json.loads(response.text)
        row = []
        for header in self.headers:
            row.append(record.get(header))

        self.worksheet.append_row(row)


    def add_additional_rows(self, number_of_rows:int):
        '''
        Adds aditional rows to the spreadsheet

        Args:
            number_of_rows (int): the number of rows that should be added

        Returns:
            dict: status of the operation
        '''
        for _ in tqdm(range(number_of_rows)):
            self.add_additional_row()

        return {
            'status': 'success',
            'description': f'{number_of_rows} have been added to the spreadsheet'
        }
    
    def delete_row(self, row_index:int):
        '''
        Deletes a row from the spreadsheet

        Args:
            row_index (int): the index of the row that should be deleted

        Returns:
            dict: status of the operation
        '''
        self.worksheet.delete_rows(row_index+1)
        
        return {
            'status': 'success',
            'description': f'row {row_index} has been deleted'
        }
    
    def delete_rows(self, start_index:int, end_index:int):
        '''
        Deletes a range of rows from the spreadsheet

        Args:
            start_index (int): the starting index of the rows that should be deleted
            end_index (int): the ending index of the rows that should be deleted

        Returns:
            dict: status of the operation
        '''
        self.worksheet.delete_rows(start_index + 1, end_index + 1)
        
        return {
            'status': 'success',
            'description': f'rows from {start_index} to {end_index} have been deleted'
        }



    def append_row(self, worksheet:gspread.Worksheet, data: list, attempt=1):
        try:
            worksheet.append_row(data)
        except gspread.exceptions.APIError as e:
            if attempt < 4:
                sleep_time = 15
                print(f'Attempt {attempt} failed, sleeping for {15} seconds')
                sleep(sleep_time)
                self.append_row(worksheet=worksheet, data=data, attempt=attempt+1)
                self._records = []
            else:
                raise e






class GoogleSheet():
    def __init__(self, drive_file: GoogleDriveFile, **kwargs):
        self.drive_file = drive_file
        self._kwargs = kwargs
        self._docs: Resource = None
        
        self._gs: gspread.Client = None
        self._spreadsheet: gspread.Spreadsheet = None

        self._worksheets: list[GoogleSheetWorksheet] = []
        
        self.working_worksheet_title = kwargs.get('worksheet_title', None)
        self._working_worksheet: GoogleSheetWorksheet = None
        

        # DEPRECATE
        self._worksheet: GoogleSheetWorksheet = None
        self._records: list[dict] = []
    

    @property
    def id(self):
        return self.drive_file.id
    
    @property
    def url(self):
        return f"https://docs.google.com/spreadsheets/d/{self.drive_file.id}"
    
    @property
    def title(self):
        return self.spreadsheet.title
    
    @property
    def gs(self):
        if not self._gs:
            self._gs = gspread.Client(self.drive_file.google_workspace_service.credentials)
        return self._gs
    
    @property
    def spreadsheet(self) -> gspread.Spreadsheet:
        if not self._spreadsheet:
            self._spreadsheet = self.gs.open_by_key(self.id)
        return self._spreadsheet
    
    @property
    def worksheets(self) -> list[GoogleSheetWorksheet]:
        if not self._worksheets:
            worksheets = self.spreadsheet.worksheets()
            self._worksheets = [GoogleSheetWorksheet(google_sheet=self, worksheet=worksheet) for worksheet in worksheets]
        return self._worksheets
    
    @property
    def worksheets_titles(self) -> list[str]:
        return [worksheet.title for worksheet in self.worksheets]
    
    @property
    def worksheets_ids(self) -> list[str]:
        return [worksheet.id for worksheet in self.worksheets]
    
    @property
    def worksheets_info(self) -> list[dict]:
        return [worksheet.info for worksheet in self.worksheets]
    
    def get_worksheet_by_title(self, title:str) -> GoogleSheetWorksheet:
        filtered_titles = list(filter(lambda worksheet: worksheet.title == title, self.worksheets))
        return filtered_titles[0] if filtered_titles else None
    
    def get_worksheet_by_id(self, id:str) -> GoogleSheetWorksheet:
        filtered_ids = list(filter(lambda worksheet: str(worksheet.id) == str(id), self.worksheets))
        return filtered_ids[0] if filtered_ids else None

    @property
    def working_worksheet(self) -> GoogleSheetWorksheet:
        if not self._working_worksheet:
            filtered_worksheets = list(filter(lambda worksheet: worksheet.title == self.working_worksheet_title, self.worksheets))
            self._working_worksheet = filtered_worksheets[0] if filtered_worksheets else self.worksheets[0]
        return self._working_worksheet
    
    @property
    def info(self):
        return {
            'title': self.title,
            'url': self.url,
            'id': self.id,
            'worksheets': list(map(lambda worksheet: {'title': worksheet.title, 'id': worksheet.worksheet.id}, self.worksheets))
        }
        
    
    @property
    def worksheet(self):
        if not self._worksheet:
            if self.working_worksheet_title:
                worksheet = self.spreadsheet.worksheet(self.working_worksheet_title)
            else:
                worksheet = self.spreadsheet.sheet1

            self._worksheet = GoogleSheetWorksheet(google_sheet=self, worksheet=worksheet)
        return self._worksheet
    

    def refresh_spreadsheet(self, worksheet_title=None):
        self._worksheets = []
        self._worksheet = None
        self._records = []
        self._spreadsheet = None

        self._spreadsheet = self.gs.open_by_key(self.id)
        if worksheet_title:
            worksheet = self.spreadsheet.worksheet(worksheet_title)
        else:
            worksheet = self.spreadsheet.sheet1
        
        self._worksheet = GoogleSheetWorksheet(google_sheet=self, worksheet=worksheet)
    

    @property
    def records(self):
        return self.worksheet.records
    
  
    def new_worksheet(self, title:str, index=0) -> GoogleSheetWorksheet:
        """
        Creates a new worksheet (a new tab in the Google Sheet)

        Args:
            title (str): the title of the new worksheet
            index (int, optional): the index of the new worksheet. Defaults to 0 (first tab in the spreadsheet).

        Returns:
            GoogleSheetWorksheet: the new worksheet
        """

        # The index cannot be greater than the length of curent worksheets
        index = index if index < len(self.worksheets) else len(self.worksheets)

        # The title must be unique
        worksheet_titles = [worksheet.title for worksheet in self.worksheets]
        if title in worksheet_titles:
            title = f"{title}_{uuid4()}"

        worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=26, index=index)
  
        return GoogleSheetWorksheet(google_sheet=self, worksheet=worksheet)


    def download_google_spreadsheet_as_csv(self) -> io.BytesIO:
        if self.drive_file.mime_type != 'application/vnd.google-apps.spreadsheet':
            raise ValueError("File is not a Google Spreadsheet.")
        request = self.drive_file.google_workspace_service.drive.files().export_media(fileId=self.id, mimeType='text/csv')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        
        fh.seek(0)
        return fh