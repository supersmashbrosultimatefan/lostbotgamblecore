import discord
from discord.ext import commands
import random
import json
import os
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

app = Flask('')

@app.route('/'
)
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load or initialize balances
if not os.path.exists("balances.json"):
    with open("balances.json", "w") as f:
        json.dump({}, f)

with open("balances.json", "r") as f:
    balances = json.load(f)

cooldowns = {}
daily_cooldowns = {}
rob_cooldowns = {}

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')

@bot.command()
@commands.cooldown(1, 1800, commands.BucketType.user)  # 30 minutes
async def work(ctx):
    user_id = str(ctx.author.id)
    balances[user_id] = balances.get(user_id, 0) + 100
    await ctx.send(f"{ctx.author.mention}, you earned 100 coins!")
    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last_claim = daily_cooldowns.get(user_id)

    if last_claim and now - last_claim < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last_claim)
        await ctx.send(f"You already claimed your daily reward. Try again in {remaining}.")
        return

    balances[user_id] = balances.get(user_id, 0) + 1000
    daily_cooldowns[user_id] = now
    await ctx.send(f"{ctx.author.mention}, you claimed 1000 coins as your daily reward!")
    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.command()
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)
    bal = balances.get(user_id, 0)
    await ctx.send(f"{target.mention} has {bal} coins.")

@bot.command()
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    if balances.get(user_id, 0) < amount:
        await ctx.send("You don't have enough coins.")
        return

    if random.random() < 0.5:
        balances[user_id] -= amount
        await ctx.send(f"{ctx.author.mention}, you lost {amount} coins!")
    else:
        balances[user_id] += amount
        await ctx.send(f"{ctx.author.mention}, you won {amount} coins!")

    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.command()
async def lb(ctx):
    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="Leaderboard", color=discord.Color.gold())
    for i, (user_id, balance) in enumerate(top, 1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=f"#{i} - {user.name}", value=f"{balance} coins", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def rob(ctx, target: discord.Member):
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    now = datetime.utcnow()

    last_rob = rob_cooldowns.get(user_id)
    if last_rob and now - last_rob < timedelta(minutes=60):
        remaining = timedelta(minutes=60) - (now - last_rob)
        await ctx.send(f"You must wait {remaining} before robbing again.")
        return

    if balances.get(target_id, 0) < 100:
        await ctx.send("Target doesn't have enough coins to rob.")
        return

    if random.random() < 0.5:
        await ctx.send(f"{ctx.author.mention} tried to rob {target.mention} and failed!")
    else:
        stolen_percent = random.uniform(0.1, 0.25)
        stolen_amount = int(balances.get(target_id, 0) * stolen_percent)
        balances[target_id] -= stolen_amount
        balances[user_id] = balances.get(user_id, 0) + stolen_amount
        await ctx.send(f"{ctx.author.mention} robbed {stolen_amount} coins from {target.mention}!")

    rob_cooldowns[user_id] = now
    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.command()
async def tip(ctx, target: discord.Member, amount: int):
    user_id = str(ctx.author.id)
    target_id = str(target.id)

    if balances.get(user_id, 0) < amount:
        await ctx.send("You don't have enough coins to tip.")
        return

    balances[user_id] -= amount
    balances[target_id] = balances.get(target_id, 0) + amount
    await ctx.send(f"{ctx.author.mention} tipped {amount} coins to {target.mention}!")
    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.command()
async def give(ctx, target: discord.Member, amount: int):
    if str(ctx.author.id) != "669836907815108609":
        await ctx.send("You don't have permission to use this command.")
        return
    balances[str(target.id)] = balances.get(str(target.id), 0) + amount
    await ctx.send(f"Gave {amount} coins to {target.mention}.")
    with open("balances.json", "w") as f:
        json.dump(balances, f)

keep_alive()
bot.run(os.getenv("TOKEN"))
