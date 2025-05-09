from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands, tasks
from collections import defaultdict
import json

# === Flask server to stay alive (for UptimeRobot) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

message_counts = defaultdict(int)
DATA_FILE = "message_counts.json"

# Load message counts
def load_message_counts():
    global message_counts
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            message_counts.update({int(k): int(v) for k, v in data.items()})
        print("Loaded message counts.")
    except FileNotFoundError:
        print("No message_counts.json found. Starting fresh.")
    except Exception as e:
        print(f"Error loading message counts: {e}")

# Save message counts
def save_message_counts():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(message_counts, f)
        print("Saved message counts.")
    except Exception as e:
        print(f"Error saving message counts: {e}")

# Replace with your server and channel ID
GUILD_ID = 1367427041565212732
CHANNEL_ID = 1368220767459872799
leaderboard_message = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update_leaderboard.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    message_counts[message.author.id] += 1
    save_message_counts()
    await bot.process_commands(message)

@tasks.loop(minutes=5)
async def update_leaderboard():
    global leaderboard_message
    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(CHANNEL_ID)

    if not guild or not channel:
        print("Guild or channel not found. Check your IDs.")
        return

    top_users = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    description = "\n".join(
        [f"<@{user_id}> — {count} messages" for user_id, count in top_users]
    )

    embed = discord.Embed(title="Top Active Users", description=description, color=0x00ff00)

    if leaderboard_message:
        await leaderboard_message.edit(embed=embed)
    else:
        leaderboard_message = await channel.send(embed=embed)

# === Run Bot ===
keep_alive()
load_message_counts()
token = os.environ.get("TOKEN")
bot.run(token)
