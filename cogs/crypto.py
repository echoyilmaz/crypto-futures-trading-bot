from discord.ext import commands

import aiohttp

from utils.api import fetch_pairs, fetch_candles

import asyncio

class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot):
        self.bot = bot
        self.position_manager_loop = self.bot.loop.create_task(self.position_manager())

    async def position_manager(self):

        candlestick_limit = "400"
        timeframe = "1m"

        async with aiohttp.ClientSession() as session:
            pairs = await fetch_pairs(session)
            while True:
                for pair in pairs:
                    result = await fetch_candles(session, pair, timeframe, candlestick_limit)
                    print(result)
                    await asyncio.sleep(0.2)

def setup(bot):
    bot.add_cog(Crypto(bot))
