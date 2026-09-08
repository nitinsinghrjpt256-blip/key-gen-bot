import os
import random
import string
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask
import requests

# ==========================================
# 1. Render Web Service Keep-Alive Server
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. Bot Configuration & Credentials
# ==========================================
TOKEN    = os.environ.get("DISCORD_TOKEN", "MTU0NjkzMjUzMTIwMTU3NzE1Mg.GfT2IN.jAKhuT41LbtqcT9bD6t-tw9ddp0O2dN6XTZzyg")
GUILD_ID = 1525181999147388958

API_URL  = "https://auth.terminalx999.online/api_admin.php"
API_KEY  = os.environ.get("API_KEY", "TX999_1fc0134c4c418cf9f0817f355ac10cf7e5f73cf899a83bbf4731e4eec3929870")
APP_ID   = "9f087d585fbd666572fc24b7"

# Custom Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function to generate default key name
def generate_random_username():
    rand_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"VIP-USER-{rand_id}"

# Helper function to parse keys
def parse_keys(data):
    keys = []
    raw = data.get("data")
    if isinstance(raw, list):
        keys = [str(i.get("key", i)) if isinstance(i, dict) else str(i) for i in raw]
    elif isinstance(raw, dict):
        k_list = raw.get("keys") or raw.get("key") or raw.get("key_list") or []
        keys = [str(k) for k in k_list] if isinstance(k_list, list) else ([str(k_list)] if k_list else [])
    elif isinstance(raw, str):
        keys = [raw]

    if not keys:
        top = data.get("key") or data.get("keys")
        if isinstance(top, list):
            keys = [str(k) for k in top]
        elif isinstance(top, str):
            keys = [top]
    return keys

# ==========================================
# 3. Events & Component Interaction
# ==========================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        if ":" in custom_id:
            action, key = custom_id.split(":", 1)
            if action == "delete_key":
                action = "delete_lib_key"
            await interaction.response.defer(ephemeral=True)
            try:
                payload = {
                    "api_key": API_KEY, 
                    "action": action, 
                    "key": key,
                    "app_id": APP_ID
                }
                resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
                
                try:
                    res_data = resp.json()
                except Exception:
                    await interaction.followup.send(f"❌ API Invalid Response (Status Code: {resp.status_code})", ephemeral=True)
                    return

                if res_data.get("success"):
                    await interaction.followup.send(f"✓ Action **{action}** completed for key: `{key}`", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {res_data.get('message', 'Unknown error')}", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Error: {str(e)}", ephemeral=True)

# ==========================================
# 4. Command: /genbypass
# ==========================================
@bot.tree.command(name="genbypass", description="Generate Lib Bypass / Emulator Bypass License Keys")
@discord.app_commands.describe(
    username="Key Name / Username (e.g. Oggy-VIP-99)",
    days="Validity days (default: 30)",
    count="Number of keys (default: 1)",
    note="Custom Note for panel"
)
async def genbypass(
    interaction: discord.Interaction, 
    username: str = None,
    days: int = 30, 
    count: int = 1, 
    note: str = "Lib Bypass Client [Discord Bot]"
):
    await interaction.response.defer(ephemeral=False)
    
    final_username = username if username else generate_random_username()

    payload = {
        "api_key": API_KEY,
        "action": "generate_lib_key",
        "app_id": APP_ID,
        "username": final_username,
        "key_name": final_username,
        "days": days,
        "count": count,
        "note": note,
        "hwid_lock": 1
    }
    
    try:
        resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
        
        try:
            data = resp.json()
        except Exception:
            raw_text = resp.text[:200] if resp.text else "Empty Response"
            await interaction.followup.send(
                f"❌ API Server Error (Status {resp.status_code}): `{raw_text}`",
                ephemeral=True
            )
            return

        if data.get("success"):
            keys = parse_keys(data)
            if not keys:
                await interaction.followup.send(f"⚠️ Key generate hui par response parse nahi hua: `{str(data)}`", ephemeral=True)
                return

            dur = "Lifetime" if days == 0 else f"{days} Days"
            embed = discord.Embed(
                title="⚡ Lib Bypass Key Generated", 
                description=f"**User/Key Name:** {final_username}\n**Duration:** {dur}\n**Note:** {note}", 
                color=0xEAB308
            )
            embed.add_field(name="Keys", value="\n".join([f"`{k}`" for k in keys]), inline=False)
            
            if len(keys) == 1:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Delete", custom_id=f"delete_key:{keys[0]}", style=discord.ButtonStyle.danger))
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ API Error: {data.get('message', 'Failed to generate bypass key')}", ephemeral=True)
            
    except requests.exceptions.Timeout:
        await interaction.followup.send("⚠️ Timeout Error: Panel API server ne response dene me zyaada time liya.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ System Error: {str(e)}", ephemeral=True)

# ==========================================
# 5. Start Keep-Alive & Run Bot
# ==========================================
keep_alive()
bot.run(TOKEN)
