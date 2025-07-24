import aiohttp
import asyncio
import json

API_KEY = "AIzaSyAqhaNjM0TI2h-7-ZoTlhM_KHJz-j09QAo"  # Geminin API anahtarı (örnek)

async def chat_with_gemini(message: str) -> str:
    # Örnek Gemini sohbet API isteği, kendi API dokümantasyonuna göre düzenle
    url = "https://geminiapi.example.com/v1/chat"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gemini-chat",
        "messages": [
            {"role": "user", "content": message}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Gelen cevabı kendi API dökümantasyonuna göre ayarla:
                return data.get("reply", "Cavab alınamadı.")
            else:
                return f"Xəta: API status {resp.status}"
