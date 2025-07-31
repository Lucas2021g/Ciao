import discord
from discord.ext import commands
from discord import app_commands, Intents
import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

intents = Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1400119596396314764  # <-- Sostituisci con l’ID del tuo server Discord

# RUOLI AUTORIZZATI AL PANNELLO
PANNELLO_RUOLI_AUTORIZZATI = ["Owner", "Fondatore"]

# --- Comando !crea_pannello ---
@bot.command()
async def crea_pannello(ctx):
    ruoli_utente = [r.name for r in ctx.author.roles]
    if not any(r in PANNELLO_RUOLI_AUTORIZZATI for r in ruoli_utente):
        return await ctx.send("Non hai il permesso di usare questo comando.")

    view = TicketButtons()
    await ctx.send("🎫 Seleziona il tipo di supporto che desideri:", view=view)


# --- Pulsanti Ticket ---
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Candidatura Staff", style=discord.ButtonStyle.green, custom_id="ticket_candidatura")
    async def candidatura_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "candidatura")

    @discord.ui.button(label="🛠️ Supporto Generico", style=discord.ButtonStyle.blurple, custom_id="ticket_supporto")
    async def supporto_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "supporto")

    async def create_ticket(self, interaction, tipo):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="----------Ticket----------")
        if not category:
            category = await guild.create_category("🎟️ Tickets")

        channel_name = f"ticket-{tipo}-{interaction.user.name}".lower().replace(" ", "-")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }

        staff_role = discord.utils.get(guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await ticket_channel.send(f"{interaction.user.mention} ha aperto un ticket per **{tipo}**.")

        await interaction.response.send_message(f"✅ Ticket creato: {ticket_channel.mention}", ephemeral=True)


# --- Comando !ai (in tutti i canali) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!ai "):
        prompt = message.content[4:]
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Rispondi sempre come se fossi un gatto intelligente e curioso. Fai le fusa, usa espressioni feline, sii tenero e simpatico."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            result = response.json()
            ai_reply = result['choices'][0]['message']['content'].strip()

            if not ai_reply.endswith(":3"):
                ai_reply += " :3"

            await message.channel.send(ai_reply)

        except Exception as e:
            await message.channel.send("⚠️ Miao! Qualcosa è andato storto nel contattare il server IA.")
            print(f"Errore IA: {e}")

    await bot.process_commands(message)


# --- Bot pronto ---
@bot.event
async def on_ready():
    print(f"✅ Bot connesso come {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"Errore sync: {e}")

bot.run(TOKEN)
