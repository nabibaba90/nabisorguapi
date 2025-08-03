from flask import Flask, jsonify
from pyrogram import Client
from pyrogram.sessions import StringSession
import asyncio
import time
import base64
import os

API_ID = 17570480
API_HASH = "18c5be05094b146ef29b0cb6f6601f1f"
B64_FILE = "nabi_session.b64"

# Base64 session string'i oku
if not os.path.exists(B64_FILE):
    raise FileNotFoundError(f"{B64_FILE} bulunamadı!")

with open(B64_FILE, "r") as f:
    string = f.read().strip()

try:
    decoded_session = base64.b64decode(string).decode()
except Exception as e:
    raise ValueError("Base64 decoding hatası: " + str(e))

# Flask ve event loop
app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route("/nabiapi/<komut>/<tc>")
def sorgu_yap(komut, tc):
    sonuc = loop.run_until_complete(sorgu_gonder(komut, tc))
    return jsonify(sonuc)

async def sorgu_gonder(komut, tc):
    mesajlar = []

    async with Client(
        session_name=StringSession(decoded_session),
        api_id=API_ID,
        api_hash=API_HASH
    ) as app:
        sahmaran = await app.get_users("SahmaranBot")

        # Mevcut en son mesaj ID’sini al
        last_message_id = 0
        async for msg in app.get_chat_history(sahmaran.id, limit=1):
            last_message_id = msg.id
            break

        # Komutu gönder
        await app.send_message(sahmaran.id, f"/{komut} {tc}")
        await asyncio.sleep(2)

        # Sonraki mesajları 20 saniye boyunca dinle
        baslangic = time.time()
        while time.time() - baslangic < 20:
            async for msg in app.get_chat_history(sahmaran.id, offset_id=last_message_id, limit=10):
                if msg.text and tc in msg.text and msg.text not in mesajlar:
                    mesajlar.append(msg.text)
                    last_message_id = max(last_message_id, msg.id)
            await asyncio.sleep(2)

    return {
        "komut": komut,
        "tc": tc,
        "kayit_sayisi": len(mesajlar),
        "sonuclar": mesajlar
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
