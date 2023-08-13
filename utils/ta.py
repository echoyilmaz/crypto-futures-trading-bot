import talib

from utils.math import calculate_stop_loss, calculate_take_profits, calculate_risk_to_reward

stop_percent = 0.03
profit_percent = 0.05
num_take_profit_levels = 3

pair_previous_states = {}  # Dictionary to store previous states for each pair

async def load_indicators(prices):
    prices['Alligator_Jaw'], prices['Alligator_Teeth'], prices['Alligator_Lips'] = talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=13), talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=8), talib.WILLR(prices['high'], prices['low'], prices['close'], timeperiod=5)
    return prices

async def perform_technical_analysis(pair, prices, depth):
    if pair not in pair_previous_states:
        pair_previous_states[pair] = "UNKNOWN"

    analyzed_prices = await load_indicators(prices)

    entry_price = analyzed_prices['close'].iloc[-1]

    alligator_jaw = analyzed_prices['Alligator_Jaw'].iloc[-2]
    alligator_teeth = analyzed_prices['Alligator_Teeth'].iloc[-2]
    alligator_lips = analyzed_prices['Alligator_Lips'].iloc[-2]

    previous_alligator_state = pair_previous_states[pair]

    if alligator_jaw > alligator_teeth > alligator_lips:
        current_alligator_state = "UP"
    elif alligator_jaw < alligator_teeth < alligator_lips:
        current_alligator_state = "DOWN"

    if current_alligator_state != previous_alligator_state:  # Only update state if different
        pair_previous_states[pair] = current_alligator_state

    if previous_alligator_state == "UP" and current_alligator_state == "DOWN":
        suggested_direction = "SHORT"
    elif previous_alligator_state == "DOWN" and current_alligator_state == "UP":
        suggested_direction = "LONG"
    else:
        suggested_direction = "WAIT"

    if suggested_direction == "WAIT":
        return {
            "pair": pair,
            "previous_state": previous_alligator_state,
            "direction": suggested_direction,
            "current_price": entry_price
        }

    stop_loss = await calculate_stop_loss(entry_price, stop_percent)
    take_profits = await calculate_take_profits(entry_price, profit_percent, num_take_profit_levels)
    risk_to_reward = await calculate_risk_to_reward(entry_price, stop_loss, take_profits[-1])

    return {
        "pair": pair,
        "previous_state": previous_alligator_state,
        "direction": suggested_direction,
        "current_price": entry_price,
        "stop_loss": round(stop_loss, depth),
        "take_profits": [round(tp, depth) for tp in take_profits],
        "risk_to_reward": round(risk_to_reward, 1)
    }
