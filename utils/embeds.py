async def send_trade_embed(trade_data):
    channel_id = self.bot.config["callout_channel"]
    channel = self.bot.get_channel(channel_id)

    embed = discord.Embed(title="Trade Information", color=0x00ff00)
    embed.set_author(name="Crypto Trading Bot")

    embed.add_field(name="Trader", value=trade_data["trader"], inline=False)
    embed.add_field(name="Pair", value=trade_data["pair"], inline=True)
    embed.add_field(name="Side", value=trade_data["side"], inline=True)
    embed.add_field(name="Leverage", value=trade_data["leverage"], inline=True)

    embed.add_field(name="Entry Price", value=f"${trade_data['entry']:.2f}", inline=True)
    embed.add_field(name="Stop Loss", value=f"${trade_data['stop']:.2f}" if trade_data["stop"] else "N/A", inline=True)
    embed.add_field(name="Status", value=trade_data["status"], inline=True)

    if trade_data["targets"]:
        targets_str = "\n".join([f"${target:.2f}" for target in trade_data["targets"]])
        embed.add_field(name="Targets", value=targets_str, inline=False)
    else:
        embed.add_field(name="Targets", value="None", inline=False)

    embed.add_field(name="Current Target", value=f"${trade_data['current_target']:.2f}", inline=True)
    
    embed.timestamp = trade_data["time"]
    embed.set_footer(text="Trade initiated")

    await channel.send(embed=embed)
