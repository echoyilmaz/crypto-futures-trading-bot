import talib

stop_percent = 5  # Decreased stop percentage for scalping
profit_percent = 5  # Decreased profit percentage for scalping
leverage = 10  # Lower leverage for scalping
num_take_profit_levels = 1  # Fewer take profit levels for scalping

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

async def load_indicators(prices):
    prices['RSI'] = talib.RSI(prices['close'], timeperiod=14)
    prices['SMA'] = talib.SMA(prices['close'], timeperiod=20)
    prices['EMA'] = talib.EMA(prices['close'], timeperiod=20)
    return prices

async def perform_technical_analysis(pair, prices, depth):
    if pair not in pair_previous_states:
        pair_previous_states[pair] = "UNKNOWN"

    analyzed_prices = await load_indicators(prices)

    entry_price = analyzed_prices['close'].iloc[-1]

    rsi = analyzed_prices['RSI'].iloc[-1]
    sma = analyzed_prices['SMA'].iloc[-1]
    ema = analyzed_prices['EMA'].iloc[-1]

    previous_rsi_state = pair_previous_states[pair]

    if rsi > 70:
        current_rsi_state = "OVERBOUGHT"
    elif rsi < 30:
        current_rsi_state = "OVERSOLD"
    else:
        current_rsi_state = previous_rsi_state

    if current_rsi_state != previous_rsi_state:
        pair_previous_states[pair] = current_rsi_state

    if current_rsi_state == "OVERBOUGHT" and entry_price > sma and entry_price > ema:
        suggested_direction = "SHORT"
    elif current_rsi_state == "OVERSOLD" and entry_price < sma and entry_price < ema:
        suggested_direction = "LONG"
    else:
        suggested_direction = "WAIT"

    stop_loss = await calculate_stop_loss(entry_price, stop_percent, leverage, suggested_direction)
    take_profits = await calculate_take_profits(entry_price, profit_percent, num_take_profit_levels, leverage, suggested_direction)

    return {
        "pair": pair,
        "direction": suggested_direction,
        "leverage": leverage,
        "current_price": entry_price,
        "stop_loss": round(stop_loss, depth),
        "take_profits": [round(tp, depth) for tp in take_profits],
    }