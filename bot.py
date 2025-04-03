import os, logging, sqlite3, re
from telethon import TelegramClient, events, functions
from dotenv import load_dotenv

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)

bot_s = TelegramClient('bot_subs', os.environ['API_ID'], os.environ['API_HASH']).start(bot_token=os.environ['BOT_TOKEN_S'])
bot_c = TelegramClient('bot_cont', os.environ['API_ID'], os.environ['API_HASH']).start(bot_token=os.environ['BOT_TOKEN_C'])
conn = sqlite3.connect('database.db')

def db_put(key, value):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS data (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT OR REPLACE INTO data (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
def db_get(key, default=None):
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM data WHERE key=?", (key,))
    row = cursor.fetchone()
    return default if not row else row[0]
async def handle_msg(event):
    text = "Unknown command"
    if event.message.text == '/start':
        text = "Welcome!"
    elif event.message.text == '/join':
        with open('join.txt', 'r', encoding='utf-8') as f:
            text = f.read()
    elif event.message.text == '/jointextm' and event.message.is_reply:
        msg = await event.get_reply_message()
        with open('join.txt', 'w', encoding='utf-8') as f:
            f.write(msg.text)
        text = "Join message saved"
    elif event.message.text == '/sample':
        sample_channel = db_get('sample_channel', os.environ['SAMPLE_CHANNEL'])
        invite = await bot_c(functions.messages.ExportChatInviteRequest(peer=int(sample_channel), usage_limit=1))
        text = f"Join: {invite.link}"
    elif event.message.text.startswith('/sampleidm'):
        m = re.match(r'^/sampleidm (-?\d+)$', event.message.text)
        if m:
            db_put('sample_channel', m[1])
            text = "Sample channel ID saved"
    elif event.message.text.startswith('/sub'):
        m = re.match(r'^/sub (.+) (-?\d+)$', event.message.text)
        if m:
            db_put(m[1], m[2])
            text = "Target added"
    await event.respond(text)

@bot_s.on(events.ChatAction)
async def handler(event):
    if not event.original_update.invite:
        return
    target = db_get(event.original_update.invite.title)
    if not target:
        return
    chat_id = event.original_update.new_participant.user_id
    try:
        invite = await bot_c(functions.messages.ExportChatInviteRequest(peer=int(target), usage_limit=1))
        await bot_c.send_message(chat_id, f"Join: {invite.link}")
    except Exception as e:
        await event.respond(f"Error: {repr(e)}")
@bot_c.on(events.NewMessage(func=lambda e: e.is_private))
async def handler(event):
    try:
        await handle_msg(event)
    except Exception as e:
        await event.respond(f"Error: {repr(e)}")

with bot_s:
    bot_s.run_until_disconnected()
