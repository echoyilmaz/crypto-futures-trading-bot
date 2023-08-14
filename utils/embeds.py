import discord

async def send_trade_embed(trade_data, self):
    channel_id = self.bot.config['callout_channel']
    channel = self.bot.get_channel(channel_id)

    embed = discord.Embed(title="Trade Information", color=0x3498db)
    embed.set_author(name="Crypto Trade Tracker 1m Scalping Algo")

    embed.add_field(name="Pair", value=trade_data["pair"], inline=True)
    embed.add_field(name="Position", value=trade_data["side"], inline=True)
    embed.add_field(name="Leverage", value=f"{trade_data['leverage']}x", inline=True)

    embed.add_field(name="Entry Price", value=f"${trade_data['entry']}", inline=True)
    embed.add_field(name="Stop Loss", value=f"${trade_data['stop']}" if trade_data["stop"] else "N/A", inline=True)
    embed.add_field(name="Status", value=trade_data["status"], inline=True)

    if trade_data["targets"]:
        targets_str = "\n".join([f"{index + 1}: ${target}" for index, target in enumerate(trade_data["targets"])])
        embed.add_field(name="Targets", value=targets_str, inline=False)
    else:
        embed.add_field(name="Targets", value="None", inline=False)

    current_target_index = trade_data["current_target"]
    if current_target_index < len(trade_data["targets"]):
        current_target_price = trade_data["targets"][current_target_index]
        embed.add_field(name="Current Target", value=f"{current_target_index + 1}: ${current_target_price}", inline=True)
    else:
        embed.add_field(name="Current Target", value="No targets remaining", inline=True)

    embed.timestamp = trade_data["time"]
    embed.set_footer(text="Trade initiated")

    await channel.send(embed=embed)

async def send_position_close_embed(trade_data, new_trade, self, reason):
    channel_id = self.bot.config['callout_channel']
    channel = self.bot.get_channel(channel_id)

    entry_price = trade_data['entry']
    exit_price = new_trade['entry']  # Replace with the actual exit price

    if trade_data["side"] == "LONG":
        roi = ((exit_price - entry_price) / entry_price) * 100 * (1 / trade_data['leverage'])
    elif trade_data["side"] == "SHORT":
        roi = ((entry_price - exit_price) / entry_price) * 100 * (1 / trade_data['leverage'])

    roi_color = 0x00ff00 if roi >= 0 else 0xff0000  # Green for positive ROI, red for negative ROI

    embed = discord.Embed(title="Position Closed", color=roi_color)  # Change color based on ROI
    embed.set_author(name="Crypto Trade Tracker 1m Scalping Algo")

    embed.add_field(name="Pair", value=trade_data["pair"], inline=True)
    embed.add_field(name="Position", value=trade_data["side"], inline=True)
    embed.add_field(name="Leverage", value=f"{trade_data['leverage']}x", inline=True)
    embed.add_field(name="Reason", value=reason, inline=True)

    embed.add_field(name="Entry Price", value=f"${entry_price}", inline=True)
    embed.add_field(name="Exit Price", value=f"${exit_price}", inline=True)
    embed.add_field(name="ROI", value=f"{roi:.2f}%", inline=True)  # Calculate ROI without rounding

    embed.timestamp = trade_data["time"]
    embed.set_footer(text="Position closed")

    await channel.send(embed=embed)

