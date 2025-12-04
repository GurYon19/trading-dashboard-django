"""
Debug script to test data loading from CSV files.
Run this to verify the data pipeline is working.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from dashboard.services.data_loader import find_instruments, load_trade_file
from dashboard.services.trade_processor import load_and_process_trades

print("=" * 60)
print("TRADING DASHBOARD DATA LOADING DEBUG")
print("=" * 60)

# 1. Check CSV folder path
print(f"\n1. CSV Folder Path: {settings.CSV_FOLDER_PATH}")
print(f"   Exists: {os.path.exists(settings.CSV_FOLDER_PATH)}")
print(f"   Absolute Path: {os.path.abspath(settings.CSV_FOLDER_PATH)}")

# 2. Find instruments
print(f"\n2. Finding instruments...")
instruments_dict = find_instruments(settings.CSV_FOLDER_PATH)
print(f"   Found {len(instruments_dict)} instruments:")
for name, paths in instruments_dict.items():
    print(f"   - {name}")
    print(f"     Trades: {paths['trades']}")
    print(f"     Summary: {paths['summary']}")

# 3. Test loading one instrument
if instruments_dict:
    test_instrument = list(instruments_dict.keys())[0]
    print(f"\n3. Testing load of '{test_instrument}'...")
    try:
        df = load_trade_file(instruments_dict[test_instrument]['trades'])
        print(f"   ✅ Loaded {len(df)} trades")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   First row:")
            print(f"   {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# 4. Test full processing
print(f"\n4. Testing full trade processing...")
try:
    selected_instruments = list(instruments_dict.keys())[:3]  # Test with first 3
    instrument_filters = {name: 'All' for name in selected_instruments}
    instrument_contracts = {name: 1 for name in selected_instruments}
    
    instruments_data, combined_df = load_and_process_trades(
        instruments_dict,
        selected_instruments,
        instrument_filters,
        instrument_contracts,
        '01/01/2024',
        '31/12/2024'
    )
    
    print(f"   ✅ Processed {len(combined_df)} total trades")
    print(f"   Instruments processed: {len(instruments_data)}")
    
    if len(combined_df) > 0:
        print(f"\n5. Sample Data:")
        print(f"   Total Profit: ${combined_df['Profit'].sum():.2f}")
        print(f"   Columns: {list(combined_df.columns)}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
