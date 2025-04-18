import discord
from discord.ext import commands, tasks
import random
import asyncio
import json
import os
import datetime
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
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

DATA_FILE = 'balances.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

with open(DATA_FILE, 'r') as f:
    balances = json.load(f)

cooldowns = {
    'work': {},
    'daily': {},
    'rob': {}
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

def save_balances():
    with open(DATA_FILE, 'w') as f:
        json.dump(balances, f)

@bot.command(name="раб")
async def work(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.utcnow()
    last_work = cooldowns['work'].get(user_id)

    if last_work and (now - last_work).total_seconds() < 1800:
        remaining = datetime.timedelta(seconds=1800) - (now - last_work)
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        await ctx.send(f"Подожди {mins} минут и {secs} секунд перед тем как идти на работу.")
        return

    balances[user_id] = balances.get(user_id, 0) + 100
    cooldowns['work'][user_id] = now
    save_balances()
    await ctx.send("Ты отработал смену в гей клубе и получил 100 денег")

@bot.command(name="награда")
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.utcnow()
    last_daily = cooldowns['daily'].get(user_id)

    if last_daily and (now - last_daily).total_seconds() < 86400:
        remaining = datetime.timedelta(seconds=86400) - (now - last_daily)
        hrs, rem = divmod(int(remaining.total_seconds()), 3600)
        mins, secs = divmod(rem, 60)
        await ctx.send(f"Подожди {hrs} часов, {mins} минут и {secs} секунд перед тем как забрать награду ты жирная жопа")
        return

    balances[user_id] = balances.get(user_id, 0) + 1000
    cooldowns['daily'][user_id] = now
    save_balances()
    await ctx.send("ты забрал награду в размере 1000 денег за то что ты существуешь!")

@bot.command(name="бал")
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    user_id = str(user.id)
    bal = balances.get(user_id, 0)
    await ctx.send(f"у {user.display_name} на балансе {bal} денег")

@bot.command(name="сыграть")
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    bal = balances.get(user_id, 0)

    if amount <= 0:
        await ctx.send("че конченный что ли")
        return

    if bal < amount:
        await ctx.send("нету у тебя столько денег")
        return

    if random.random() < 0.5:
        balances[user_id] += amount
        await ctx.send(f"ты ПОБЕДИЛ🤑🤑🫰!!!! теперь твой баланс: {balances[user_id]} ")
    else:
        balances[user_id] -= amount
        await ctx.send(f"ты ПРОЕБАЛСЯ🫵😂!! теперь твой баланс: {balances[user_id]} ")

    save_balances()

@bot.command(name="ограбить")
async def rob(ctx, member: discord.Member):
    robber_id = str(ctx.author.id)
    target_id = str(member.id)
    now = datetime.datetime.utcnow()
    last_rob = cooldowns['rob'].get(robber_id)

    if last_rob and (now - last_rob).total_seconds() < 3600:
        remaining = datetime.timedelta(seconds=3600) - (now - last_rob)
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        await ctx.send(f"Подожди {mins} минут и {secs} секунд перед тем как грабить, ты енот")
        return

    if target_id not in balances or balances[target_id] < 100:
        await ctx.send("у бедолаги даже денег нету нахуй грабишь")
        return

    success = random.random() < 0.5
    if success:
        stolen = int(balances[target_id] * random.uniform(0.10, 0.25))
        balances[robber_id] = balances.get(robber_id, 0) + stolen
        balances[target_id] -= stolen
        await ctx.send(f"ты УСПЕШНО ОГРАБИЛ💰💰 {member.display_name} и получил {stolen} денег!!")
    else:
        await ctx.send("ты проебался ахахахах")

    cooldowns['rob'][robber_id] = now
    save_balances()

@bot.command(name="пожертв")
async def tip(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if balances.get(sender_id, 0) < amount or amount <= 0:
        await ctx.send("сука инвалид")
        return

    balances[sender_id] -= amount
    balances[receiver_id] = balances.get(receiver_id, 0) + amount
    save_balances()
    await ctx.send(f"{ctx.author.display_name} пожертвовал {member.display_name} {amount} денег!")

@bot.command(name="лб")
async def lb(ctx):
    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for i, (user_id, bal) in enumerate(top, start=1):
        user = await bot.fetch_user(int(user_id))
        desc += f"{i}. {user.display_name}: {bal} денег\n"
    embed = discord.Embed(title="Таблица лидеров", description=desc)
    await ctx.send(embed=embed)

@bot.command(name="комманды")
async def cmds(ctx):
    commands_list = (
        "!раб - Пропахать на шахтах и получить 100 баксов\n"
        "!награда - Забирать награду в размере 1000 денег просто за то что ты жив\n"
        "!баланс [@user] - Проверить свой или чужой баланс\n"
        "!сыграть <amount> - СЫГРАТЬ В КАЗИНО ПРОДАЙ КВАРТИРУ И СЫНА\n"
        "!ограбить @user - попробовать спиздить денег на халяву\n"
        "!пожертв @user <amount> - будь добрым человеком и отдай денег кому то\n"
        "!лб - Посмотреть таблицу лидеров\n"
        "!выдать @user <количество денег> - (только для лоста uwu) дать денег"
    )
    await ctx.send(f"Here are the available commands:\n\n{commands_list}")

@bot.command(name="выдать")
async def give(ctx, target: discord.Member, amount: int):
    if str(ctx.author.id) != "669836907815108609":  # Replace with your actual Discord user ID
        await ctx.send("размечтался 🫵😂")
        return
    balances[str(target.id)] = balances.get(str(target.id), 0) + amount
    save_balances()
    await ctx.send(f"выдал {amount} денег к {target.display_name} на баланс!")

keep_alive()
bot.run(os.getenv("TOKEN"))
