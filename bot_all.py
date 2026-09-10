import os
import random
import string
import threading
import time
import discord
from discord.ext import commands
import requests
from flask import Flask

# ==========================================
# 1. 24/7 KEEP-ALIVE WEB SERVER
# ==========================================
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive and running 24/7 on Render!"

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def self_ping():
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        try:
            if render_url:
                requests.get(render_url, timeout=10)
                print("Self-ping successful! Bot is kept awake.")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(600)

def start_server():
    server_thread = threading.Thread(target=run_http_server)
    server_thread.daemon = True
    server_thread.start()

    ping_thread = threading.Thread(target=self_ping)
    ping_thread.daemon = True
    ping_thread.start()

start_server()

# ==========================================
# 2. BOT CONFIGURATION & CREDENTIALS
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1525181999147388958
OWNER_ID = 1525179499602509977

LOG_CHANNEL_ID = 1547688035796254941  # Logs channel ID

API_URL = "https://auth.terminalx999.online/api_admin.php"
API_KEY = "TX999_1fc0134c4c418cf9f0817f355ac10cf7e5f73cf899a83bbf4731e4eec3929870"
APP_ID = "9f087d585fbd666572fc24b7"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

def get_key_action_view(key: str):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Reset HWID", custom_id=f"reset_hwid:{key}", style=discord.ButtonStyle.primary))
    view.add_item(discord.ui.Button(label="Ban", custom_id=f"ban_key:{key}", style=discord.ButtonStyle.danger))
    view.add_item(discord.ui.Button(label="Unban", custom_id=f"unban_key:{key}", style=discord.ButtonStyle.success))
    view.add_item(discord.ui.Button(label="Delete", custom_id=f"delete_key:{key}", style=discord.ButtonStyle.secondary))
    return view

# ==========================================
# 3. EVENTS & INTERACTIONS
# ==========================================
@bot.event
async def on_ready():
    print(f"Logged in as Key Manager Bot: {bot.user.name}")
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands successfully!")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Contact super admin PERSISTX", ephemeral=True)
            return

        custom_id = interaction.data.get("custom_id", "")
        if ":" in custom_id:
            action, key = custom_id.split(":", 1)
            await interaction.response.defer(ephemeral=True)
            try:
                payload = {
                    "api_key": API_KEY,
                    "action": action,
                    "key": key,
                    "app_id": APP_ID
                }
                resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
                res_data = resp.json()
                
                if res_data.get("success"):
                    await interaction.followup.send(f"✓ Action **{action.upper()}** completed successfully for key:\n`{key}`", ephemeral=True)
                else:
                    msg = res_data.get("message", "Unknown response")
                    await interaction.followup.send(f"❌ Failed: {msg}", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Error executing action: {str(e)}", ephemeral=True)

# ==========================================
# 4. BOT COMMANDS
# ==========================================

@bot.tree.command(name="genkey", description="Generate License Keys in a Professional Table Format")
@discord.app_commands.choices(package=[
    discord.app_commands.Choice(name="BASIC PANEL", value="e52c1515c53453b85d0d4e87"),
    discord.app_commands.Choice(name="AIMSILENT EXE", value="affc8da8fd5ace99981ab877"),
    discord.app_commands.Choice(name="UID BYPASS", value="cb921031dc43197e8ccb6828"),
    discord.app_commands.Choice(name="EXTERNAL PANEL", value="3d1c6c948b4715fbd2fada2d"),
    discord.app_commands.Choice(name="PVT AIMKILL", value="d4f0ce93349f236711344cb5"),
    discord.app_commands.Choice(name="VAULT PANEL", value="154d1edaddd7203fbfd847f4")
])
@discord.app_commands.describe(
    package="Select target package",
    days="Number of validity days (0 = lifetime)",
    count="Number of keys (max 500)",
    note="Optional note (e.g. customer name/batch)"
)
async def genkey(
    interaction: discord.Interaction,
    package: discord.app_commands.Choice[str],
    days: int = 30,
    count: int = 1,
    note: str = ""
):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Contact super admin PERSISTX", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)
    
    payload = {
        "api_key": API_KEY,
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package.value,
        "days": days,
        "count": count,
        "note": note
    }
    
    try:
        resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if data.get("success"):
            keys = parse_keys(data)
            dur_text = "Lifetime" if days == 0 else f"{days} Days"
            note_str = note if note else "N/A"
            
            # Smart Log Channel Appending (Ek hi table me nayi keys aage add hongi)
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                new_rows = [f"| {k:<20} | {package.name[:13]:<13} | {dur_text:<10} | {note_str[:11]:<11} |" for k in keys]
                
                last_msg = None
                async for msg in log_channel.history(limit=5):
                    if msg.author == bot.user and "```markdown" in msg.content and "LICENSE KEY" in msg.content:
                        last_msg = msg
                        break
                
                if last_msg:
                    content = last_msg.content.rstrip("` \n")
                    for r in new_rows:
                        content += "\n" + r
                    content += "\n```"
                    if len(content) < 1950:
                        await last_msg.edit(content=content)
                    else:
                        log_lines = ["```markdown", "| LICENSE KEY          | PACKAGE       | DURATION   | NOTE        |", "|----------------------|---------------|------------|-------------|"]
                        log_lines.extend(new_rows)
                        log_lines.append("```")
                        await log_channel.send("\n".join(log_lines))
                else:
                    log_lines = ["```markdown", "| LICENSE KEY          | PACKAGE       | DURATION   | NOTE        |", "|----------------------|---------------|------------|-------------|"]
                    log_lines.extend(new_rows)
                    log_lines.append("```")
                    await log_channel.send("\n".join(log_lines))

            # User interface ke liye Clean Embed Table
            embed = discord.Embed(title="📊 License Key Generation Dashboard", color=0x5865F2)
            embed.description = "Aapki nayi keys successfully generate kar di gayi hain:"
            
            ui_lines = ["```markdown", "| NO | LICENSE KEY          | DURATION   | NOTE        |", "|----|----------------------|------------|-------------|"]
            for idx, k in enumerate(keys[:15], 1):
                ui_lines.append(f"| {idx:<2} | {k:<20} | {dur_text:<10} | {note_str[:11]:<11} |")
            ui_lines.append("```")
            
            embed.add_field(name=f"📦 Package: {package.name}", value="\n".join(ui_lines), inline=False)
            
            if len(keys) > 15:
                embed.set_footer(text=f"Showing 15 of {len(keys)} keys. Baaki keys logs channel ki master table me update kar di gayi hain.")
            else:
                embed.set_footer(text=f"Total Keys Generated: {len(keys)}")

            view = get_key_action_view(keys[0]) if len(keys) == 1 else None
            
            if view:
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
        else:
            err_msg = data.get("message", "No keys returned from API response.")
            await interaction.followup.send(f"❌ Generation Failed: `{err_msg}`", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"⚠️ API Communication Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="managekey", description="Manage any key (HWID Reset, Ban, Unban, Delete)")
@discord.app_commands.describe(key="Enter the key you want to manage")
async def managekey(interaction: discord.Interaction, key: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Contact super admin PERSISTX", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚙️ Key Control Panel",
        description=f"Select an action for key:\n`{key}`",
        color=0x3B82F6
    )
    view = get_key_action_view(key.strip())
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="keyinfo", description="Get full details & status of any specific key")
@discord.app_commands.describe(key="Enter the license key to check")
async def keyinfo(interaction: discord.Interaction, key: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Contact super admin PERSISTX", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    payload = {
        "api_key": API_KEY,
        "action": "key_info",
        "app_id": APP_ID,
        "key": key.strip()
    }
    
    try:
        resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if data.get("success"):
            info = data.get("data", {}) or data
            
            embed = discord.Embed(
                title="🔍 Key Information Details",
                color=0x3B82F6
            )
            embed.add_field(name="Key", value=f"`{key.strip()}`", inline=False)
            
            status = "🔴 Banned" if info.get("banned") else ("🟢 Active" if info.get("status") == "active" or info.get("used") else "🟡 Unused")
            embed.add_field(name="Status", value=status, inline=True)
            
            duration = info.get("duration") or info.get("days") or "N/A"
            embed.add_field(name="Duration", value=f"{duration} Days", inline=True)
            
            hwid = info.get("hwid") or "Not Registered"
            embed.add_field(name="HWID", value=f"`{hwid}`", inline=False)
            
            if info.get("created_at"):
                embed.add_field(name="Created At", value=str(info.get("created_at")), inline=True)
                
            view = get_key_action_view(key.strip())
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            msg = data.get("message", "Key not found or invalid.")
            await interaction.followup.send(f"❌ Error: `{msg}`", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"⚠️ API Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="resethwid", description="Reset HWID lock for any existing key")
@discord.app_commands.describe(key="Enter the key to reset its HWID")
async def resethwid(interaction: discord.Interaction, key: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Contact super admin PERSISTX", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    payload = {
        "api_key": API_KEY,
        "action": "reset_hwid",
        "app_id": APP_ID,
        "key": key.strip()
    }
    
    try:
        resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if data.get("success"):
            await interaction.followup.send(f"✓ HWID successfully reset for key:\n`{key.strip()}`", ephemeral=True)
        else:
            msg = data.get("message", "Failed to reset HWID.")
            await interaction.followup.send(f"❌ Failed: `{msg}`", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"⚠️ API Error: {str(e)}", ephemeral=True)

bot.run(TOKEN)
