import numpy as np
import pandas as pd
import math

# Parameters
stop_percent = 25  # Stop percentage as a value out of 100
leverage = 50
num_take_profit_levels = 3

async def calculate_take_profits(entry_price, position_direction):
    take_profits = []
    for level in range(1, num_take_profit_levels + 1):
        if position_direction == "LONG":
            take_profit = entry_price + entry_price * level * (stop_percent / 100) / leverage
        else:
            take_profit = entry_price - entry_price * level * (stop_percent / 100) / leverage
        take_profits.append(take_profit)
    return take_profits

async def perform_technical_analysis(pair, prices, depth):
    entry_price = prices['close'].iloc[-1]
    # Calculate Twin Range Filter
    twin_range_filter = calculate_twin_range_filter(prices['close'])

    # Determine the trade direction based on Twin Range Filter
    if(math.isnan(twin_range_filter[0])):
        suggested_direction = "WAIT"
    else:
        if entry_price > twin_range_filter[0]:
            suggested_direction = "LONG"
            stop_price = entry_price * (1 - (stop_percent / leverage) / 100)
        else:
            suggested_direction = "SHORT"
            stop_price = entry_price * (1 + (stop_percent / leverage) / 100)

    take_profits = await calculate_take_profits(entry_price, suggested_direction)

    return {
        "pair": pair,
        "direction": suggested_direction,
        "leverage": leverage,
        "current_price": entry_price,
        "stop_loss": round(stop_price, depth),
        "take_profits": [round(tp, depth) for tp in take_profits],
    }

# Twin Range Filter Calculation
def calculate_twin_range_filter(source):
    # Calculate Smooth Average Range (SAR)
    per1 = 27
    mult1 = 1.6
    per2 = 55
    mult2 = 2
    
    smrng1 = smooth_range(source, per1, mult1)
    smrng2 = smooth_range(source, per2, mult2)
    smrng = (smrng1 + smrng2) / 2
    
    # Calculate Range Filter (RF)
    rf = range_filter(source, smrng)
    
    return rf

# Calculate Smooth Range
def smooth_range(source, period, multiplier):
    avg_range = pd.Series.abs(source - source.shift(1)).rolling(window=period).mean()
    weighted_period = 2 * period - 1
    smoothed_range = avg_range.ewm(span=weighted_period, adjust=False).mean() * multiplier
    return smoothed_range

# Calculate Range Filter
def range_filter(source, smooth_range):
    rf = source.copy()
    for i in range(1, len(source)):
        rf[i] = max(rf[i - 1] - smooth_range[i], min(rf[i - 1] + smooth_range[i], source[i]))
    return rf