import aiohttp
import asyncio

# GOOGLE GEMINI API KEY (kendi anahtarını buraya koy)
API_KEY = "AIzaSyAqhaNjM0TI2h-7-ZoTlhM_KHJz-j09QAo"

# Gemini API endpoint URL'si (örnek, gerçek endpoint Google belgelerinden kontrol edilmeli)
GEMINI_API_URL = "https://gemini.googleapis.com/v1/chat:sendMessage"

async def sohbet_response(user_text: str) -> str:
    """
    Kullanıcının yazdığı metni Google Gemini API'ye gönderir, yanıtı döner.
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    json_data = {
        "model": "gemini-2.0-flash",  # Örnek model adı, gerçek dokümana göre değiştir
        "messages": [
            {
                "role": "user",
                "content": user_text
            }
        ],
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GEMINI_API_URL, headers=headers, json=json_data) as resp:
                if resp.status != 200:
                    return f"API xətası: Status kodu {resp.status}"

                data = await resp.json()

                # Burada dönüş yapısı Gemini API'ye göre değişir,
                # Örnek varsayalım ki "choices" listesinde "message" objesi var
                message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not message:
                    return "Cavab alınmadı."

                return message

        except Exception as e:
            return f"Xəta baş verdi: {e}"
