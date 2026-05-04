import asyncio
import re
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

temp_sessions = {}

app = Client("ban_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_chat_id(chat_input):
    if chat_input.lstrip("-").isdigit():
        return int(chat_input)
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", chat_input)
    if match:
        return match.group(1)
    return None

@app.on_message(filters.private & filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Ban All Bot\n\n"
        "1. Send me your Pyrogram string session from telegram.tools\n"
        "2. Then send: /startban group_link_or_id\n\n"
        "You must have admin + ban permission in the group\n"
        "Your session is never saved - stored only in RAM during ban process"
    )

@app.on_message(filters.private & filters.command("startban"))
async def startban(client, message):
    user_id = message.from_user.id
    
    if user_id not in temp_sessions:
        await message.reply_text("Please send your Pyrogram session string first")
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /startban group_link_or_id")
        return
    
    session_string = temp_sessions[user_id]
    chat_input = message.command[1]
    chat_id = extract_chat_id(chat_input)
    
    if not chat_id:
        await message.reply_text("Invalid group link or ID")
        return
    
    status_msg = await message.reply_text("Checking admin permissions...")
    
    try:
        user_client = Client("user_session", session_string=session_string, api_id=API_ID, api_hash=API_HASH)
        await user_client.start()
        
        target_chat = await user_client.get_chat(chat_id)
        me = await user_client.get_me()
        member = await user_client.get_chat_member(chat_id, me.id)
        
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await status_msg.edit_text("You are not an admin in this group")
            await user_client.stop()
            del temp_sessions[user_id]
            return
        
        has_ban_right = False
        if member.status == ChatMemberStatus.OWNER:
            has_ban_right = True
        elif member.privileges and member.privileges.can_restrict_members:
            has_ban_right = True
        
        if not has_ban_right:
            await status_msg.edit_text("You are admin but don't have ban permission")
            await user_client.stop()
            del temp_sessions[user_id]
            return
        
        await status_msg.edit_text("Starting ban all members...")
        
        banned_count = 0
        async for member_obj in user_client.get_chat_members(chat_id):
            if member_obj.user.id == me.id:
                continue
            if member_obj.user.id == message.from_user.id:
                continue
            
            try:
                await user_client.ban_chat_member(chat_id, member_obj.user.id)
                banned_count += 1
                
                if banned_count % 10 == 0:
                    await status_msg.edit_text(f"Banned {banned_count} members so far...")
                
                await asyncio.sleep(0.5)
            except Exception:
                continue
        
        await status_msg.edit_text(f"Completed! Banned {banned_count} members")
        await user_client.stop()
        del temp_sessions[user_id]
        
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")
        if 'user_client' in locals():
            await user_client.stop()
        del temp_sessions[user_id]

@app.on_message(filters.private & filters.text & ~filters.command(["start", "startban"]))
async def save_session(client, message):
    session_string = message.text.strip()
    user_id = message.from_user.id
    
    if len(session_string) < 50:
        await message.reply_text("Invalid session string. Generate from telegram.tools")
        return
    
    temp_sessions[user_id] = session_string
    await message.reply_text("Session saved temporarily. Now send /startban group_link_or_id")

if __name__ == "__main__":
    print("Ban All Bot Started")
    app.run()
