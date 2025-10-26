import json
from flask import Flask
from flask_sock import Sock
from google_transcribe import GoogleTranscribe

app = Flask(__name__)
sock = Sock(app)

HTTP_SERVER_PORT = 8080

@sock.route('/media')
def media(ws):
    """Handles the WebSocket connection from Twilio."""
    print("Twilio media stream connected")
    transcriber = GoogleTranscribe()

    def audio_stream_generator():
        """A generator that yields audio chunks from the WebSocket."""
        while True:
            print("Receiving message")
            try:
                message = ws.receive()
                if message is None:
                    break
                data = json.loads(message)
                if data['event'] == 'media':
                    print(data)
                    yield data['media']['payload']
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    # for transcript in transcriber.transcribe_stream(audio_stream_generator()):
    #     print(f'Transcription: {transcript}')

    for _ in audio_stream_generator():
        print("Received audio chunk.")

if __name__ == '__main__':
    print("This script is not meant to be run directly. Run with a WSGI server like Gunicorn.")