import talib

stop_percent = 10  # Percentage value out of 100
profit_percent = 30  # Percentage value out of 100
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

async def load_indicators(prices):
    prices['RSI'] = talib.RSI(prices['close'], timeperiod=14)
    prices['%K'], prices['%D'] = talib.STOCH(prices['high'], prices['low'], prices['close'], fastk_period=14, slowk_period=3, slowd_period=3)
    prices['macd'], prices['signal'], prices['histogram'] = talib.MACD(prices['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    return prices

async def perform_technical_analysis(pair, prices, depth):

    analyzed_prices = await load_indicators(prices)

    entry_price = analyzed_prices['close'].iloc[-1]

    rsi = analyzed_prices['RSI'].iloc[-1]
    stoch_k = analyzed_prices['%K'].iloc[-1]
    stoch_d = analyzed_prices['%D'].iloc[-1]
    macd = analyzed_prices['macd'].iloc[-1]
    macd_signal = analyzed_prices['signal'].iloc[-1]

    if rsi > 70 and stoch_k > stoch_d and macd > macd_signal:
        suggested_direction = "SHORT"
    elif rsi < 30 and stoch_k < stoch_d and macd < macd_signal:
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
