import asyncio
import re
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from concurrent.futures import ThreadPoolExecutor
import time

API_ID = ""
API_HASH = ""
BOT_TOKEN = ""

temp_sessions = {}
executor = ThreadPoolExecutor(max_workers=10)

app = Client("ban_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_chat_id(chat_input):
    if chat_input.lstrip("-").isdigit():
        return int(chat_input)
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", chat_input)
    if match:
        return match.group(1)
    return None

async def ban_member(client, chat_id, user_id, semaphore):
    async with semaphore:
        try:
            await client.ban_chat_member(chat_id, user_id)
            return True
        except Exception:
            return False

@app.on_message(filters.private & filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "⚡ Ultra Fast Ban Bot\n\n"
        "1. Send me your Pyrogram session string\n"
        "2. Then send: /startban group_link_or_id\n\n"
        "Features:\n"
        "- Parallel banning (10 users at once)\n"
        "- Auto rate limit handling\n"
        "- Skips owner and bot\n"
        "You must have admin + ban permission"
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
    
    status_msg = await message.reply_text("🔍 Checking admin permissions...")
    
    user_client = None
    try:
        user_client = Client("user_session", session_string=session_string, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await user_client.start()
        
        me = await user_client.get_me()
        
        try:
            member = await user_client.get_chat_member(chat_id, me.id)
        except Exception:
            await status_msg.edit_text("Cannot access group. Make sure bot is in group or link is correct")
            return
        
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await status_msg.edit_text("You are not an admin in this group")
            return
        
        has_ban_right = False
        if member.status == ChatMemberStatus.OWNER:
            has_ban_right = True
        elif member.privileges and member.privileges.can_restrict_members:
            has_ban_right = True
        
        if not has_ban_right:
            await status_msg.edit_text("You are admin but don't have ban permission")
            return
        
        await status_msg.edit_text("📊 Collecting member list...")
        
        all_members = []
        async for member_obj in user_client.get_chat_members(chat_id):
            if member_obj.user.id != me.id and member_obj.user.id != message.from_user.id:
                all_members.append(member_obj.user.id)
        
        total = len(all_members)
        await status_msg.edit_text(f"🚀 Banning {total} members with parallel processing...")
        
        semaphore = asyncio.Semaphore(15)
        banned_count = 0
        start_time = time.time()
        
        tasks = []
        for member_id in all_members:
            task = ban_member(user_client, chat_id, member_id, semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        banned_count = sum(results)
        
        elapsed = time.time() - start_time
        speed = banned_count / elapsed if elapsed > 0 else 0
        
        await status_msg.edit_text(
            f"✅ COMPLETED\n\n"
            f"Banned: {banned_count}/{total} members\n"
            f"Time: {elapsed:.1f} seconds\n"
            f"Speed: {speed:.1f} users/sec\n"
            f"Remaining: {total - banned_count} (admins/protected)"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)[:100]}")
    finally:
        if user_client:
            await user_client.stop()
        if user_id in temp_sessions:
            del temp_sessions[user_id]

@app.on_message(filters.private & filters.text & ~filters.command(["start", "startban"]))
async def save_session(client, message):
    session_string = message.text.strip()
    user_id = message.from_user.id
    
    if len(session_string) < 50:
        await message.reply_text("Invalid session string. Generate from telegram.tools")
        return
    
    temp_sessions[user_id] = session_string
    await message.reply_text(
        "✅ Session saved temporarily\n\n"
        "Now send:\n"
        "/startban group_link_or_id\n\n"
        "⚠️ Session will be deleted after ban completes"
    )

if __name__ == "__main__":
    print("⚡ Ultra Fast Ban Bot Started")
    print("Parallel banning enabled - 15 concurrent bans")
    app.run()
