import pandas as pd

from utils.ta import perform_technical_analysis

import asyncio

async def fetch_pairs(session):
    async with session.get("https://api-swap-rest.bingbon.pro/api/v1/market/getAllContracts") as request:
        if request.status == 200:
            data = await request.json(content_type=None)
            pairs = []
            for contract in data['data']['contracts']:
                pair = str(contract['symbol'])
                if 'USDT' in pair and contract['maxLongLeverage'] >= 1 and contract['maxShortLeverage'] >= 1:
                    pair_entry = {'bingx': pair, 'binance': None, 'depth': None}
                    pair = ''.join(filter(lambda x: x not in '-', str(pair)))
                    pair_entry.update({'binance': pair})
                    # symbol_list = ["BTCUSDT"]
                    # if pair_entry['binance'] not in symbol_list:
                    #     continue
                    print(pair_entry['binance'])
                    async with session.get("https://fapi.binance.com/fapi/v1/exchangeInfo") as depth_request:
                        if depth_request.status == 200:
                            depth_data = await depth_request.json()
                            for pair in depth_data['symbols']:
                                if pair_entry['binance'] == pair['symbol']:
                                    precision = pair['filters'][0]['tickSize']
                                    stepsize = precision.rstrip('0')
                                    if '1' == stepsize:
                                        depth = 0
                                    else:
                                        depth = len(str(stepsize).split(".")[1])
                                    pair_entry['depth'] = depth
                                    pairs.append(pair_entry)
                                    break
            
            return pairs
            
        elif request.status == 429:
            print("API limit broken")
            await asyncio.sleep(60)
        elif request.status == 419:
            print("IP banned from API endpoint")

async def fetch_candles(session, pair, interval, long_tf):
    params = {"symbol": pair['binance'], "interval": interval, "limit": long_tf}
    async with session.get("https://fapi.binance.com/fapi/v1/klines", params=params, timeout=5) as request:
        if request.status == 200:
            data = await request.json(content_type=None)
            candles_data = [[entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6]] for entry in data]
            
            if candles_data:
                columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time']
                prices = pd.DataFrame(candles_data, columns=columns)
                
                if len(prices.index) != 0:
                    prices = prices.astype(float)
                    prices.rename(columns={0: 'open_time', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume', 6: 'close_time'}, inplace=True)

                    return prices
                
        elif request.status == 429:
            print("API limit broken")
            await asyncio.sleep(60)
        elif request.status == 419:
            print("IP banned from API endpoint")
        else:
            print(f"Some other response code for {pair['binance']}?")

async def fetch_open_interest(session, pair, interval, long_tf):
    params = {"symbol": pair['binance'], "period": interval, "limit": long_tf}
    
    async with session.get("https://fapi.binance.com/futures/data/openInterestHist", params=params, timeout=5) as request:
        if request.status == 200:
            data = await request.json(content_type=None)
            
            open_interest_data = [
                {
                    'symbol': entry['symbol'],
                    'sumOpenInterest': float(entry['sumOpenInterest']),
                    'sumOpenInterestValue': float(entry['sumOpenInterestValue']),
                    'timestamp': pd.Timestamp(entry['timestamp'], unit='ms')
                }
                for entry in data
            ]
            
            if open_interest_data:
                open_interest = pd.DataFrame(open_interest_data)
                return open_interest
                
        elif request.status == 429:
            print("API limit broken")
            await asyncio.sleep(60)
        elif request.status == 419:
            print("IP banned from API endpoint")
        else:
            print(f"Some other response code for {pair['binance']}?")

async def fetch_long_short_ratio(session, pair, interval, long_tf):
    params = {"symbol": pair['binance'], "period": interval, "limit": long_tf}
    
    async with session.get("https://fapi.binance.com/futures/data/globalLongShortAccountRatio", params=params, timeout=5) as request:
        if request.status == 200:
            data = await request.json(content_type=None)
            
            long_short_data = [
                {
                    'symbol': entry['symbol'],
                    'longShortRatio': float(entry['longShortRatio']),
                    'longAccount': float(entry['longAccount']),
                    'shortAccount': float(entry['shortAccount']),
                    'timestamp': pd.Timestamp(entry['timestamp'], unit='ms')
                }
                for entry in data
            ]
            
            if long_short_data:
                long_short_ratio = pd.DataFrame(long_short_data)
                return long_short_ratio
                
        elif request.status == 429:
            print("API limit broken")
            await asyncio.sleep(60)
        elif request.status == 419:
            print("IP banned from API endpoint")
        else:
            print(f"Some other response code for {pair['binance']}?")