import csv
from collections import defaultdict
from pathlib import Path
import sys

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'c:\Users\yonig\Desktop\strategies.csv')

with csv_path.open(newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader if any(v.strip() for v in row.values())]

account_to_keys = defaultdict(set)

for r in rows:
    connection = (r.get('Connection') or '').strip()
    strategy = (r.get('Strategy') or '').strip()
    instrument = (r.get('Instrument') or '').strip()
    parameters = (r.get('Parameters') or '').strip()
    if not connection:
        continue
    key = (strategy, instrument, parameters)
    account_to_keys[connection].add(key)

connections = sorted(account_to_keys.keys())
print(f'Connections detected: {connections}')
print(f'Counts: {[(conn, len(account_to_keys[conn])) for conn in connections]}')
print()

if len(connections) == 2:
    conn1, conn2 = connections
    only_in_conn1 = sorted(account_to_keys[conn1] - account_to_keys[conn2])
    only_in_conn2 = sorted(account_to_keys[conn2] - account_to_keys[conn1])
    
    print(f'{conn1}: {len(account_to_keys[conn1])} strategies')
    print(f'{conn2}: {len(account_to_keys[conn2])} strategies')
    print()
    
    if not only_in_conn1 and not only_in_conn2:
        print('SUCCESS: Both connections have identical strategies!')
        print('(Strategy, Instrument, and Parameters all match)')
    else:
        print('MISMATCHES FOUND:')
        if only_in_conn1:
            print(f'\n  Only in {conn1} ({len(only_in_conn1)} strategies):')
            for strategy, instrument, parameters in only_in_conn1:
                print(f'    - {strategy} | {instrument}')
                print(f'      Params: {parameters[:80]}...' if len(parameters) > 80 else f'      Params: {parameters}')
        if only_in_conn2:
            print(f'\n  Only in {conn2} ({len(only_in_conn2)} strategies):')
            for strategy, instrument, parameters in only_in_conn2:
                print(f'    - {strategy} | {instrument}')
                print(f'      Params: {parameters[:80]}...' if len(parameters) > 80 else f'      Params: {parameters}')

