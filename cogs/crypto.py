import aiohttp
import asyncio
from datetime import datetime

from discord.ext import commands

from utils.api import fetch_pairs, fetch_candles
from utils.process import process_trade_data

class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot):
        self.bot = bot
        self.position_manager_loop = self.bot.loop.create_task(self.position_manager())

    async def position_manager(self):

        candlestick_limit = "100"
        timeframe = "5m"

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                for pair in pairs:
                    result = await fetch_candles(session, pair, timeframe, candlestick_limit)

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
                            "roi": []
                        }

                        try:
                            await process_trade_data(self, trade)
                        except Exception as e:
                            import traceback
                            traceback.print_exc()

                    await asyncio.sleep(0.15)

def setup(bot):
    bot.add_cog(Crypto(bot))
