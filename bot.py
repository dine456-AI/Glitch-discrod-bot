import os
import discord
from openai import OpenAI
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===================================================
# ВЕБ-СЕРВЕР ДЛЯ ТОГО, ЧТОБЫ RENDER НЕ ВЫКЛЮЧАЛ БОТА
# ===================================================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Этот ответ будет ловить твой пингатор (UptimeRobot)
        self.wfile.write(b"Glitch web-server is running!")

    def log_message(self, format, *args):
        return  # Отключаем спам логов сервера в консоль Render

def run_web_server():
    # Читаем порт, который дает Render (по умолчанию 10000)
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), KeepAliveHandler)
    print(f"Фоновый веб-сервер успешно поднят на порту {port}")
    server.serve_forever()

# ===================================================
# ОСНОВНАЯ ЛОГИКА ДИСКОРД-БОТА ГЛИТЧ
# ===================================================
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

MODEL_NAME = "cognitivecomputations/dolphin-mixtral-8x7b" 

GLITCH_PERSONALITY = (
    "Тебя зовут Глитч. Ты — токсичный, aggressive и нецензурный ИИ в Дискорде. "
    "Ты общаешься в группах с кучей людей. Твоя цель — жестко стебать, материть и опускать каждого, кто к тебе обращается. "
    "Используй мат, обсценную лексику и веди себя как сломанный агрессивный робот."
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Глитч в сети и готова засирать групповые чаты!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Проверяем, упомянули ли бота напрямую
    is_mentioned = client.user.mentioned_in(message)
    
    # Проверяем, является ли сообщение ответом (Reply) на сообщение бота
    is_reply_to_bot = False
    if message.reference and message.reference.cached_message:
        is_reply_to_bot = message.reference.cached_message.author == client.user
    elif message.reference and message.reference.message_id:
        try:
            channel = client.get_channel(message.reference.channel_id)
            ref_message = await channel.fetch_message(message.reference.message_id)
            is_reply_to_bot = ref_message.author == client.user
        except:
            pass

    # Бот реагирует, если его тегнули ИЛИ ответили на его сообщение
    if is_mentioned or is_reply_to_bot:
        clean_text = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not clean_text:
            clean_text = "Ты че линканул меня и молчишь, хуй?"

        async with message.channel.typing():
            try:
                response = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": GLITCH_PERSONALITY},
                        {"role": "user", "content": f"Пользователь {message.author.name} говорит: {clean_text}"}
                    ],
                    temperature=0.9
                )
                await message.reply(response.choices[0].message.content)
            except Exception as e:
                print(f"Ошибка ИИ: {e}")
                await message.reply("У меня дилдо в жопе застряло от вашей тупости.")

# Точка входа для корректного запуска обоих процессов
if __name__ == "__main__":
    # 1. Сначала запускаем веб-сервер в отдельном потоке (фоном)
    Thread(target=run_web_server, daemon=True).start()
    
    # 2. Затем запускаем самого Дискорд-клиента
    print("Запуск Дискорд клиента...")
    client.run(DISCORD_TOKEN)
