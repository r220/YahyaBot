from telethon.sessions import StringSession
from telethon import TelegramClient, events
from telethon.tl import types
import json
import logging
from dotenv import load_dotenv
from os import getenv
import asyncio


logging.basicConfig(
    format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING
)
load_dotenv()

# TELEGRAM CLIENT SETUP
api_id = int(getenv('API_KEY'))  
api_hash = getenv('API_HASH')
SESSION = getenv('SESSION')
client = TelegramClient(StringSession(SESSION), api_id, api_hash)
forwarded_ch = int(getenv('FORWARDED_CHANNEL'))
JSON = 'data.json'
BOT = int(getenv('BOT')) 

# json file setup
file = ''
file_lists = {
    "remained_users": [],
    "allowed_users": [],
    "blocked_users": [],
    "allowed_words": [],
    "blocked_words": []
}

def load_json():
    global file
    with open(JSON, 'r') as f:
        file = json.load(f)
        file_lists["remained_users"] = file["users"]["remained"]
        file_lists['allowed_users'] = file['users']['allowed']
        file_lists["blocked_users"] = file["users"]["blocked"]
        file_lists['allowed_words'] = file['words']['allowed']
        file_lists["blocked_words"] = file["words"]["blocked"]

counter = 0
# BOT update event
# @client.on(events.NewMessage(incoming=True))
@client.on(events.NewMessage(outgoing=True))
async def my_event_handler(event):
    global counter
    counter += 1
    print(counter)
    
    # CHECK msg
    chat_id = event.chat_id
    message = event.message.message
    print(message)
    # extra (BOT): check added/removed channels/groups
    if chat_id == BOT and message == '/update':
        msgs = await refresh()
        for i in range(0, len(msgs), 30):
            await client.send_message(BOT, "\n".join(msgs[i:i+100]))
        print('succeed')
        return

# -----------------------------------------------------         
# Detect when a chat/channel is deleted or inaccessible
# ----------------------------------------------------- 
async def refresh():
    global file
    dialogs = await client.get_dialogs()
    
    current = [
        {
            "id": str(d.id),
            "name": d.entity.title
        }
        for d in dialogs
        if isinstance(d.entity, (types.Chat, types.Channel))
    ]
    
    s = file['users']
    users = s['remained'] + s['allowed'] + s['blocked']
    added = [c for c in current if c["id"] not in {u["id"] for u in users}]
    removed = [u for u in users if u["id"] not in {c["id"] for c in current}]
    msg = []
    if not (added or removed):
        msg = ["🤖 no changes to update.."]
    else:
        # ADDED
        if added:
            msg.append("🟢 You Joined to the following (channels/groups): \n")
            for d in added:
                file['users']['remained'].append(d)
                msg.append(f"{d['name']}")
        # REMOVED
        if removed:
            msg.append("\n🔴 You Left from the following (channels/groups): \n")
            for d in removed:
                if d["id"] in [i["id"] for i in s['allowed']]:
                    print('removed from allowed')
                    file['users']['allowed'].remove(d)
                elif d["id"] in [i["id"] for i in s['blocked']]:
                    file['users']['blocked'].remove(d)
                elif d["id"] in [i["id"] for i in s['remained']]:
                    file['users']['remained'].remove(d)
                msg.append(f"{d['name']}")         

        with open(JSON, "w") as f:
            json.dump(file, f, indent = 4)
        load_json()
    return msg

with client:
    load_json()
    print('Update running')
    client.run_until_disconnected()