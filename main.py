import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# --- Flask setup for uptime pinging ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load balances from file or initialize
try:
    with open("balances.json", "r") as f:
        balances = json.load(f)
except:
    balances = {}

def save_balances():
    with open("balances.json", "w") as f:
        json.dump(balances, f)

cooldowns = {}  # Tracks work and daily cooldowns

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def work(ctx):
    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last_used = cooldowns.get(user_id, {}).get('work')

    if last_used and now - last_used < timedelta(minutes=30):
        await ctx.send("You must wait 30 minutes before using !work again.")
        return

    balances[user_id] = balances.get(user_id, 0) + 100
    cooldowns.setdefault(user_id, {})['work'] = now
    save_balances()
    await ctx.send(f"You worked and earned 100 coins! You now have {balances[user_id]}.")

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last_used = cooldowns.get(user_id, {}).get('daily')

    if last_used and now - last_used < timedelta(days=1):
        await ctx.send("You already claimed your daily reward today!")
        return

    balances[user_id] = balances.get(user_id, 0) + 1000
    cooldowns.setdefault(user_id, {})['daily'] = now
    save_balances()
    await ctx.send(f"Daily claimed! You received 1000 coins. You now have {balances[user_id]}.")

@bot.command()
async def balance(ctx, target: discord.Member = None):
    if target is None:
        target = ctx.author
    user_id = str(target.id)
    bal = balances.get(user_id, 0)
    await ctx.send(f"{target.name} has {bal} coins.")

@bot.command()
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    balance_amt = balances.get(user_id, 0)

    if amount <= 0:
        await ctx.send("Please enter a valid amount.")
        return
    if balance_amt < amount:
        await ctx.send("You don't have enough coins to gamble that amount.")
        return

    if os.urandom(1)[0] < 128:  # 50% chance
        winnings = amount * 2
        balances[user_id] = balance_amt + amount  # Net gain
        await ctx.send(f"You won! You now have {balances[user_id]} coins.")
    else:
        balances[user_id] = balance_amt - amount
        await ctx.send(f"You lost! You now have {balances[user_id]} coins.")

    save_balances()

@bot.command()
async def lb(ctx):
    sorted_bal = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    leaderboard = []
    for i, (uid, bal) in enumerate(sorted_bal, 1):
        member = ctx.guild.get_member(int(uid))
        name = member.name if member else f"User {uid}"
        leaderboard.append(f"{i}. {name}: {bal} coins")
    await ctx.send("\n".join(leaderboard))

@bot.command()
async def rob(ctx, target: discord.Member):
    user_id = str(ctx.author.id)
    target_id = str(target.id)

    if target_id not in balances or balances[target_id] < 10:
        await ctx.send("That user doesn't have enough money to rob!")
        return

    if os.urandom(1)[0] < 128:
        steal_amount = int(balances[target_id] * (0.1 + (os.urandom(1)[0] % 16) / 100))
        balances[user_id] = balances.get(user_id, 0) + steal_amount
        balances[target_id] -= steal_amount
        await ctx.send(f"You successfully robbed {steal_amount} coins from {target.name}!")
    else:
        await ctx.send("Your robbery failed!")

    save_balances()

@bot.command()
async def tip(ctx, target: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    target_id = str(target.id)

    if balances.get(sender_id, 0) < amount or amount <= 0:
        await ctx.send("You don't have enough coins or invalid amount.")
        return

    balances[sender_id] -= amount
    balances[target_id] = balances.get(target_id, 0) + amount
    save_balances()
    await ctx.send(f"You tipped {target.name} {amount} coins!")

@bot.command()
async def give(ctx, target: discord.Member, amount: int):
    if str(ctx.author.id) != "669836907815108609":
        await ctx.send("You are not authorized to use this command.")
        return

    target_id = str(target.id)
    balances[target_id] = balances.get(target_id, 0) + amount
    save_balances()
    await ctx.send(f"Gave {amount} coins to {target.name}!")

# --- Start everything ---
keep_alive()
bot.run(os.getenv("TOKEN"))
