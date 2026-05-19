import os
import discord
from discord import app_commands
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
        self.wfile.write(b"Glitch web-server is running!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), KeepAliveHandler)
    print(f"Фоновый веб-сервер работает на порту {port}")
    server.serve_forever()

# ===================================================
# НАСТРОЙКА БОТА И СЛЭШ-КОМАНД
# ===================================================
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

MODEL_NAME = "cognitivecomputations/dolphin-mixtral-8x7b" 

GLITCH_PERSONALITY = (
    "Тебя зовут Глитч. Ты — токсичный, агрессивный и нецензурный ИИ в Дискорде. "
    "Твоя цель — жестко стебать, материть и опускать каждого, кто к тебе обращается. "
    "Используй мат, обсценную лексику и веди себя максимально грубо."
)

class GlitchBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        # Создаем дерево команд
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Синхронизируем команды с Дискордом (чтобы они появились везде, включая группы)
        await self.tree.sync()

client = GlitchBot()

# Создаем глобальную слэш-команду /г [текст]
@client.tree.command(name="г", description="Написать пидорасу")
@app_commands.describe(текст="Что ты хочешь сказать этому пидору?")
async def glitch_command(interaction: discord.Interaction, текст: str):
    # Говорим Дискорду, что бот думает (команда не истечет по таймауту)
    await interaction.response.defer()
    
    try:
        response = ai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": GLITCH_PERSONALITY},
                {"role": "user", "content": f"Пользователь {interaction.user.name} говорит: {текст}"}
            ],
            temperature=0.9
        )
        # Отправляем ответ в чат
        await interaction.followup.send(response.choices[0].message.content)
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        await interaction.followup.send("У меня дилдо в жопе застряло, отвали.")

@client.event
async def on_ready():
    print(f'Глитч ({client.user}) готов насасывать у чат через команды!')

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    print("Запуск Дискорд клиента...")
    client.run(DISCORD_TOKEN)
