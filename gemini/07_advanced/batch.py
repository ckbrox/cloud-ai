
from google.genai import Client, types
from google.genai.models import _GenerateContentParameters_to_vertex
import time
import google.auth

'''
You can view batch inference jobs here: https://console.cloud.google.com/vertex-ai/batch-predictions
'''

_, project_id = google.auth.default()


client = Client(vertexai=True, project=project_id, location="global")

job = client.batches.create(
    model="gemini-2.5-flash",
    src=f"gs://{project_id}/temp/batch2.jsonl", # replace with the location of your batch file
    config=types.CreateBatchJobConfig(dest=f"gs://{project_id}/batch"), # replace with your output destination
)
print(f"Job name: {job.name}")
print(f"Job state: {job.state}")


completed_states = {
    types.JobState.JOB_STATE_SUCCEEDED,
    types.JobState.JOB_STATE_FAILED,
    types.JobState.JOB_STATE_CANCELLED,
    types.JobState.JOB_STATE_PAUSED,
}

while job.state not in completed_states:
    time.sleep(10)
    job = client.batches.get(name=job.name)
    print(f"Job state: {job.state}")