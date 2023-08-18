import aiohttp
import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Context

from utils.api import fetch_pairs, fetch_candles
from utils.process import process_trade_data, handle_open_trade
from utils.ta import perform_technical_analysis

class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot):
        self.bot = bot
        self.position_manager_loop = self.bot.loop.create_task(self.position_manager())
        self.open_trade_manager_loop = self.bot.loop.create_task(self.open_trade_manager())
        self.console_manager_loop = self.bot.loop.create_task(self.console_manager())

    async def console_manager(self):
        while True:
            closed_trades = [trade for trade in self.bot.trade_positions if trade["status"] == "CLOSED"]
            open_trades = [trade for trade in self.bot.trade_positions if trade["status"] == "OPEN"]
            
            num_wins = sum(1 for trade in closed_trades if sum(trade['roi']) > 0)
            num_losses = sum(1 for trade in closed_trades if sum(trade['roi']) <= 0)
            num_trades = len(closed_trades)
            num_open_trades = len(open_trades)

            total_roi = sum(sum(trade['roi']) for trade in closed_trades)
            average_roi = total_roi / num_trades if num_trades > 0 else 0.0

            wins_losses_open_trades = f"{num_wins}W/{num_losses}L/{num_trades}T/{num_open_trades}O"
            formatted_average_roi = f"{average_roi:.2f}% ROI avg." if average_roi >= 0 else "-{:.2f}% ROI avg.".format(abs(average_roi))

            total_realized_pnl = sum(trade["realizedpnl"] for trade in closed_trades)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Print the trade statistics with \r for updating on the same line
            print(f"{current_time} - Wins/Losses/Total/Open Trades: {wins_losses_open_trades} | Average ROI: {formatted_average_roi} | Total Realized PNL: ${total_realized_pnl:.2f}", end='\r')
            await asyncio.sleep(1)
    

    @commands.hybrid_command(name="stats", description="Show total stats.")
    async def stats(self, ctx: Context) -> None:
        closed_trades = [trade for trade in self.bot.trade_positions if trade["status"] == "CLOSED"]
        
        num_wins = sum(1 for trade in closed_trades if sum(trade['roi']) > 0)
        num_losses = sum(1 for trade in closed_trades if sum(trade['roi']) <= 0)
        num_trades = len(closed_trades)

        total_roi = sum(sum(trade['roi']) for trade in closed_trades)
        average_roi = total_roi / num_trades if num_trades > 0 else 0.0

        wins_losses_trades = f"{num_wins}W/{num_losses}L/{num_trades}T"
        formatted_average_roi = f"{average_roi:.2f}% ROI avg." if average_roi >= 0 else "-{:.2f}% ROI avg.".format(abs(average_roi))

        # Create an embed
        embed = discord.Embed(title="Trade Statistics", color=0x00ff00)
        embed.add_field(name="Wins/Losses/Total Trades", value=wins_losses_trades, inline=False)
        embed.add_field(name="Average ROI", value=formatted_average_roi, inline=False)

        # Additional stats
        total_realized_pnl = sum(trade["realizedpnl"] for trade in closed_trades)
        embed.add_field(name="Total Realized PNL", value=f"${total_realized_pnl:.2f}", inline=False)

        # Send the embed
        await ctx.send(embed=embed)

    async def open_trade_manager(self):

        candlestick_limit = "1"
        timeframe = "1m"

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                if self.bot.trade_positions:
                    for trade in self.bot.trade_positions:
                        if trade["status"] == "OPEN":
                            for pair in pairs:
                                if pair['binance'] == trade['pair']:
                                    try:
                                        prices = await fetch_candles(session, pair, timeframe, candlestick_limit)

                                        current_price = prices['close'].iloc[-1]

                                        await handle_open_trade(current_price, trade, self)

                                        await asyncio.sleep(0.15)

                                    except Exception as e:
                                        import traceback
                                        traceback.print_exc()

                await asyncio.sleep(0.15)  # Sleep before the next iteration


    async def position_manager(self):

        candlestick_limit = "100"
        timeframe = "1m"
        margin = 1

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                for pair in pairs:
                        try:
                            prices = await fetch_candles(session, pair, timeframe, candlestick_limit)

                            result = await perform_technical_analysis(pair['binance'], prices, pair['depth'])

                            if result is not None:
                                trade = {
                                    "time": datetime.now(),
                                    "pair": result['pair'],
                                    "side": result['direction'],
                                    "leverage": result['leverage'],
                                    "entry": result['current_price'],
                                    "targets": result.get('take_profits', []),
                                    "stop": result.get('stop_loss', None),
                                    "status": "",
                                    "current_target": 0,
                                    "roi": [],
                                    "margin": margin,
                                    "realizedpnl": 0
                                }

                                await process_trade_data(self, trade)

                            await asyncio.sleep(0.15)

                        except Exception as e:

                            import traceback
                            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Crypto(bot))
