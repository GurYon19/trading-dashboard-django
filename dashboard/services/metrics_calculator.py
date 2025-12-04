"""
Metrics calculation service for trading dashboard.
Handles all statistics calculations for trading data.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any


def calculate_max_consecutive(profits: np.ndarray, direction: int) -> int:
    """
    Calculate maximum consecutive winners (1) or losers (-1).
    
    Args:
        profits: Array of profit values
        direction: 1 for winners, -1 for losers
    
    Returns:
        Maximum consecutive count
    """
    if len(profits) == 0:
        return 0
    
    max_consec = 0
    current_consec = 0
    
    for profit in profits:
        if (direction == 1 and profit > 0) or (direction == -1 and profit < 0):
            current_consec += 1
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = 0
    
    return max_consec


def calculate_recovery_and_flat_periods(df: pd.DataFrame, equity_curve: pd.Series) -> Tuple[pd.Timedelta, pd.Timedelta, pd.Timedelta, float]:
    """
    Calculate Max Time to Recover, Max Flat Period, and other time-based stats.
    
    Args:
        df: DataFrame with trades
        equity_curve: Series with cumulative equity values
    
    Returns:
        Tuple of (max_time_to_recover, max_flat_period, avg_flat_period, pct_time_in_market)
    """
    if len(df) == 0 or len(equity_curve) == 0:
        return pd.Timedelta(0), pd.Timedelta(0), pd.Timedelta(0), 0.0

    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Entry time']):
        df = df.copy()
        df['Entry time'] = pd.to_datetime(df['Entry time'])
    if not pd.api.types.is_datetime64_any_dtype(df['Exit time']):
        df = df.copy()
        df['Exit time'] = pd.to_datetime(df['Exit time'])

    # 1. Max Time to Recover (Equity Peaks)
    # Find longest duration between new equity highs
    max_time_to_recover = pd.Timedelta(0)
    
    # We need to associate equity values with time.
    # Equity is realized at Exit time.
    # Create a dataframe with Time and Equity
    eq_df = pd.DataFrame({
        'Time': df['Exit time'],
        'Equity': equity_curve.values
    })
    
    current_peak = -float('inf')
    peak_time = None
    
    for _, row in eq_df.iterrows():
        equity = row['Equity']
        time = row['Time']
        
        if equity > current_peak:
            if peak_time is not None:
                recovery_time = time - peak_time
                if recovery_time > max_time_to_recover:
                    max_time_to_recover = recovery_time
            
            current_peak = equity
            peak_time = time
    
    # 2. Flat Periods (No Trades)
    # Merge overlapping trade intervals to find true gaps
    intervals = []
    for _, row in df.iterrows():
        intervals.append((row['Entry time'], row['Exit time']))
    
    intervals.sort(key=lambda x: x[0])
    
    merged = []
    if intervals:
        curr_start, curr_end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start < curr_end:  # Overlap
                curr_end = max(curr_end, next_end)
            else:
                merged.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged.append((curr_start, curr_end))
    
    # Calculate gaps
    flat_periods = []
    for i in range(len(merged) - 1):
        gap = merged[i+1][0] - merged[i][1]
        flat_periods.append(gap)
    
    max_flat_period = max(flat_periods) if flat_periods else pd.Timedelta(0)
    avg_flat_period = pd.Series(flat_periods).mean() if flat_periods else pd.Timedelta(0)
    
    # 3. % Time in Market (Days)
    # Calculated as (Number of Unique Trading Days / Total Days in Period)
    unique_trading_days = df['Entry time'].dt.date.nunique()
    
    if len(df) > 0:
        start_date = df['Entry time'].min()
        end_date = df['Exit time'].max()
        total_days = (end_date - start_date).days + 1
        if total_days < 1:
            total_days = 1
    else:
        total_days = 1
    
    pct_time_in_market = (unique_trading_days / total_days * 100) if total_days > 0 else 0.0

    return max_time_to_recover, max_flat_period, avg_flat_period, pct_time_in_market


def calculate_comprehensive_stats(df: pd.DataFrame, instrument_name: str = '') -> Tuple[Dict[str, Any], pd.Series, pd.Series]:
    """
    Calculate comprehensive trading statistics.
    
    Args:
        df: DataFrame with trades (must have 'Profit' column)
        instrument_name: Name of the instrument (for labeling)
    
    Returns:
        Tuple of (stats_dict, equity_curve, drawdown):
        - stats_dict: Dictionary with all calculated statistics
        - equity_curve: Series with cumulative equity values
        - drawdown: Series with drawdown values
    """
    if len(df) == 0:
        return {}, pd.Series(dtype=float), pd.Series(dtype=float)
    
    profits = df['Profit'].values
    
    # Basic stats
    total_profit = profits.sum()
    gross_profit = profits[profits > 0].sum() if len(profits[profits > 0]) > 0 else 0
    gross_loss = profits[profits < 0].sum() if len(profits[profits < 0]) > 0 else 0
    num_trades = len(df)
    num_winners = len(profits[profits > 0])
    num_losers = len(profits[profits < 0])
    win_rate = (num_winners / num_trades * 100) if num_trades > 0 else 0
    
    # Trade statistics
    avg_trade = profits.mean()
    avg_win = profits[profits > 0].mean() if num_winners > 0 else 0
    avg_loss = profits[profits < 0].mean() if num_losers > 0 else 0
    win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    # Profit factor
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf') if gross_profit > 0 else 0
    
    # Largest trades
    largest_win = profits.max()
    largest_loss = profits.min()
    
    # Equity curve and drawdown
    equity_curve = pd.Series(profits).cumsum()
    running_max = equity_curve.expanding().max()
    drawdown = equity_curve - running_max
    max_drawdown = drawdown.min()
    
    # Consecutive winners/losers
    max_consec_winners = calculate_max_consecutive(profits, 1)
    max_consec_losers = calculate_max_consecutive(profits, -1)
    
    # Expectancy
    expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * abs(avg_loss))
    
    # Time statistics
    if 'Entry time' in df.columns and 'Exit time' in df.columns:
        # Convert to datetime if not already
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['Entry time']):
            df['Entry time'] = pd.to_datetime(df['Entry time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        if not pd.api.types.is_datetime64_any_dtype(df['Exit time']):
            df['Exit time'] = pd.to_datetime(df['Exit time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        holding_times = (df['Exit time'] - df['Entry time']).dt.total_seconds() / 60  # minutes
        avg_time_in_market = holding_times.mean() if len(holding_times) > 0 else 0
    else:
        avg_time_in_market = 0
    
    # Bars in trade
    avg_bars = df['Bars'].mean() if 'Bars' in df.columns else 0
    
    # Sharpe ratio (simplified - using trade returns)
    if num_trades > 1:
        sharpe_ratio = (avg_trade / profits.std()) * np.sqrt(252) if profits.std() != 0 else 0
    else:
        sharpe_ratio = 0
    
    # Recovery and Flat Periods
    max_time_to_recover, max_flat_period, avg_flat_period, pct_time_in_market = calculate_recovery_and_flat_periods(df, equity_curve)
    
    stats = {
        'Instrument': instrument_name,
        'Total Net Profit': total_profit,
        'Gross Profit': gross_profit,
        'Gross Loss': gross_loss,
        'Number of Trades': num_trades,
        'Number of Winning Trades': num_winners,
        'Number of Losing Trades': num_losers,
        'Percent Profitable': win_rate,
        'Avg Trade': avg_trade,
        'Avg Winning Trade': avg_win,
        'Avg Losing Trade': avg_loss,
        'Ratio Avg Win/Avg Loss': win_loss_ratio,
        'Profit Factor': profit_factor if profit_factor != float('inf') else 0,
        'Largest Winning Trade': largest_win,
        'Largest Losing Trade': largest_loss,
        'Max Drawdown': max_drawdown,
        'Max Consecutive Winners': max_consec_winners,
        'Max Consecutive Losers': max_consec_losers,
        'Expectancy': expectancy,
        'Avg Time in Market (minutes)': avg_time_in_market,
        'Avg Bars in Trade': avg_bars,
        'Sharpe Ratio': sharpe_ratio,
        'Max Time to Recover': max_time_to_recover,
        'Max Flat Period': max_flat_period,
        'Avg Flat Period': avg_flat_period,
        'Time in Market %': pct_time_in_market,
    }
    
    return stats, equity_curve, drawdown


def calculate_day_of_week_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics grouped by day of week.
    
    Args:
        df: DataFrame with trades (must have 'Entry time' and 'Profit' columns)
    
    Returns:
        DataFrame with statistics per day of week
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    # Ensure Entry time is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['Entry time']):
        df['Entry time'] = pd.to_datetime(df['Entry time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # Extract day of week (Monday=0, Sunday=6)
    df['DayOfWeek'] = df['Entry time'].dt.dayofweek
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['DayName'] = df['DayOfWeek'].map(lambda x: day_names[x] if pd.notna(x) else 'Unknown')
    
    # Group by day of week
    day_stats = []
    
    for day_num in range(7):
        day_df = df[df['DayOfWeek'] == day_num].copy()
        if len(day_df) == 0:
            continue
        
        profits = day_df['Profit'].values
        total_profit = profits.sum()
        num_trades = len(day_df)
        num_winners = len(profits[profits > 0])
        num_losers = len(profits[profits < 0])
        win_rate = (num_winners / num_trades * 100) if num_trades > 0 else 0
        avg_trade = profits.mean()
        avg_win = profits[profits > 0].mean() if num_winners > 0 else 0
        avg_loss = profits[profits < 0].mean() if num_losers > 0 else 0
        gross_profit = profits[profits > 0].sum() if num_winners > 0 else 0
        gross_loss = profits[profits < 0].sum() if num_losers > 0 else 0
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf') if gross_profit > 0 else 0
        
        day_stats.append({
            'DayOfWeek': day_num,
            'DayName': day_names[day_num],
            'Total Net Profit': total_profit,
            'Number of Trades': num_trades,
            'Number of Winning Trades': num_winners,
            'Number of Losing Trades': num_losers,
            'Percent Profitable': win_rate,
            'Avg Trade': avg_trade,
            'Avg Winning Trade': avg_win,
            'Avg Losing Trade': avg_loss,
            'Gross Profit': gross_profit,
            'Gross Loss': gross_loss,
            'Profit Factor': profit_factor if profit_factor != float('inf') else 0,
        })
    
    return pd.DataFrame(day_stats).sort_values('DayOfWeek')


def calculate_daily_instrument_stats(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Calculate statistics about instruments traded per day.
    
    Args:
        df: DataFrame with trades (must have 'Entry time', 'Instrument', and 'Profit' columns)
    
    Returns:
        Tuple of (stats_dict, daily_instruments_df):
        - stats_dict: Dictionary with statistics
        - daily_instruments_df: DataFrame with daily instrument counts
    """
    if len(df) == 0:
        return {}, pd.DataFrame()
    
    # Ensure Entry time is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['Entry time']):
        df['Entry time'] = pd.to_datetime(df['Entry time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # Extract date (without time)
    df['Date'] = df['Entry time'].dt.date
    
    # Group by date and count unique instruments
    daily_instruments = df.groupby('Date')['Instrument'].nunique().reset_index()
    daily_instruments.columns = ['Date', 'Num_Instruments']
    
    # Calculate statistics
    max_instruments = daily_instruments['Num_Instruments'].max()
    avg_instruments = daily_instruments['Num_Instruments'].mean()
    min_instruments = daily_instruments['Num_Instruments'].min()
    
    # Find days with max instruments and get instrument names
    max_instrument_days = daily_instruments[daily_instruments['Num_Instruments'] == max_instruments]['Date'].tolist()
    
    # Get instrument names for max days
    max_day_instruments = {}
    for date in max_instrument_days:
        instruments = df[df['Date'] == date]['Instrument'].unique().tolist()
        max_day_instruments[date] = sorted(instruments)
    
    # Count days by number of instruments
    instrument_count_distribution = daily_instruments['Num_Instruments'].value_counts().sort_index()
    
    # Get daily profit by number of instruments traded
    daily_profit = df.groupby('Date').agg({
        'Profit': 'sum',
        'Instrument': 'nunique'
    }).reset_index()
    daily_profit.columns = ['Date', 'Daily_Profit', 'Num_Instruments']
    
    # Calculate average profit by number of instruments
    avg_profit_by_instruments = daily_profit.groupby('Num_Instruments')['Daily_Profit'].agg(['mean', 'sum', 'count']).reset_index()
    avg_profit_by_instruments.columns = ['Num_Instruments', 'Avg_Daily_Profit', 'Total_Profit', 'Num_Days']
    
    # Get detailed instrument list per date
    daily_instrument_details = df.groupby('Date').agg({
        'Instrument': lambda x: ', '.join(sorted(x.unique())),
        'Profit': 'sum'
    }).reset_index()
    daily_instrument_details.columns = ['Date', 'Instruments', 'Daily_Profit']
    daily_instrument_details['Num_Instruments'] = daily_instrument_details['Instruments'].apply(lambda x: len(x.split(', ')))
    
    stats = {
        'max_instruments': max_instruments,
        'avg_instruments': avg_instruments,
        'min_instruments': min_instruments,
        'total_trading_days': len(daily_instruments),
        'max_instrument_days': max_instrument_days,
        'max_day_instruments': max_day_instruments,
        'distribution': instrument_count_distribution,
        'daily_data': daily_profit,
        'profit_by_instruments': avg_profit_by_instruments,
        'daily_details': daily_instrument_details
    }
    
    return stats, daily_instruments


def calculate_5min_window_stats(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Calculate statistics about max instruments with entries in same 5-minute window.
    
    Args:
        df: DataFrame with trades (must have 'Entry time', 'Instrument', and 'Profit' columns)
    
    Returns:
        Tuple of (stats_dict, window_instruments_df):
        - stats_dict: Dictionary with statistics
        - window_instruments_df: DataFrame with 5-minute window instrument counts
    """
    if len(df) == 0:
        return {}, pd.DataFrame()
    
    # Ensure Entry time is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['Entry time']):
        df['Entry time'] = pd.to_datetime(df['Entry time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # Round entry time to 5-minute windows
    df['Time_Window'] = df['Entry time'].dt.floor('5min')
    
    # Group by 5-minute window and count unique instruments
    window_instruments = df.groupby('Time_Window')['Instrument'].nunique().reset_index()
    window_instruments.columns = ['Time_Window', 'Num_Instruments']
    
    # Calculate statistics
    max_instruments = window_instruments['Num_Instruments'].max()
    avg_instruments = window_instruments['Num_Instruments'].mean()
    min_instruments = window_instruments['Num_Instruments'].min()
    total_windows = len(window_instruments)
    
    # Find windows with max instruments
    max_instrument_windows = window_instruments[window_instruments['Num_Instruments'] == max_instruments]['Time_Window'].tolist()
    
    # Get instrument names for max windows
    max_window_instruments = {}
    for time_window in max_instrument_windows[:10]:  # Limit to first 10 to avoid overwhelming display
        instruments = df[df['Time_Window'] == time_window]['Instrument'].unique().tolist()
        max_window_instruments[time_window] = sorted(instruments)
    
    # Count windows by number of instruments
    instrument_count_distribution = window_instruments['Num_Instruments'].value_counts().sort_index()
    
    # Get profit by number of instruments in window
    window_profit = df.groupby('Time_Window').agg({
        'Profit': 'sum',
        'Instrument': 'nunique'
    }).reset_index()
    window_profit.columns = ['Time_Window', 'Window_Profit', 'Num_Instruments']
    
    # Calculate average profit by number of instruments
    avg_profit_by_instruments = window_profit.groupby('Num_Instruments')['Window_Profit'].agg(['mean', 'sum', 'count']).reset_index()
    avg_profit_by_instruments.columns = ['Num_Instruments', 'Avg_Window_Profit', 'Total_Profit', 'Num_Windows']
    
    # Get detailed instrument list per window (limit to show manageable amount)
    window_instrument_details = df.groupby('Time_Window').agg({
        'Instrument': lambda x: ', '.join(sorted(x.unique())),
        'Profit': 'sum'
    }).reset_index()
    window_instrument_details.columns = ['Time_Window', 'Instruments', 'Window_Profit']
    window_instrument_details['Num_Instruments'] = window_instrument_details['Instruments'].apply(lambda x: len(x.split(', ')))
    
    # Sort by time and take sample (latest windows or max diversification windows)
    window_instrument_details = window_instrument_details.sort_values('Num_Instruments', ascending=False).head(50)
    
    stats = {
        'max_instruments': max_instruments,
        'avg_instruments': avg_instruments,
        'min_instruments': min_instruments,
        'total_windows': total_windows,
        'max_instrument_windows': max_instrument_windows[:10],  # Limit display
        'max_window_instruments': max_window_instruments,
        'distribution': instrument_count_distribution,
        'window_data': window_profit,
        'profit_by_instruments': avg_profit_by_instruments,
        'window_details': window_instrument_details
    }
    
    return stats, window_instruments

