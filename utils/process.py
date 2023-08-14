from utils.embeds import send_position_close_embed, send_position_open_embed
from utils.database import save_data

async def process_trade_data(self, new_trade):
    for trade in self.bot.trade_positions:
        if trade["status"] == "OPEN" and trade["pair"] == new_trade["pair"]:
            current_price = new_trade['entry']  # Use the entry price as the current price from the fetched result

            if trade["side"] == "LONG":
                if current_price <= trade["stop"]:
                    trade["status"] = "CLOSED"
                    roi = ((current_price - trade['entry']) / trade['entry']) * 100 * (trade['leverage'])        
                    trade['roi'].append(roi)
                    await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                    await save_data(self)
                    print(trade)
                else:
                    last_hit_target = trade["current_target"]
                    for i, target in enumerate(trade["targets"][last_hit_target:]):
                        if current_price >= target:
                            trade["current_target"] = last_hit_target + i + 1
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
                                if i == 0:  # Move stop loss to entry after hitting the first target
                                    trade["stop"] = trade['entry']
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {trade['current_target']} Hit")
                                await save_data(self)
                                print(trade)
                    trade["targets"] = trade["targets"][trade["current_target"] - last_hit_target:]

            elif trade["side"] == "SHORT":
                if current_price >= trade["stop"]:
                    trade["status"] = "CLOSED"
                    roi = ((trade['entry'] - current_price) / trade['entry']) * 100 * (trade['leverage'])         
                    trade['roi'].append(roi)
                    await send_position_close_embed(trade, new_trade, self, "Stop Loss Hit")
                    print(trade)
                else:
                    last_hit_target = trade["current_target"]
                    for i, target in enumerate(trade["targets"][last_hit_target:]):
                        if current_price <= target:
                            trade["current_target"] = last_hit_target + i + 1
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
                                if i == 0:  # Move stop loss to entry after hitting the first target
                                    trade["stop"] = trade['entry']
                                await send_position_close_embed(trade, new_trade, self, f"Profit Target {trade['current_target']} Hit")
                                await save_data(self)
                                print(trade)
                    trade["targets"] = trade["targets"][trade["current_target"] - last_hit_target:]
    
    if new_trade['side'] in ['LONG', 'SHORT']:
        new_trade['status'] = "OPEN"
        self.bot.trade_positions.append(new_trade)
        await send_position_open_embed(new_trade, self)
        print(new_trade)
        await save_data(self)