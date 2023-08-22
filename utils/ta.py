import talib

stop_percent = 20  # Percentage value out of 100
profit_percent = 80  # Percentage value out of 100
leverage = 50
num_take_profit_levels = 1

pair_previous_states = {}  # Dictionary to store previous states for each pair

async def calculate_stop_loss(entry_price, stop_percent, leverage, position_direction):
    leverage_multiplier = 1 / leverage
    if position_direction == "LONG":
        stop_loss = entry_price - (entry_price * stop_percent / 100) * leverage_multiplier
    else:
        stop_loss = entry_price + (entry_price * stop_percent / 100) * leverage_multiplier
    return stop_loss

async def calculate_take_profits(entry_price, profit_percent, num_levels, leverage, position_direction):
    leverage_multiplier = 1 / leverage
    take_profits = []
    for level in range(1, num_levels + 1):
        if position_direction == "LONG":
            take_profit = entry_price + (entry_price * (profit_percent * level / 100)) * leverage_multiplier
        else:
            take_profit = entry_price - (entry_price * (profit_percent * level / 100)) * leverage_multiplier
        take_profits.append(take_profit)
    return take_profits

async def load_indicators(prices, oi, long_short_ratio):
    oi['ema5'] = talib.EMA(oi['sumOpenInterest'], timeperiod=5)
    oi['ema8'] = talib.EMA(oi['sumOpenInterest'], timeperiod=8)
    long_short_ratio['long_ema'] = talib.EMA(long_short_ratio['longAccount'], timeperiod=8)
    long_short_ratio['short_ema'] = talib.EMA(long_short_ratio['shortAccount'], timeperiod=8)
    return oi, long_short_ratio

async def perform_technical_analysis(pair, prices, oi, long_short_ratio, depth):
    if pair not in pair_previous_states:
        pair_previous_states[pair] = "UNKNOWN"

    analyzed_oi, analyzed_ls_ratio = await load_indicators(prices, oi, long_short_ratio)

    entry_price = prices['close'].iloc[-1]
    oi_ema5 = analyzed_oi['ema5'].iloc[-1]
    oi_ema8 = analyzed_oi['ema8'].iloc[-1]
    long_ema = analyzed_ls_ratio['long_ema'].iloc[-1]
    short_ema = analyzed_ls_ratio['short_ema'].iloc[-1]

    previous_state = pair_previous_states[pair]

    if oi_ema5 > oi_ema8 and long_ema > short_ema:
        current_state = "UP"
    elif oi_ema5 < oi_ema8 and long_ema < short_ema:
        current_state = "DOWN"
    else:
        current_state = previous_state

    if current_state != previous_state:
        pair_previous_states[pair] = current_state

    if previous_state == "UP" and current_state == "DOWN":
        suggested_direction = "LONG"
    elif previous_state == "DOWN" and current_state == "UP":
        suggested_direction = "SHORT"
    else:
        suggested_direction = "WAIT"

    stop_loss = await calculate_stop_loss(entry_price, stop_percent, leverage, suggested_direction)
    take_profits = await calculate_take_profits(entry_price, profit_percent, num_take_profit_levels, leverage, suggested_direction)

    stop = round(stop_loss, depth)

    if stop == entry_price:
        suggested_direction = "WAIT"

    return {
        "pair": pair,
        "direction": suggested_direction,
        "leverage": leverage,
        "current_price": entry_price,
        "stop_loss": stop,
        "take_profits": [round(tp, depth) for tp in take_profits],
    }