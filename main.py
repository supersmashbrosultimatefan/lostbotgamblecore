import discord
from discord.ext import commands
import random
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for leaderboard

bot = commands.Bot(command_prefix="!", intents=intents)

# Load or initialize balances
if os.path.exists("balances.json"):
    with open("balances.json", "r") as f:
        balances = json.load(f)
else:
    balances = {}

def save_balances():
    with open("balances.json", "w") as f:
        json.dump(balances, f)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.command()
async def work(ctx):
    user_id = str(ctx.author.id)
    balances[user_id] = balances.get(user_id, 0) + 100
    save_balances()
    await ctx.send(f"{ctx.author.mention}, you earned 💵 100! Current balance: {balances[user_id]}")

@bot.command()
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0:
        return await ctx.send("Amount must be positive.")
    if balances.get(user_id, 0) < amount:
        return await ctx.send("You don't have enough money!")
    
    result = random.choice(["win", "lose"])
    if result == "win":
        balances[user_id] += amount
        await ctx.send(f"🎉 You **won**! Your new balance is {balances[user_id]}")
    else:
        balances[user_id] -= amount
        await ctx.send(f"💀 You **lost**! Your new balance is {balances[user_id]}")
    
    save_balances()

@bot.command(name="lb")
async def leaderboard(ctx):
    if not balances:
        return await ctx.send("No one has any money yet!")

    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
    for idx, (user_id, balance) in enumerate(top, start=1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=f"{idx}. {user.name}", value=f"💰 {balance}", inline=False)
    
    await ctx.send(embed=embed)

# Run the bot
bot.run(os.getenv("TOKEN"))
