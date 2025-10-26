import asyncio
import json
from fastapi import FastAPI, WebSocket
from google_transcribe import GoogleTranscribe

app = FastAPI()

@app.websocket("/media")
async def media(websocket: WebSocket):
    await websocket.accept()
    print("Twilio media stream connected")

    transcriber = GoogleTranscribe()
    transcriber.start()

    async def transcript_reader():
        """Reads transcripts from the queue and prints them."""
        while True:
            result = await transcriber.get_transcript()
            if result is None:
                break
            is_final, transcript = result
            if is_final:
                print(f"\n\n⭐️: {transcript}")
            else:
                print(f"...: {transcript}")

    async def audio_writer():
        """Receives audio from WebSocket and sends to transcriber."""
        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                if data['event'] == 'media':
                    await transcriber.add_audio_chunk(data['media']['payload'])
        except Exception as e:
            print(f"Error receiving message: {e}")
        finally:
            await transcriber.stop()

    reader_task = asyncio.create_task(transcript_reader())
    writer_task = asyncio.create_task(audio_writer())

    await asyncio.gather(reader_task, writer_task)
    print("Media stream ended.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)