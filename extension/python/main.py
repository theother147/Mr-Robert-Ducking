from Transcription import Transcription
import asyncio


async def main():
    transcription = Transcription()
    await transcription.start_server()

asyncio.run(main())
