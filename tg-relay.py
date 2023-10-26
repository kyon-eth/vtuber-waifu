import asyncio
import websockets
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from rich.logging import RichHandler
import logging
import threading
from config import *

WS_URI = 'ws://localhost:8765'

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("waifuchat")

websocket = None  # Global variable to keep the WebSocket connection

async def manage_websocket():
    global websocket
    while True:
        try:
            async with websockets.connect(WS_URI, ping_interval=None) as ws:
                websocket = ws
                async for message in ws:
                    # Handle incoming WebSocket messages if necessary
                    print(f"Received: {message}")
        except Exception as e:
            print(f"WebSocket Connection Error: {e}, Retrying...")
            await asyncio.sleep(1)


async def send_to_websocket(message: str):
    global websocket
    if websocket:
        try:
            await websocket.send(message)
        except Exception as e:
            print(f"Send Message Error: {e}")


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_id = update.message.from_user.id
    group_id = update.message.chat.id
    
    if group_id != user_id:
        logger.info(f"Group ({group_id}) - User ({user_id}): {message_text}")
        await send_to_websocket(f"User ({user_id}): {message_text}")
    else:
        logger.warning(f"[PRIVATE MSG] User ({user_id}): {message_text}")


def run_websocket_manager():
    asyncio.new_event_loop().run_until_complete(manage_websocket())

# Start the WebSocket manager in a new thread
threading.Thread(target=run_websocket_manager, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle_messages))
app.run_polling()
