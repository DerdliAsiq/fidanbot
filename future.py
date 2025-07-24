import asyncio
from google import genai

client = genai.Client()

async def sohbet_response(user_text: str) -> str:
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text
        )
    )
    return response.text
