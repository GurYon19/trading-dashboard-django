"""
Trade processing service for trading dashboard.
Handles trade filtering, combining, and contract multiplier application.
"""
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, Union, List


def load_and_filter_trades(trade_file: str, start_date: Union[str, datetime], end_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Load trades from CSV and filter by date range.
    
    Args:
        trade_file: Path to CSV file
        start_date: Start date (datetime object or string in format 'dd/mm/yyyy')
        end_date: End date (datetime object or string in format 'dd/mm/yyyy')
    
    Returns:
        DataFrame with filtered and cleaned trades
    
    Raises:
        FileNotFoundError: If trade_file doesn't exist
        ValueError: If CSV is empty, missing required columns, or has invalid data
    """
    # Validate file exists
    if not os.path.exists(trade_file):
        raise FileNotFoundError(f"Trade file not found: {trade_file}")
    
    # Load CSV
    try:
        df = pd.read_csv(trade_file)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {trade_file}")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {trade_file}: {str(e)}")
    
    # Validate required columns
    required_columns = ['Entry time', 'Exit time']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {', '.join(missing_columns)}. "
                        f"Available columns: {', '.join(df.columns.tolist())}")
    
    # Check if dataframe is empty
    if len(df) == 0:
        raise ValueError(f"CSV file contains no data rows: {trade_file}")
    
    # Parse dates with error handling
    try:
        df['Entry time'] = pd.to_datetime(df['Entry time'], format='%d/%m/%Y %H:%M:%S')
    except Exception as e:
        raise ValueError(f"Failed to parse 'Entry time' column. Expected format: dd/mm/yyyy HH:MM:SS. Error: {str(e)}")
    
    try:
        df['Exit time'] = pd.to_datetime(df['Exit time'], format='%d/%m/%Y %H:%M:%S')
    except Exception as e:
        raise ValueError(f"Failed to parse 'Exit time' column. Expected format: dd/mm/yyyy HH:MM:SS. Error: {str(e)}")
    
    # Convert start_date and end_date to datetime if they're strings
    if isinstance(start_date, str):
        try:
            start = datetime.strptime(start_date, '%d/%m/%Y')
        except Exception as e:
            raise ValueError(f"Invalid start_date format: {start_date}. Expected: dd/mm/yyyy")
    else:
        start = start_date
    
    if isinstance(end_date, str):
        try:
            end = datetime.strptime(end_date, '%d/%m/%Y') + pd.Timedelta(days=1)
        except Exception as e:
            raise ValueError(f"Invalid end_date format: {end_date}. Expected: dd/mm/yyyy")
    else:
        end = end_date + pd.Timedelta(days=1)
    
    # Filter by date range
    df_filtered = df[(df['Entry time'] >= start) & (df['Entry time'] < end)].copy()
    
    # Clean all monetary columns (convert from string "$1,234.00" to float)
    monetary_columns = ['Profit', 'MAE', 'MFE', 'ETD', 'Commission', 
                       'Clearing Fee', 'Exchange Fee', 'IP Fee', 'NFA Fee', 'Cum. net profit']
    
    for col in monetary_columns:
        if col in df_filtered.columns:
            if df_filtered[col].dtype == 'object':
                df_filtered[col] = df_filtered[col].str.replace('$', '', regex=False)
                df_filtered[col] = df_filtered[col].str.replace(',', '', regex=False)
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
    
    # Sort by entry time
    df_filtered = df_filtered.sort_values('Entry time').reset_index(drop=True)
    
    return df_filtered


def filter_trades_by_direction(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    """
    Filter trades by direction (Long/Short).
    
    Args:
        df: DataFrame with trades
        direction: 'All', 'Long Only', or 'Short Only'
    
    Returns:
        Filtered DataFrame
    """
    if direction == "All" or 'Market pos.' not in df.columns:
        return df
    
    if direction == "Long Only":
        return df[df['Market pos.'] == 'Long'].copy()
    elif direction == "Short Only":
        return df[df['Market pos.'] == 'Short'].copy()
    
    return df


def apply_contract_multiplier(df: pd.DataFrame, multiplier: int) -> pd.DataFrame:
    """
    Apply contract multiplier to all monetary columns.
    
    Args:
        df: DataFrame with trades
        multiplier: Number of contracts (default: 1)
    
    Returns:
        DataFrame with adjusted monetary values
    """
    if multiplier == 1 or len(df) == 0:
        return df
    
    df = df.copy()
    
    # List of monetary columns that should be multiplied by contract count
    monetary_columns = ['Profit', 'MAE', 'MFE', 'ETD', 'Commission', 
                       'Clearing Fee', 'Exchange Fee', 'IP Fee', 'NFA Fee']
    
    for col in monetary_columns:
        if col in df.columns:
            df[col] = df[col] * multiplier
    
    return df


def load_and_process_trades(
    instruments: Dict[str, Dict[str, str]],
    selected_instruments: Union[List[str], Dict[str, bool]],
    instrument_filters: Dict[str, str],
    instrument_contracts: Dict[str, int],
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Load and filter trades based on selections.
    
    Args:
        instruments: Dictionary of instrument names to file paths
        selected_instruments: List of selected instrument names, or dict of instrument names to boolean
        instrument_filters: Dictionary of instrument names to filter option ('All', 'Long Only', 'Short Only')
        instrument_contracts: Dictionary of instrument names to contract multiplier
        start_date: Start date (datetime or string 'dd/mm/yyyy')
        end_date: End date (datetime or string 'dd/mm/yyyy')
    
    Returns:
        Tuple of (instruments_data, combined_df):
        - instruments_data: Dict mapping instrument names to their processed data
        - combined_df: Combined DataFrame of all selected instruments
    """
    all_trades = []
    instruments_data = {}
    
    # Convert dates to string format if they're datetime objects
    if isinstance(start_date, datetime):
        start_str = start_date.strftime('%d/%m/%Y')
    else:
        start_str = start_date
    
    if isinstance(end_date, datetime):
        end_str = end_date.strftime('%d/%m/%Y')
    else:
        end_str = end_date
    
    # Handle both list and dict formats for selected_instruments
    if isinstance(selected_instruments, dict):
        # Convert dict to list of selected instrument names
        selected_list = [name for name, selected in selected_instruments.items() if selected]
    else:
        selected_list = selected_instruments if selected_instruments else []
    
    print(f"DEBUG trade_processor: selected_list = {selected_list}, type = {type(selected_instruments)}")
    print(f"DEBUG trade_processor: instruments keys = {list(instruments.keys())}")
    
    for name, files in instruments.items():
        if name in selected_list:
            try:
                df = load_and_filter_trades(files['trades'], start_str, end_str)
                
                # Apply Long/Short filter
                filter_option = instrument_filters.get(name, "All")
                df = filter_trades_by_direction(df, filter_option)
                
                # Apply contract multiplier
                contracts = instrument_contracts.get(name, 1)
                df = apply_contract_multiplier(df, contracts)
                
                if len(df) > 0:
                    df['Instrument'] = name
                    df['Contracts'] = contracts  # Store for reference
                    all_trades.append(df)
                    instruments_data[name] = {
                        'trades': df,
                        'files': files,
                        'contracts': contracts
                    }
            except Exception as e:
                # Log error but continue with other instruments
                print(f"Error processing {name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
    
    if len(all_trades) == 0:
        return {}, pd.DataFrame()
    
    combined_df = pd.concat(all_trades, ignore_index=True)
    combined_df = combined_df.sort_values('Entry time').reset_index(drop=True)
    
    return instruments_data, combined_df

