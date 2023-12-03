import os
import discord
from utils import *
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import commands, tasks
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Get the discordbot token from .env file
load_dotenv()
TOKEN = os.getenv('TOKEN')
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASS = os.getenv("DATABASE_PASS")

intents = discord.Intents.default()
intents.message_content = True

uri = f"mongodb+srv://{DATABASE_USER}:{DATABASE_PASS}@courseseatbotdatabase.mj5n16n.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["database"]
servers = db["servers"]

# Temporary solution until we get a database running
loops = 0
bot = commands.Bot(command_prefix='$', intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update.start()
    for guild in bot.guilds:
        if not servers.find_one({"_id": guild.id}):
            servers.insert_one(
                {"channel_id": None, "refresh": 5, "classes": [], "_id": guild.id})


@bot.event
async def on_guild_join(guild):
    print("Joined guild {guild.name}")
    server = {"channel_id": None, "refresh": 5, "classes": [], "_id": guild.id}
    servers.insert_one(server)


@bot.command()
async def set_channel(ctx):
    servers.update_one({"_id": ctx.guild.id}, {
        "$set": {"channel_id": ctx.channel.id}})
    channel = ctx.channel
    await channel.send(f"Set bot to current channel, {channel.name}")


@bot.command()
async def set_refresh(ctx, arg):
    try:
        refresh = int(arg)
    except ValueError:
        await ctx.channel.send("Please input an integer.")
        return
    servers.update_one({"_id": ctx.guild.id}, {
        "$set": {"refresh": refresh}})
    channel = ctx.channel
    await channel.send(f"Set refresh rate to every {refresh} minutes")

# pass in url to watch the class for changes in seat availability


@bot.command()
async def add_class(ctx, *args):
    if (len(args) == 0):
        await ctx.channel.send("Please send a valid url.")
        return
    elif (len(args) == 1):
        args.append(0)

    try:
        reserved_seats = int(args[1])
    except ValueError:
        reserved_seats = 0
    url = args[0]
    server = servers.find_one({"_id": ctx.guild.id})
    channel = bot.get_channel(server["channel_id"])
    if channel is None:
        await ctx.channel.send("Set your channel first with $set_channel")
        return
    servers.update_one({"_id": ctx.guild.id}, {
        "$push": {"classes": {"url": url, "reserved_seats": reserved_seats, "seats": -1}}})
    await channel.send(f"Watching url {url}")


@bot.command()
async def list_classes(ctx):
    server = servers.find_one({"_id": ctx.guild.id})
    channel = bot.get_channel(server["channel_id"])
    i = 1
    await channel.send("Watching the following classes:")
    for cls in server["classes"]:
        await channel.send(f"{i}. Url: {cls['url']}, Reserved Seats: {cls['reserved_seats']}, Current Available Seats: {cls['seats']}")
        i += 1


@bot.command()
async def delete_class(ctx, arg):
    server = servers.find_one({"_id": ctx.guild.id})
    channel = bot.get_channel(server["channel_id"])
    try:
        class_num = int(arg)
    except ValueError:
        await channel.send(f"That is not a valid class number. Check out $list_classes to view your current monitored classes and their ids.")
        return
    if class_num - 1 >= len(server["classes"]):
        await channel.send("The number you entered is not in scope. Check out $list_classes to veiw your current monitored classes and their ids.")
        return
    server["classes"].pop(class_num - 1)
    servers.update_one({"_id": ctx.guild.id}, {
                       "$set": {"classes": server["classes"]}})


@tasks.loop(minutes=1.0)
async def update():
    global loops
    for guild in bot.guilds:
        server = servers.find_one({"_id": guild.id})
        channel = bot.get_channel(server["channel_id"])
        if loops % server["refresh"] == 0:
            for cls in server["classes"]:
                seats = cls["seats"]
                url = cls["url"]
                reserved_seats = cls["reserved_seats"]
                available = await check_url(seats, url, reserved_seats)
                if available != seats:
                    cls["seats"] = available
                    await channel.send(f"The number of open seats for {url} has changed to {available}")
            servers.update_one({"_id": guild.id}, {
                "$set": {"classes": server["classes"]}})
    loops += 1

bot.run(TOKEN)
