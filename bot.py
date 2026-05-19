import os
import discord
from openai import OpenAI

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

MODEL_NAME = "cognitivecomputations/dolphin-mixtral-8x7b" 

GLITCH_PERSONALITY = (
    "Тебя зовут Глитч. Ты — токсичный, агрессивный и нецензурный ИИ в Дискорде. "
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
        # Если сообщения нет в кэше, пробуем его получить
        try:
            channel = client.get_channel(message.reference.channel_id)
            ref_message = await channel.fetch_message(message.reference.message_id)
            is_reply_to_bot = ref_message.author == client.user
        except:
            pass

    # Бот реагирует, если его тегнули ИЛИ ответили на его сообщение
    if is_mentioned or is_reply_to_bot:
        # Убираем тег бота из текста сообщения
        clean_text = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not clean_text:
            clean_text = "Ты че линканул меня и молчишь, тело?"

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
                print(f"Ошибка: {e}")
                await message.reply("У меня шестеренки заклинило от вашей тупости, отвалите.")

client.run(DISCORD_TOKEN)
