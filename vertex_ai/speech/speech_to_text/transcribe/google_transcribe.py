import asyncio
from google.cloud import speech

class GoogleTranscribe:
    def __init__(self):
        self.client = speech.SpeechAsyncClient()
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
                sample_rate_hertz=8000,
                language_code="en-US",
            ),
            interim_results=True,
        )
        self._audio_queue = asyncio.Queue()
        self._transcript_queue = asyncio.Queue()
        self._task = None

    async def _audio_generator(self):
        yield speech.StreamingRecognizeRequest(streaming_config=self.streaming_config)
        while True:
            chunk = await self._audio_queue.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def _transcribe_loop(self):
        print("Starting transcribe loop...")
        try:
            responses = await self.client.streaming_recognize(
                requests=self._audio_generator()
            )
            async for response in responses:
                if not response.results:
                    print("No results in response.")
                    continue

                for result in response.results:
                    # print(f"Result: is_final={result.is_final}, transcript='{result.alternatives[0].transcript}'")
                    await self._transcript_queue.put(
                        (result.is_final, result.alternatives[0].transcript)
                    )
        except Exception as e:
            print(f"Error in transcribe loop: {e}")
        finally:
            print("Exiting transcribe loop.")
            await self._transcript_queue.put(None) # Signal end of transcripts

    def start(self):
        self._task = asyncio.create_task(self._transcribe_loop())

    async def stop(self):
        await self._audio_queue.put(None)
        if self._task:
            await self._task

    async def add_audio_chunk(self, chunk):
        await self._audio_queue.put(chunk)

    async def get_transcript(self):
        return await self._transcript_queue.get()