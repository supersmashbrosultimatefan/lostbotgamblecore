import discord
import json
import os
import random
import asyncio
from discord.ext import commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = "balances.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_balances():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_balances(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(data, user_id):
    if str(user_id) not in data:
        data[str(user_id)] = {"balance": 0, "last_work": "1970-01-01", "last_daily": "1970-01-01"}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command(name="бал")
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    data = load_balances()
    ensure_user(data, user.id)
    await ctx.send(f"{user.display_name}'s balance: {data[str(user.id)]['balance']} coins")

@bot.command(name="раб")
async def work(ctx):
    data = load_balances()
    user_id = str(ctx.author.id)
    ensure_user(data, user_id)

    last_work = datetime.fromisoformat(data[user_id]["last_work"])
    now = datetime.utcnow()
    if now - last_work >= timedelta(minutes=30):
        data[user_id]["balance"] += 100
        data[user_id]["last_work"] = now.isoformat()
        save_balances(data)
        await ctx.send(f"{ctx.author.mention} пахал на шахте и заработал 100 денюжек")
    else:
        remaining = timedelta(minutes=30) - (now - last_work)
        await ctx.send(f"{ctx.author.mention}, свали нахуй и возвращайся через {remaining.seconds // 60} минут.")

@bot.command(name="награда")
async def daily(ctx):
    data = load_balances()
    user_id = str(ctx.author.id)
    ensure_user(data, user_id)

    last_daily = datetime.fromisoformat(data[user_id]["last_daily"])
    now = datetime.utcnow()
    if now - last_daily >= timedelta(days=1):
        data[user_id]["balance"] += 1000
        data[user_id]["last_daily"] = now.isoformat()
        save_balances(data)
        await ctx.send(f"{ctx.author.mention} забрал награду в размере 1000!")
    else:
        next_claim = timedelta(days=1) - (now - last_daily)
        hours = next_claim.seconds // 3600
        minutes = (next_claim.seconds % 3600) // 60
        await ctx.send(f"{ctx.author.mention}, приходи через {hours}ч {minutes}мин чтобы забрать ДЕНЮЖКИИ")

@bot.command(name="ограбить")
async def rob(ctx, target: discord.Member):
    if target == ctx.author:
        await ctx.send("You can't rob yourself, chill 😅")
        return

    data = load_balances()
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    ensure_user(data, user_id)
    ensure_user(data, target_id)

    if data[target_id]["balance"] < 100:
        await ctx.send(f"{target.display_name} не имеет никаких денег вообще ")
        return

    success = random.choice([True, False])
    if success:
        steal_percent = random.randint(10, 25)
        stolen_amount = data[target_id]["balance"] * steal_percent // 100
        data[target_id]["balance"] -= stolen_amount
        data[user_id]["balance"] += stolen_amount
        save_balances(data)
        await ctx.send(f"{ctx.author.mention} успешно ограбил {target.display_name} и украл {stolen_amount} денег")
    else:
        await ctx.send(f"{ctx.author.mention} попытался ограбить {target.display_name} но у него ничего нахуй не получилось!")

@bot.command(name="донат")
async def tip(ctx, target: discord.Member, amount: int):
    if target == ctx.author:
        await ctx.send("хуй тебе")
        return

    if amount <= 0:
        await ctx.send("нормальную цифру поставь олух")
        return

    data = load_balances()
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    ensure_user(data, user_id)
    ensure_user(data, target_id)

    if data[user_id]["balance"] < amount:
        await ctx.send("нету у тебя столько олух")
        return

    data[user_id]["balance"] -= amount
    data[target_id]["balance"] += amount
    save_balances(data)
    await ctx.send(f"{ctx.author.mention} пожертвовал {amount} денег к {target.display_name}")

@bot.command(name="лб")
async def leaderboard(ctx):
    data = load_balances()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)
    top = sorted_users[:10]

    msg = "**🏆 Leaderboard 🏆**\n"
    for i, (uid, info) in enumerate(top, 1):
        user = await bot.fetch_user(int(uid))
        msg += f"{i}. {user.display_name} - {info['balance']} coins\n"

    await ctx.send(msg)


@bot.command(name="выдать")
async def give(ctx, target: discord.Member, amount: int):
    if ctx.author.id != YOUR_USER_ID_HERE:
        await ctx.send("You are not authorized to use this command.")
        return

    global balances  # <-- Add this line to access the global variable

    balances[str(target.id)] = balances.get(str(target.id), 0) + amount
    save_balances()
    await ctx.send(f"Gave {amount} to {target.mention}. Their new balance is {balances[str(target.id)]}")


@bot.command()
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)

    # Check if user has enough balance
    if user_id not in balances or balances[user_id] < amount:
        await ctx.send("You don't have enough currency to gamble that amount.")
        return

    # Perform 50/50 gamble
    if random.choice([True, False]):
        balances[user_id] += amount * 2  # Win: double the bet
        await ctx.send(f"You won! 🎉 Your new balance is {balances[user_id]}")
    else:
        balances[user_id] -= amount  # Lose: lose the bet
        await ctx.send(f"You lost! 💸 Your new balance is {balances[user_id]}")

    save_balances()





# Run your bot
bot.run(os.getenv("TOKEN"))
