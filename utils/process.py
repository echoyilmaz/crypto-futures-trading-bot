from utils.embeds import send_position_close_embed, send_position_open_embed
from utils.database import save_data

import numpy as np

async def process_trade_data(self, new_trade):
    current_price = new_trade['entry']
    is_long_trade_open = await any_trade_open(self.bot.trade_positions, new_trade, "LONG")
    is_short_trade_open = await any_trade_open(self.bot.trade_positions, new_trade, "SHORT")

    if new_trade['side'] == 'SHORT' and is_long_trade_open:
        await close_opposing_trade(self.bot.trade_positions, new_trade, "LONG", current_price, self)
    elif new_trade['side'] == 'LONG' and is_short_trade_open:
        await close_opposing_trade(self.bot.trade_positions, new_trade, "SHORT", current_price, self)
    else:
        await handle_new_trade(self.bot.trade_positions, new_trade, is_long_trade_open, is_short_trade_open, current_price, self)

async def close_opposing_trade(trade_positions, new_trade, opposite_side, current_price, self):
    existing_trade = next((trade for trade in trade_positions if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == opposite_side), None)
    if existing_trade:
        existing_trade["status"] = "CLOSED"
        roi = await calculate_roi(existing_trade['entry'], current_price, existing_trade['leverage'], existing_trade['side'])
        existing_trade['roi'].append(roi)
        await send_position_close_embed(existing_trade, new_trade, self, "Opposing Signal Received")
        await save_data(self)
        print(existing_trade)

async def calculate_roi(entry_price, exit_price, leverage, trade_side):
    if trade_side == "LONG":
        return ((exit_price - entry_price) / entry_price) * 100 * leverage
    elif trade_side == "SHORT":
        return ((entry_price - exit_price) / entry_price) * 100 * leverage

async def any_trade_open(trade_positions, new_trade, side):
    return any(trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == side for trade in trade_positions)

async def handle_new_trade(trade_positions, new_trade, is_long_trade_open, is_short_trade_open, current_price, self):
    if (new_trade['side'] == 'LONG' and is_long_trade_open) or (new_trade['side'] == 'SHORT' and is_short_trade_open):
        return
    elif new_trade['side'] != 'WAIT':
        new_trade['status'] = "OPEN"
        trade_positions.append(new_trade)
        await send_position_open_embed(new_trade, self, "Trade Opened")
        await save_data(self)
        print(new_trade)

    print(new_trade)

    for trade in trade_positions:
        if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"]:
            await handle_open_trade(current_price, trade, new_trade, self)

async def handle_open_trade(current_price, trade, new_trade, self):
    if trade["side"] == "LONG":
        if current_price <= trade["stop"]:
            await close_trade_on_stop_loss(trade, new_trade, current_price, self)
        else:
            await handle_profit_targets(trade, current_price, new_trade, self)
    elif trade["side"] == "SHORT":
        if current_price >= trade["stop"]:
            await close_trade_on_stop_loss(trade, new_trade, current_price, self)
        else:
            await handle_profit_targets(trade, current_price, new_trade, self)

async def close_trade_on_stop_loss(trade, new_trade, current_price, self):
    trade["status"] = "CLOSED"
    roi = await calculate_roi(trade['entry'], current_price, trade['leverage'], trade['side'])
    trade['roi'].append(roi)
    await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
    await save_data(self)
    print(trade)

async def handle_profit_targets(trade, current_price, new_trade, self):
    for i, target in enumerate(trade["targets"]):
        target_value = target.item() if isinstance(target, np.float64) else target
        if (trade["side"] == "LONG" and current_price >= target_value) or (trade["side"] == "SHORT" and current_price <= target_value):
            trade["current_target"] = i + 1
            if trade["current_target"] == len(trade["targets"]):
                await close_trade_at_final_target(trade, new_trade, current_price, self)
            else:
                await update_trade_state_for_target_hit(trade, current_price, i, new_trade, self)
    trade["targets"] = trade["targets"][trade["current_target"]:]
    
async def close_trade_at_final_target(trade, new_trade, current_price, self):
    trade["status"] = "CLOSED"
    roi = await calculate_roi(trade['entry'], current_price, trade['leverage'], trade['side'])
    trade['roi'].append(roi)
    await send_position_close_embed(trade, new_trade, self, "Final Take Profit Hit")
    await save_data(self)
    print(trade)

async def update_trade_state_for_target_hit(trade, current_price, target_index, new_trade, self):
    roi = await calculate_roi(trade['entry'], current_price, trade['leverage'], trade['side'])
    trade['roi'].append(roi)
    if target_index == 0:
        trade["stop"] = trade['entry']
    await send_position_close_embed(trade, new_trade, self, f"Profit Target {trade['current_target']} Hit")
    await save_data(self)
    print(trade)
