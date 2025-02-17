import os
from threading import Thread
import discord
import asyncio
import json
from discord.ext import commands
from flask import Flask



WELCOME_CHANNEL_ID  = 1338648634748698634
AUTO_ROLE_ID = 1338654321098765432
ANNOUNCE_CHANNEL_ID = 1335742926025785369
COMMANDS_CHANNEL_ID = 1338648126382149747
TICKET_CHANNEL_ID = 1338964572320829512 
ROLE_ID = 1339723637858500680
GUILD_ID = 1335742926025785366
WARN_CHANNEL_ID = 1339617845394276513
CHANNEL_ID = ANNOUNCE_CHANNEL_ID
TOKEN = os.getenv("DISCORD_TOKEN")

warns = {}

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask server to keep the bot alive
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

def save_message_id(message_id):
    with open("reaction_message.json", "w") as file:
        json.dump({"message_id": message_id}, file)

# Função para carregar o ID da mensagem salva
def load_message_id():
    try:
        with open("reaction_message.json", "r") as file:
            data = json.load(file)
            return data.get("message_id")
    except (FileNotFoundError, json.JSONDecodeError):
        return None

@bot.event
async def on_ready():
    print(f"{bot.user} está online!")

    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(CHANNEL_ID)

    if not guild or not channel:
        print("⚠️ Servidor ou canal não encontrado. Verifique os IDs.")
        return

    message_id = load_message_id()

    if message_id:
        # Tenta pegar a mensagem existente
        try:
            message = await channel.fetch_message(message_id)
            print("✅ Mensagem encontrada! Monitorando reações...")
        except discord.NotFound:
            print("❌ Mensagem não encontrada! Criando uma nova...")
            message = await send_reaction_message(channel)
    else:
        print("📩 Nenhuma mensagem salva! Criando uma nova...")
        message = await send_reaction_message(channel)

    # Garante que a mensagem tenha a reação inicial ✅
    await message.add_reaction("✅")

# Função para enviar a mensagem e salvar o ID
async def send_reaction_message(channel):
    message = await channel.send("👋 Welcome ! React with ✅ to receive o cargo the **Member** role!")
    save_message_id(message.id)
    return message

# Evento quando alguém adiciona uma reação
@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name != "✅":
        return  # Ignora outras reações

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return  # Ignora bots

    role = guild.get_role(ROLE_ID)

    if role not in member.roles:
        await member.add_roles(role)
        print(f"✅ {member} recebeu o cargo de Membro!")

# Evento quando alguém remove a reação
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name != "✅":
        return  # Ignora outras reações

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return  # Ignora bots

    role = guild.get_role(ROLE_ID)

    if role in member.roles:
        await member.remove_roles(role)
        print(f"❌ {member} perdeu o cargo de Membro.")


# 📌 Welcome Message
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"🎉 Welcome, {member.mention}! Please read the rules and e check the  **#annoucements channel** enjoy!")

# 🔨 Kick Command
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Rule violation"):
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("🚫 Use this command in the correct channel!")
        return
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")

# 🔨 Ban Command
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Rule violation"):
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("🚫 Use this command in the correct channel!")
        return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason}")

# ⚠️ Warn Command with Auto-Kick
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="Rule violation"):
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("🚫 Use this command in the correct channel!")
        return
        
    warn_channel = bot.get_channel(WARN_CHANNEL_ID)
    if not warn_channel:
        await ctx.send("🚫 Use this command in the correct channel!")
        return
    else:
        
        if member.id not in warns:
            warns[member.id] = []
    
            warns[member.id].append(reason)
            warn_count = len(warns[member.id])
    
            await ctx.send(f"⚠️ {member.mention} has been warned ({warn_count}/3). Reason: {reason}")
    
            warn_channel = bot.get_channel(WARN_CHANNEL_ID)
            if warn_channel:
                await warn_channel.send(f"⚠️ Warning for {member.mention} | Count: {warn_count}/3 | Reason: {reason}")
    
        if warn_count >= 3:
            await member.kick(reason="Exceeded 3 warnings")
            await ctx.send(f"👢 {member.mention} has been kicked for exceeding 3 warnings!")
            warns[member.id] = []  # Reset warnings after kick
    
# 📢 Announcement Command
@bot.command()
async def announce(ctx, *, message):
    if ctx.channel.id != COMMANDS_CHANNEL_ID:
        await ctx.send("🚫 Use this command in the correct channel!")
        return
    an_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if an_channel:
        await an_channel.send(f"📢 **Announcement:** {message}")
        await ctx.send(f"✅ Announcement sent in {an_channel.mention}!")
    else:
        await ctx.send("⚠️ Announcement channel not found. Please check the configuration.")

# 🎫 Ticket System
@bot.command()
async def ticket(ctx):
    try:
        if ctx.channel.id != TICKET_CHANNEL_ID:
            await ctx.send("🚫 Use this command in the tickets channel!")
            return
        category = discord.utils.get(ctx.guild.categories, name="Tickets")
        if not category:
            category = await ctx.guild.create_category("Tickets")
        ticket_channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", category=category)
        await ticket_channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        await ticket_channel.send(f"🎫 {ctx.author.mention}, your ticket has been created! Please describe your issue.")

    except Exception as e:
        print(f"Erro no comando ticket: {e}")
        await ctx.send(f"❌ Ocorreu um erro ao criar o ticket: `{str(e)}`")

@bot.command()
async def closeticket(ctx):
    """closes the ticket channel if it belongs to the correct category."""
    if ctx.channel.category and ctx.channel.category.name.lower() == "tickets":
        await ctx.send(f"🔒 {ctx.author.mention} closed this ticket. the channel will be deleted in 5 seconds.")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("🚫 this command can only be used in a ticket channel.")

@bot.command(name="commands")
async def commands_list(ctx):
    help_message = """
**📌 List of Available Commands:**

🔹 `!announce <message>` → Sends an announcement in the designated channel.
🔹 `!ticket` → Creates a private support ticket.
🔹 `!closeticket` → Closes and deletes a ticket.
🔹 `!ban @user <reason>` → Bans a user from the server.
🔹 `!kick @user <reason>` → Kicks a user from the server.
🔹 `!warn @user <reason>` → Issues a warning to a user (3 warnings = kick).
🔹 `!welcome <user>` → Sends a welcome message in the designated channel.

🛠 **Moderation commands are restricted to administrators/moderators.**
"""

    try:
        await ctx.author.send(help_message)
        await ctx.send("📩 Check your DMs for the list of commands!")
    except discord.Forbidden:
        await ctx.send("⚠️ I couldn't send you a DM. Please enable direct messages.")

bot.run(TOKEN)

async def reconnect_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"Erro detectado: {e}")
            await asyncio.sleep(5)  # espera 5 segundos antes de tentar reconectar

asyncio.run(reconnect_bot())





 
