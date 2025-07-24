import logging
import aiohttp

GEMINI_API_KEY = "AIzaSyAqhaNjM0TI2h-7-ZoTlhM_KHJz-j09QAo"  # Aynı anahtarı buraya da ekledim

logger = logging.getLogger(__name__)

async def query_gemini_api(message_text: str) -> str:
    """
    Gemini API ile sohbet sorgusu yapar.
    Gerçek endpoint ve payload Gemini dokümanına göre ayarlanmalı.
    """
    url = "https://gemini.api.endpoint/chat"  # Burayı gerçek Gemini API endpoint ile değiştir
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": message_text
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "Cavab alınmadı.")
                else:
                    return f"Xəta: API status kodu {resp.status}"
    except Exception as e:
        logger.error(f"Gemini API xətası: {e}")
        return "Xəta baş verdi, sonra yenidən cəhd edin."
