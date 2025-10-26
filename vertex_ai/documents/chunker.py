from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import google.auth

_, project_id = google.auth.default()

layout_parser_id = '81fcd3079f79dc52' # Change to your layout_parser_id

def process_document(
        file: bytes, 
        project_id: str=project_id, 
        location: str='us', 
        parser_id: str=layout_parser_id, 
        mime_type:str="application/pdf",
        chunk_size:int=1000,
    ) -> documentai.Document:
    '''
    Processes a document with Document AI

    Args:
        project_id (str): your Google Cloud project id
        location (str): the location of your Doc AI processpr
        parser_id (str): the ID of your Doc AI processor
        file (bytes): the bytes of the file to process
        mime_type (str): the mimeType of the file to process
    '''
    # Create a DocAI client
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(
            api_endpoint=f"{location}-documentai.googleapis.com"
        )
    )

    # Get the processor name
    name = client.processor_version_path(
        project=project_id, 
        location=location, 
        processor=parser_id,
        processor_version='pretrained'
    )

    process_options = documentai.ProcessOptions(
        layout_config=documentai.ProcessOptions.LayoutConfig(
            chunking_config=documentai.ProcessOptions.LayoutConfig.ChunkingConfig(
                chunk_size=chunk_size,
                include_ancestor_headings=False,
            )
        )
    )

    # Form the request
    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=file, mime_type=mime_type),
        process_options=process_options
    )


    # Process the document
    result = client.process_document(request=request)
    return result.document


