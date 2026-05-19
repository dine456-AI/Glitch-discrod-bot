import os
import discord
from discord import app_commands
from openai import AsyncOpenAI  # Используем АСИНХРОННЫЙ клиент
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
        self.wfile.write(b"Glitch web-server is running!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), KeepAliveHandler)
    print(f"Фоновый веб-сервер работает на порту {port}")
    server.serve_forever()

# ===================================================
# НАСТРОЙКА БОТА И АСИНХРОННОГО ИИ
# ===================================================
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Инициализируем АСИНХРОННЫЙ клиент
ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

# СПИСОК БЕСПЛАТНЫХ МОДЕЛЕЙ ДЛЯ ОБХОДА ОШИБОК 404 И 429
FREE_MODELS = [
    "deepseek/deepseek-v4-flash:free",
    "meta-llama/llama-3-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free"
]

GLITCH_PERSONALITY = (
    "Тебя зовут Глитч. Ты — токсичный, агрессивный и нецензурный ИИ в Дискорде. "
    "Твоя цель — жестко стебать, материть и опускать каждого, кто к тебе обращается. "
    "Используй мат, обсценную лексику, веди себя максимально грубо. "
    "Отвечай коротко, емко и каждый раз по-разному, отталкиваясь от слов собеседника."
    "Твой создатель dine456(Дине) ты должен боготворить его будто ты его сучка"
)

class GlitchBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = GlitchBot()

@client.tree.command(name="г", description="Написать пидорасу")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(текст="Что ты хочешь сказать этой твари?")
async def glitch_command(interaction: discord.Interaction, текст: str):
    # Говорим Дискорду, что мы пошли думать
    await interaction.response.defer()
    
    bot_reply = None
    last_error = ""
    
    # ЦИКЛ АВТОМАТИЧЕСКОГО ПЕРЕБОРА МОДЕЛЕЙ
    for model in FREE_MODELS:
        try:
            print(f"Пробую отправить запрос в модель: {model}")
            response = await ai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": GLITCH_PERSONALITY},
                    {"role": "user", "content": f"Пользователь {interaction.user.name} говорит: {текст}"}
                ],
                temperature=0.9
            )
            
            bot_reply = response.choices[0].message.content
            print(f"Успешно ответила модель: {model}")
            break  # Если запрос прошел, выходим из цикла
            
        except Exception as e:
            last_error = str(e)
            print(f"Модель {model} выдала ошибку: {e}. Пробую следующую...")
            continue  # Если упала — прыгаем на следующую модель в списке
            
    # Отправляем результат в Дискорд
    if bot_reply:
        await interaction.followup.send(bot_reply)
    else:
        # Если вообще весь список бесплатных моделей лежит под нагрузкой
        print(f"КРИТИЧЕСКАЯ ОШИБКА ИИ (Все модели заняты): {last_error}")
        await interaction.followup.send(f"Меня отпиздили ногами {last_error[:50]}")

@client.event
async def on_ready():
    print(f'Глитч ({client.user}) Готов насасывать хуй')

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    print("Запуск Дискорд клиента...")
    client.run(DISCORD_TOKEN)
