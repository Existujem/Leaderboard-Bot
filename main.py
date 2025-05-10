from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands, tasks
from collections import defaultdict
import json

# === Flask server to stay alive ===
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

# Load message counts
message_counts = defaultdict(int)
if os.path.exists("message_counts.json"):
    with open("message_counts.json", "r") as f:
        data = json.load(f)
        for user_id, count in data.items():
            message_counts[int(user_id)] = count

# Your actual guild and channel IDs
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

    # Save updated data
    with open("message_counts.json", "w") as f:
        json.dump({str(user_id): count for user_id, count in message_counts.items()}, f)

# === Run Bot ===
keep_alive()
token = os.environ.get("TOKEN")
bot.run(token)
