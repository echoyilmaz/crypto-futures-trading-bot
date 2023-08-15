from utils.embeds import send_position_close_embed, send_position_open_embed
from utils.database import save_data

import numpy as np

async def process_trade_data(self, new_trade):
    current_price = new_trade['entry']
    is_long_trade_open = any(trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == "LONG" for trade in self.bot.trade_positions)
    is_short_trade_open = any(trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == "SHORT" for trade in self.bot.trade_positions)
    
    if new_trade['side'] == 'SHORT' and is_long_trade_open:
        existing_trade = next((trade for trade in self.bot.trade_positions if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == "LONG"), None)
        if existing_trade:
            existing_trade["status"] = "CLOSED"
            roi = ((current_price - existing_trade['entry']) / existing_trade['entry']) * 100 * (existing_trade['leverage'])
            existing_trade['roi'].append(roi)
            await send_position_close_embed(existing_trade, new_trade, self, "Opposing Signal Received")
            await save_data(self)
            print(existing_trade)
    elif new_trade['side'] == 'LONG' and is_short_trade_open:
        existing_trade = next((trade for trade in self.bot.trade_positions if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"] and trade["side"] == "SHORT"), None)
        if existing_trade:
            existing_trade["status"] = "CLOSED"
            roi = ((existing_trade['entry'] - current_price) / existing_trade['entry']) * 100 * (existing_trade['leverage'])
            existing_trade['roi'].append(roi)
            await send_position_close_embed(existing_trade, new_trade, self, "Opposing Signal Received")
            await save_data(self)
            print(existing_trade)

    if new_trade['side'] == 'LONG' and is_long_trade_open:
        pass
    elif new_trade['side'] == 'SHORT' and is_short_trade_open:
        pass
    elif new_trade['side'] != 'WAIT':
        new_trade['status'] = "OPEN"
        self.bot.trade_positions.append(new_trade)
        await send_position_open_embed(new_trade, self, "Trade Opened")
        await save_data(self)
        print(new_trade)
    
    print(new_trade)

    for trade in self.bot.trade_positions:
        if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"]:
            if trade["side"] == "LONG":
                if current_price <= trade["stop"]:
                    trade["status"] = "CLOSED"
                    roi = ((current_price - trade['entry']) / trade['entry']) * 100 * (trade['leverage'])
                    trade['roi'].append(roi)
                    await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                    await save_data(self)
                    print(trade)
                else:
                    for i, target in enumerate(trade["targets"]):
                        if isinstance(target, np.float64):
                            target_value = target.item()  # Convert numpy float64 to regular float
                        else:
                            target_value = target
                        if current_price >= target_value:
                            trade["current_target"] = i + 1
                            if trade["current_target"] == len(trade["targets"]):
                                trade["status"] = "CLOSED"
                                roi = ((current_price - trade['entry']) / trade['entry']) * 100 * (trade['leverage'])
                                trade['roi'].append(roi)
                                await send_position_close_embed(trade, new_trade, self, "Final Take Profit Hit")
                                await save_data(self)
                                print(trade)
                            else:
                                roi = ((current_price - trade['entry']) / trade['entry']) * 100 * (trade['leverage'])
                                trade['roi'].append(roi)
                                if i == 0:
                                    trade["stop"] = trade['entry']
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {trade['current_target']} Hit")
                                await save_data(self)
                                print(trade)
                    trade["targets"] = trade["targets"][trade["current_target"]:]
            elif trade["side"] == "SHORT":
                if current_price >= trade["stop"]:
                    trade["status"] = "CLOSED"
                    roi = ((trade['entry'] - current_price) / trade['entry']) * 100 * (trade['leverage'])
                    trade['roi'].append(roi)
                    await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                    await save_data(self)
                    print(trade)
                else:
                    for i, target in enumerate(trade["targets"]):
                        if isinstance(target, np.float64):
                            target_value = target.item()  # Convert numpy float64 to regular float
                        else:
                            target_value = target
                        if current_price <= target_value:
                            trade["current_target"] = i + 1
                            if trade["current_target"] == len(trade["targets"]):
                                trade["status"] = "CLOSED"
                                roi = ((trade['entry'] - current_price) / trade['entry']) * 100 * (trade['leverage'])
                                trade['roi'].append(roi)
                                await send_position_close_embed(trade, new_trade, self, "Final Take Profit Hit")
                                await save_data(self)
                                print(trade)
                            else:
                                roi = ((trade['entry'] - current_price) / trade['entry']) * 100 * (trade['leverage'])
                                trade['roi'].append(roi)
                                if i == 0:
                                    trade["stop"] = trade['entry']
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {trade['current_target']} Hit")
                                await save_data(self)
                                print(trade)
                    trade["targets"] = trade["targets"][trade["current_target"]:]

