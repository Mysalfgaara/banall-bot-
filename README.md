# Ban All Telegram Bot

## Environment Variables

Set these in Heroku or Railway:

- `API_ID` - Your Telegram API ID from my.telegram.org
- `API_HASH` - Your Telegram API Hash from my.telegram.org  
- `BOT_TOKEN` - Your bot token from @BotFather

## Deploy to Heroku

1. Push code to GitHub
2. Create new app on Heroku
3. Add config vars (API_ID, API_HASH, BOT_TOKEN)
4. Deploy from GitHub

## Deploy to Railway

1. Push code to GitHub
2. Create new project on Railway
3. Add environment variables
4. Connect GitHub repo
5. Railway auto-detects Dockerfile

## How to Use

1. Generate session string from telegram.tools
2. Send session to bot
3. Send /startban group_link_or_id
