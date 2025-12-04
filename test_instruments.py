"""Simple test to check instrument discovery"""
import os

csv_folder = os.path.join(os.getcwd(), 'csv_exports')
print(f"CSV Folder: {csv_folder}")
print(f"Exists: {os.path.exists(csv_folder)}")

if os.path.exists(csv_folder):
    files = os.listdir(csv_folder)
    print(f"\nTotal files: {len(files)}")
    print("\nSample files:")
    for f in files[:10]:
        print(f"  - {f}")
    
    # Test instrument matching
    print("\n--- Testing Instrument Discovery ---")
    lower_to_actual = {f.lower(): f for f in files}
    
    trade_suffixes = ['-trades.csv', '-Trades.csv']
    summary_suffixes = ['-summary.csv', '-Summary.csv']
    
    trade_prefixes = set()
    summary_prefixes = set()
    
    for f in files:
        fl = f.lower()
        for suf in trade_suffixes:
            if fl.endswith(suf.lower()):
                prefix = fl[:-len(suf)]
                trade_prefixes.add(prefix)
                print(f"Trade file: {f} -> prefix: {prefix}")
                break
        for suf in summary_suffixes:
            if fl.endswith(suf.lower()):
                prefix = fl[:-len(suf)]
                summary_prefixes.add(prefix)
                print(f"Summary file: {f} -> prefix: {prefix}")
                break
    
    matched = trade_prefixes.intersection(summary_prefixes)
    print(f"\nMatched prefixes: {len(matched)}")
    for prefix in sorted(matched):
        print(f"  - {prefix}")
