import aiohttp
import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import Context

from utils.api import fetch_pairs, fetch_candles, fetch_open_interest, fetch_long_short_ratio
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

    @commands.hybrid_command(name="winningpairs", description="Show all winning pairs.")
    async def winningpairs(self, ctx: Context) -> None:
        closed_trades = [trade for trade in self.bot.trade_positions if trade["status"] == "CLOSED"]
        
        # Calculate average ROI by pair and win/loss/total trades
        pair_stats = {}
        for trade in closed_trades:
            pair = trade["pair"]
            roi = sum(trade["roi"])
            if pair not in pair_stats:
                pair_stats[pair] = {"total_roi": roi, "num_trades": 1, "num_wins": 1 if roi > 0 else 0, "num_losses": 1 if roi <= 0 else 0}
            else:
                pair_stats[pair]["total_roi"] += roi
                pair_stats[pair]["num_trades"] += 1
                if roi > 0:
                    pair_stats[pair]["num_wins"] += 1
                else:
                    pair_stats[pair]["num_losses"] += 1
        
        # Filter pairs with positive ROI
        positive_roi_pairs = {pair: stats for pair, stats in pair_stats.items() if stats["total_roi"] > 0}
        
        # Calculate average ROI and identify best performing pairs
        best_performing_pairs = []
        winning_pairs = []
        for pair, stats in positive_roi_pairs.items():
            average_roi = stats["total_roi"] / stats["num_trades"]
            best_performing_pairs.append((pair, average_roi, stats["num_wins"], stats["num_losses"], stats["num_trades"]))
            if stats["num_wins"] > stats["num_losses"]:
                winning_pairs.append(pair)
        best_performing_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Split the best performing pairs into multiple embeds if needed
        max_fields_per_embed = 10
        num_embeds = (len(best_performing_pairs) + max_fields_per_embed - 1) // max_fields_per_embed

        for embed_num in range(num_embeds):
            embed = discord.Embed(title="Trade Statistics", color=0x00ff00)
            start_idx = embed_num * max_fields_per_embed
            end_idx = min(start_idx + max_fields_per_embed, len(best_performing_pairs))

            # Add average ROI, win/loss/total for each pair to the embed
            for idx in range(start_idx, end_idx):
                pair, average_roi, num_wins, num_losses, num_trades = best_performing_pairs[idx]
                formatted_average_roi = f"{average_roi:.2f}%"
                win_loss_total = f"{num_wins}W/{num_losses}L/{num_trades}T"
                embed.add_field(name=f"Pair: {pair}", value=f"Average ROI: {formatted_average_roi}\nWin/Loss/Total: {win_loss_total}", inline=False)
            
            # Send the embed
            await ctx.send(embed=embed)
        
        # Print winning pairs as comma-separated list
        if winning_pairs:
            winning_pairs_list = ", ".join(winning_pairs)
            await ctx.send(f"Winning pairs: {winning_pairs_list}")
        else:
            await ctx.send("No winning pairs.")

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
        timeframe = "5m"
        margin = 1

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                for pair in pairs:
                        try:
                            prices = await fetch_candles(session, pair, timeframe, candlestick_limit)
                            oi = await fetch_open_interest(session, pair, timeframe, candlestick_limit)
                            long_short_ratio = await fetch_long_short_ratio(session, pair, timeframe, candlestick_limit)

                            result = await perform_technical_analysis(pair['binance'], prices, oi, long_short_ratio, pair['depth'])

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
