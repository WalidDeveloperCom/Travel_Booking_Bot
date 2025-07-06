import subprocess
import sys
import os

# Start FastAPI server
fastapi_cmd = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--reload']
# Start Telegram bot
bot_cmd = [sys.executable, 'bot/bot.py']

fastapi_proc = subprocess.Popen(fastapi_cmd)
bot_proc = subprocess.Popen(bot_cmd)

try:
    fastapi_proc.wait()
    bot_proc.wait()
except KeyboardInterrupt:
    fastapi_proc.terminate()
    bot_proc.terminate() 