@bot.tree.command(name="genkey", description="Generate License Keys")
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
    
    # Panel ke form ke mutabiq exact payload mapping
    payload = {
        "api_key": API_KEY,
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package.value,
        "days": str(days),
        "count": str(count),
        "note": note
    }
    
    try:
        # Kuch PHP APIs multipart ya standard data form expect karti hain
        resp = requests.post(API_URL, data=payload, headers=HEADERS, timeout=10)
        
        try:
            data = resp.json()
        except Exception:
            await interaction.followup.send(f"❌ API Invalid JSON Response: `{resp.text[:150]}`", ephemeral=True)
            return
        
        if data.get("success"):
            keys = parse_keys(data)
            dur = "Lifetime" if days == 0 else f"{days} Days"
            embed = discord.Embed(title="🔑 FREE KEY BY PERSISTX", color=0x22C55E)
            embed.add_field(name="Package Name", value=f"**{package.name}**", inline=True)
            embed.add_field(name="Duration", value=dur, inline=True)
            embed.add_field(name="Count", value=str(len(keys)), inline=True)
            
            if note:
                embed.add_field(name="Note", value=f"`{note}`", inline=False)
                
            formatted_keys = "\n".join([f"`{k}`" for k in keys[:20]])
            if len(keys) > 20:
                formatted_keys += f"\n... and {len(keys) - 20} more keys"
                
            embed.add_field(name="Keys", value=formatted_keys, inline=False)
            
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
