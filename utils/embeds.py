import discord

async def send_position_open_embed(trade_data, self, reason):
    channel_id = self.bot.config['callout_channel']
    channel = self.bot.get_channel(channel_id)

    embed = discord.Embed(title=reason, color=0x3498db)

    embed.add_field(name="Pair", value=trade_data["pair"][:-4], inline=True)
    embed.add_field(name="Position", value=trade_data["side"], inline=True)
    embed.add_field(name="Leverage", value=f"{trade_data['leverage']}x", inline=True)

    embed.add_field(name="Entry", value=f"${trade_data['entry']}", inline=True)
    embed.add_field(name="Stop", value=f"${trade_data['stop']}" if trade_data["stop"] else "N/A", inline=True)

    if trade_data["targets"]:
        targets_str = "\n".join([f"{index + 1}: ${target}" for index, target in enumerate(trade_data["targets"])])
        embed.add_field(name="Targets", value=targets_str, inline=False)
    else:
        embed.add_field(name="Targets", value="None", inline=False)

    current_target_index = trade_data["current_target"]
    if current_target_index < len(trade_data["targets"]):
        current_target_price = trade_data["targets"][current_target_index]
        embed.add_field(name="Current", value=f"{current_target_index + 1}: ${current_target_price}", inline=True)
    else:
        embed.add_field(name="Current", value="No targets remaining", inline=True)

    embed.timestamp = trade_data["time"]
    embed.set_footer(text=reason)

    await channel.send(embed=embed)

async def send_position_close_embed(trade_data, current_price, self, reason):
    channel_id = self.bot.config['callout_channel']
    channel = self.bot.get_channel(channel_id)

    entry_price = trade_data['entry']
    exit_price = current_price  # Replace with the actual exit price

    roi = sum(trade_data['roi']) / len(trade_data['roi'])

    roi_color = 0x00ff00 if roi >= 0 else 0xff0000  # Green for positive ROI, red for negative ROI

    embed = discord.Embed(title=reason, color=roi_color)  # Change color based on ROI

    embed.add_field(name="Pair", value=trade_data["pair"][:-4], inline=True)
    embed.add_field(name="Position", value=trade_data["side"], inline=True)
    embed.add_field(name="Leverage", value=f"{trade_data['leverage']}x", inline=True)

    embed.add_field(name="Entry", value=f"${entry_price}", inline=True)
    embed.add_field(name="Stop", value=f"${trade_data['stop']}" if trade_data["stop"] else "N/A", inline=True)
    embed.add_field(name="Exit", value=f"${exit_price}", inline=True)
    if trade_data["targets"]:
        targets_str = "\n".join([f"{index + 1}: ${target}" for index, target in enumerate(trade_data["targets"])])
        embed.add_field(name="Targets", value=targets_str, inline=False)
    else:
        embed.add_field(name="Targets", value="None", inline=False)

    current_target_index = trade_data["current_target"]
    if current_target_index < len(trade_data["targets"]):
        current_target_price = trade_data["targets"][current_target_index]
        embed.add_field(name="Current", value=f"{current_target_index + 1}: ${current_target_price}", inline=True)
    else:
        embed.add_field(name="Current", value="No targets remaining", inline=True)
    embed.add_field(name="Avg. ROI", value=f"{roi:.2f}%", inline=True)  # Calculate ROI without rounding

    embed.timestamp = trade_data["time"]
    embed.set_footer(text=reason)

    await channel.send(embed=embed)

    # Append ROI to the trade_positions dictionary based on pair, side, and entry