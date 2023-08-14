import aiohttp
import asyncio
import pickle
from datetime import datetime

from discord.ext import commands

from utils.api import fetch_pairs, fetch_candles
from utils.embeds import send_trade_embed
from utils.math import check_trade_status

class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot):
        self.bot = bot
        self.position_manager_loop = self.bot.loop.create_task(self.position_manager())

    async def position_manager(self):

        candlestick_limit = "100"
        timeframe = "1m"

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                for pair in pairs:
                    result = await fetch_candles(session, pair, timeframe, candlestick_limit)

                    if result is not None:
                        trade = {
                            "trader": "Printer",
                            "time": datetime.now(),
                            "pair": result['pair'],
                            "side": result['direction'],
                            "leverage": result['leverage'],
                            "entry": result['current_price'],
                            "targets": result.get('take_profits', []),
                            "stop": result.get('stop_loss', None),
                            "status": "PASS",
                            "current_target": 0,
                            "roi": []
                        }

                        await check_trade_status(self, trade)

                        if result['direction'] in ['LONG', 'SHORT']:
                            trade['status'] = "OPEN"
                            self.bot.trade_positions.append(trade)
                            await send_trade_embed(trade, self)
                            print(trade)
                            with open('trade_positions.pickle', 'wb') as f:
                                pickle.dump(self.bot.trade_positions, f)

                    await asyncio.sleep(0.15)

def setup(bot):
    bot.add_cog(Crypto(bot))
