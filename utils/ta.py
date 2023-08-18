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
    prices['Alligator_Jaw'], prices['Alligator_Teeth'], prices['Alligator_Lips'] = talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=13), talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=8), talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=5)
    prices['RSI'] = talib.RSI(prices['close'], timeperiod=14)  # Calculate RSI with a period of 14
    return prices

async def perform_technical_analysis(pair, prices, depth):
    if pair not in pair_previous_states:
        pair_previous_states[pair] = "UNKNOWN"

    analyzed_prices = await load_indicators(prices)

    entry_price = analyzed_prices['close'].iloc[-1]

    alligator_jaw = analyzed_prices['Alligator_Jaw'].iloc[-1]
    alligator_teeth = analyzed_prices['Alligator_Teeth'].iloc[-1]
    alligator_lips = analyzed_prices['Alligator_Lips'].iloc[-1]
    rsi_value = analyzed_prices['RSI'].iloc[-1]

    previous_alligator_state = pair_previous_states[pair]

    if alligator_jaw > alligator_teeth > alligator_lips:
        current_alligator_state = "UP"
    elif alligator_jaw < alligator_teeth < alligator_lips:
        current_alligator_state = "DOWN"
    else:
        current_alligator_state = previous_alligator_state

    if current_alligator_state != previous_alligator_state:
        pair_previous_states[pair] = current_alligator_state

    if previous_alligator_state == "UP" and current_alligator_state == "DOWN":
        suggested_direction = "SHORT"
    elif previous_alligator_state == "DOWN" and current_alligator_state == "UP":
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
