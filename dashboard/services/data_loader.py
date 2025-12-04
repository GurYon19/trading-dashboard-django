"""
Data loading service for trading dashboard.
Handles CSV file discovery and loading.
"""
import os
import pandas as pd
from typing import Dict, Any


def find_instruments(folder: str) -> Dict[str, Dict[str, str]]:
    """
    Find all instrument pairs using '<prefix>-trades.csv' and '<prefix>-Summary.csv' pattern (case-insensitive).
    
    Args:
        folder: Path to folder containing CSV files
        
    Returns:
        Dictionary mapping instrument names to their file paths:
        {
            'instrument_name': {
                'summary': '/path/to/summary.csv',
                'trades': '/path/to/trades.csv'
            }
        }
    """
    if not os.path.exists(folder):
        return {}
    
    files = os.listdir(folder)
    instruments = {}

    # Normalize filenames for case-insensitive matching
    lower_to_actual = {f.lower(): f for f in files}

    trade_suffixes = ['-trades.csv', '-Trades.csv']
    summary_suffixes = ['-summary.csv', '-Summary.csv']

    trade_prefixes = set()
    summary_prefixes = set()

    for f in files:
        fl = f.lower()
        for suf in trade_suffixes:
            if fl.endswith(suf.lower()):
                trade_prefixes.add(fl[:-len(suf)])
                break
        for suf in summary_suffixes:
            if fl.endswith(suf.lower()):
                summary_prefixes.add(fl[:-len(suf)])
                break

    matched_prefixes = trade_prefixes.intersection(summary_prefixes)

    for prefix in matched_prefixes:
        trade_name = None
        summary_name = None
        for suf in trade_suffixes:
            candidate = prefix + suf
            if candidate.lower() in lower_to_actual:
                trade_name = lower_to_actual[candidate.lower()]
                break
        for suf in summary_suffixes:
            candidate = prefix + suf
            if candidate.lower() in lower_to_actual:
                summary_name = lower_to_actual[candidate.lower()]
                break
        if trade_name and summary_name:
            # Create short name: ROA305-GC-55 -> GC55
            clean_name = prefix.replace('ROA305-', '').replace('roa305-', '').replace('-', '')
            # Preserve case if possible, but prefix is from lowercase matching. 
            # Let's try to make it uppercase for consistency
            clean_name = clean_name.upper()
            
            instruments[clean_name] = {
                'summary': os.path.join(folder, summary_name),
                'trades': os.path.join(folder, trade_name)
            }

    return instruments


def load_trade_file(file_path: str) -> pd.DataFrame:
    """
    Load a trade CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with trades
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Trade file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {file_path}")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {file_path}: {str(e)}")
    
    if len(df) == 0:
        raise ValueError(f"CSV file contains no data rows: {file_path}")
    
    return df


def load_summary_file(file_path: str) -> pd.DataFrame:
    """
    Load a summary CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with summary data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Summary file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {file_path}")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {file_path}: {str(e)}")
    
    return df

