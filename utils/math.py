from utils.embeds import send_position_close_embed

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

async def calculate_risk_to_reward(entry_price, stop_loss, take_profit):
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    risk_to_reward = risk / reward
    return risk_to_reward

async def check_trade_status(self, new_trade):
        for trade in self.bot.trade_positions:
            if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"]:
                current_price = new_trade['entry']  # Use the entry price as the current price from the fetched result

                if trade["side"] == "LONG":
                    if current_price <= trade["stop"]:
                        await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                        trade["status"] = "CLOSED"
                    else:
                        for i, target in enumerate(trade["targets"]):
                            if current_price >= target:
                                trade["current_target"] = i + 1
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {i + 1} Hit")
                                trade["targets"].pop(0)
                                break
                elif trade["side"] == "SHORT":
                    if current_price >= trade["stop"]:
                        await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                        trade["status"] = "CLOSED"
                    else:
                        for i, target in enumerate(trade["targets"]):
                            if current_price <= target:
                                trade["current_target"] = i + 1
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {i + 1} Hit")
                                trade["targets"].pop(0)
                                break
