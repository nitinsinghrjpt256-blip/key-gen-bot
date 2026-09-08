import os
import threading
import time
import discord
from discord.ext import commands
import requests
from flask import Flask

# ==========================================
# 1. 24/7 KEEP-ALIVE WEB SERVER (Render Free Web Service)
# ==========================================
app = Flask("")


@app.route("/")
def home():
    return "Bot is alive and running 24/7 on Render!"


def run_http_server():
    # Render automatically PORT environment variable deta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def self_ping():
    # Render free service ko active rakhne ke liye self-ping loop
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        try:
            if render_url:
                requests.get(render_url, timeout=10)
                print("Self-ping successful! Bot is kept awake.")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(600)  # Har 10 minute me ping karega


def start_server():
    # Flask server thread
    server_thread = threading.Thread(target=run_http_server)
    server_thread.daemon = True
    server_thread.start()

    # Self ping thread
    ping_thread = threading.Thread(target=self_ping)
    ping_thread.daemon = True
    ping_thread.start()


# Server start karein
start_server()

# ==========================================
# 2. ADVANCED KEY GENERATOR BOT CONFIG
# ==========================================

# Direct Token or Environment Variable
TOKEN = os.getenv(
    "DISCORD_TOKEN",
    "MTU0NjkzMjUzMTIwMTU3NzE1Mg.Gw1LQ3.LKBspE2HBR3Fdpjf0iWvkamH87TthJTItTu7Y8",
)

# Discord Server ID (Numeric)
GUILD_ID = 1525181999147388958

API_URL = "https://auth.terminalx999.online/api_admin.php"
API_KEY = (
    "TX999_1fc0134c4c418cf9f0817f355ac10cf7e5f73cf899a83bbf4731e4eec3929870"
)
APP_ID = "9f087d585fbd666572fc24b7"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as All-Packages Bot: {bot.user.name}")
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands successfully!")
    except Exception as e:
        print(f"Sync error: {e}")


# Action Buttons Listener (HWID Reset, Ban, Unban, Delete)
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        if ":" in custom_id:
            action, key = custom_id.split(":", 1)
            await interaction.response.defer(ephemeral=True)
            try:
                payload = {"api_key": API_KEY, "action": action, "key": key}
                resp = requests.post(API_URL, json=payload, timeout=10)
                res_data = resp.json()

                if res_data.get("success"):
                    await interaction.followup.send(
                        f"✓ Action **{action.upper()}** completed successfully for key:\n`{key}`",
                        ephemeral=True,
                    )
                else:
                    msg = res_data.get("message", "Unknown response")
                    await interaction.followup.send(
                        f"❌ Failed: {msg}", ephemeral=True
                    )
            except Exception as e:
                await interaction.followup.send(
                    f"⚠️ Error executing action: {str(e)}", ephemeral=True
                )


# Slash Command: Generate Keys
@bot.tree.command(
    name="genkey", description="Generate License Keys for Packages"
)
@discord.app_commands.choices(
    package=[
        discord.app_commands.Choice(
            name="BASIC PANEL", value="e52c1515c53453b85d0d4e87"
        ),
        discord.app_commands.Choice(
            name="AIMSILENT EXE", value="affc8da8fd5ace99981ab877"
        ),
        discord.app_commands.Choice(
            name="UID BYPASS", value="cb921031dc43197e8ccb6828"
        ),
        discord.app_commands.Choice(
            name="EXTERNAL PANEL", value="3d1c6c948b4715fbd2fada2d"
        ),
        discord.app_commands.Choice(
            name="PVT AIMKILL", value="d4f0ce93349f236711344cb5"
        ),
        discord.app_commands.Choice(
            name="VAULT PANEL", value="154d1edaddd7203fbfd847f4"
        ),
    ]
)
@discord.app_commands.describe(
    package="Select target package",
    days="Number of validity days (0 = lifetime)",
    count="Number of keys (max 500)",
    note="Optional note (e.g. customer name/batch)",
)
async def genkey(
    interaction: discord.Interaction,
    package: str,
    days: int = 30,
    count: int = 1,
    note: str = "",
):
    await interaction.response.defer(ephemeral=False)

    payload = {
        "api_key": API_KEY,
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package,
        "days": days,
        "count": count,
        "note": note,
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        data = resp.json()

        # Parse keys from response
        keys = []
        if isinstance(data.get("data"), dict):
            keys = data.get("data", {}).get("keys", [])
        elif isinstance(data.get("data"), list):
            keys = data.get("data", [])
        elif "keys" in data:
            keys = data.get("keys", [])

        if data.get("success") and keys:
            dur = "Lifetime" if days == 0 else f"{days} Days"
            embed = discord.Embed(
                title="🔑 License Keys Generated", color=0x22C55E
            )
            embed.add_field(
                name="Package ID", value=f"`{package}`", inline=True
            )
            embed.add_field(name="Duration", value=dur, inline=True)
            embed.add_field(name="Count", value=str(len(keys)), inline=True)

            if note:
                embed.add_field(name="Note", value=f"`{note}`", inline=False)

            formatted_keys = "\n".join([f"`{k}`" for k in keys[:20]])
            if len(keys) > 20:
                formatted_keys += f"\n... and {len(keys) - 20} more keys"

            embed.add_field(name="Keys", value=formatted_keys, inline=False)

            # Action buttons
            view = None
            if len(keys) == 1:
                target_key = keys[0]
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label="Reset HWID",
                        custom_id=f"reset_hwid:{target_key}",
                        style=discord.ButtonStyle.primary,
                    )
                )
                view.add_item(
                    discord.ui.Button(
                        label="Ban",
                        custom_id=f"ban_key:{target_key}",
                        style=discord.ButtonStyle.danger,
                    )
                )
                view.add_item(
                    discord.ui.Button(
                        label="Unban",
                        custom_id=f"unban_key:{target_key}",
                        style=discord.ButtonStyle.success,
                    )
                )
                view.add_item(
                    discord.ui.Button(
                        label="Delete",
                        custom_id=f"delete_key:{target_key}",
                        style=discord.ButtonStyle.secondary,
                    )
                )

            if view:
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
        else:
            err_msg = data.get(
                "message", "No keys returned from API response."
            )
            await interaction.followup.send(
                f"❌ Generation Failed: `{err_msg}`", ephemeral=True
            )

    except Exception as e:
        await interaction.followup.send(
            f"⚠️ API Communication Error: {str(e)}", ephemeral=True
        )


bot.run(TOKEN)
