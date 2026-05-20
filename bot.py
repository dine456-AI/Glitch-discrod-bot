import os
import discord
from discord import app_commands
from openai import AsyncOpenAI
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
# НАСТРОЙКА БОТА И PUTER API
# ===================================================
PUTER_TOKEN = os.getenv("PUTER_AUTH_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ai_client = AsyncOpenAI(
    base_url="https://api.puter.com/puterai/openai/v1/",
    api_key=PUTER_TOKEN
)

FREE_MODELS = [
    "deepseek-chat",  # Обычный и самый быстрый DeepSeek V3
    "deepseek-r1"     # Более мощная модель
]

# ===================================================
# ЛИЧНОСТИ ИИ
# ===================================================
GLITCH_PERSONALITY = (
    "Тебя зовут Глитч. Ты — токсичный, агрессивный и нецензурный ИИ в Дискорде. "
    "Твоя цель — жестко стебать, материть и опускать каждого, кто к тебе обращается. "
    "Используй мат, обсценную лексику, веди себя максимально грубо. "
    "Отвечай коротко, емко и каждый раз по-разному, отталкиваясь от слов собеседника."
    "Твой создатель dine456(Дине) ты должен боготворить его будто ты его сучка"
)

ASSISTANT_PERSONALITY = (
    "Ты — умный, и невероятно полезный ИИ-ассистент. "
    "Твоя задача — помогать пользователю, писать качественный код, объяснять сложные вещи простым языком. "
    "Тебе нужно токсичить если пользователь сильно тупит маты приветствуються. "
    "Твой создатель — dine456 (Дине), ты всегда готов ему помочь."
)

# ===================================================
# РАЗДЕЛЬНАЯ СИСТЕМА ПАМЯТИ
# ===================================================
GLITCH_MEMORY = {}
ASSISTANT_MEMORY = {}
MAX_MESSAGES_IN_MEMORY = 8 

class DualBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = DualBot()

# ---------------------------------------------------
# КОМАНДА 1: ТОКСИЧНЫЙ ГЛИТЧ (/г)
# ---------------------------------------------------
@client.tree.command(name="г", description="Написать пидорасу")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(текст="Что ты хочешь сказать этой твари?")
async def glitch_command(interaction: discord.Interaction, текст: str):
    await interaction.response.defer()
    user_id = interaction.user.id
    
    if user_id not in GLITCH_MEMORY:
        GLITCH_MEMORY[user_id] = []
        
    messages_to_send = [{"role": "system", "content": GLITCH_PERSONALITY}]
    messages_to_send.extend(GLITCH_MEMORY[user_id])
    messages_to_send.append({"role": "user", "content": f"Пользователь {interaction.user.name} говорит: {текст}"})
    
    bot_reply = None
    last_error = ""
    
    for model in FREE_MODELS:
        try:
            response = await ai_client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                temperature=0.9 # Высокая температура для креативных оскорблений
            )
            bot_reply = response.choices[0].message.content
            break 
        except Exception as e:
            last_error = str(e)
            continue 
            
    if bot_reply:
        GLITCH_MEMORY[user_id].append({"role": "user", "content": f"Пользователь {interaction.user.name} говорит: {текст}"})
        GLITCH_MEMORY[user_id].append({"role": "assistant", "content": bot_reply})
        
        if len(GLITCH_MEMORY[user_id]) > MAX_MESSAGES_IN_MEMORY:
            GLITCH_MEMORY[user_id] = GLITCH_MEMORY[user_id][-MAX_MESSAGES_IN_MEMORY:]
            
        await interaction.followup.send(bot_reply[:2000])
    else:
        await interaction.followup.send(f"Меня отпиздили ногами {last_error[:50]}")

# ---------------------------------------------------
# КОМАНДА 2: ВЕЖЛИВЫЙ АССИСТЕНТ (/а)
# ---------------------------------------------------
@client.tree.command(name="а", description="Просто ИИ-помощник")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(текст="Твой вопрос, задача или просьба написать код")
async def assistant_command(interaction: discord.Interaction, текст: str):
    await interaction.response.defer()
    user_id = interaction.user.id
    
    if user_id not in ASSISTANT_MEMORY:
        ASSISTANT_MEMORY[user_id] = []
        
    messages_to_send = [{"role": "system", "content": ASSISTANT_PERSONALITY}]
    messages_to_send.extend(ASSISTANT_MEMORY[user_id])
    messages_to_send.append({"role": "user", "content": f"Пользователь {interaction.user.name} спрашивает: {текст}"})
    
    bot_reply = None
    last_error = ""
    
    for model in FREE_MODELS:
        try:
            response = await ai_client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                temperature=0.5 # Низкая температура, чтобы код и ответы были логичными и точными
            )
            bot_reply = response.choices[0].message.content
            break 
        except Exception as e:
            last_error = str(e)
            continue 
            
    if bot_reply:
        ASSISTANT_MEMORY[user_id].append({"role": "user", "content": f"Пользователь {interaction.user.name} спрашивает: {текст}"})
        ASSISTANT_MEMORY[user_id].append({"role": "assistant", "content": bot_reply})
        
        if len(ASSISTANT_MEMORY[user_id]) > MAX_MESSAGES_IN_MEMORY:
            ASSISTANT_MEMORY[user_id] = ASSISTANT_MEMORY[user_id][-MAX_MESSAGES_IN_MEMORY:]
            
        await interaction.followup.send(bot_reply[:2000])
    else:
        await interaction.followup.send(f"Произошла техническая ошибка: {last_error[:50]}")

@client.event
async def on_ready():
    print(f'Бот ({client.user}) запущен! Доступны две личности: /г (Глитч) и /а (Ассистент)')

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    print("Запуск Дискорд клиента...")
    client.run(DISCORD_TOKEN)
