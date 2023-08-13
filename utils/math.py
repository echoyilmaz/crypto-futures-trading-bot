async def calculate_stop_loss(entry_price, stop_percent):
    stop_loss = entry_price - (entry_price * stop_percent)
    return stop_loss

async def calculate_take_profits(entry_price, profit_percent, num_levels):
    take_profits = []
    for level in range(1, num_levels + 1):
        take_profit = entry_price + (entry_price * (profit_percent * level))
        take_profits.append(take_profit)
    return take_profits

async def calculate_risk_to_reward(entry_price, stop_loss, take_profit):
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    risk_to_reward = risk / reward
    return risk_to_reward