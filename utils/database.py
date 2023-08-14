import pickle

async def save_data(self):
    with open('trade_positions.pickle', 'wb') as f:
        pickle.dump(self.bot.trade_positions, f)
        f.close()