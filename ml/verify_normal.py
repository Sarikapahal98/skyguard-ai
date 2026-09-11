from data_simulator import generate_dataset
from detect import detect_anomaly

data = generate_dataset(n=500, fault_rate=0.15)
normal_rows = [r for r in data if r['label'] == 'NONE']
false_positives = 0
for row in normal_rows:
    reading = {k: row[k] for k in ['station_code','temperature','humidity','pressure','rainfall','wind_speed']}
    result = detect_anomaly(reading)
    if result['anomaly_detected']:
        false_positives += 1
print(f'False positives: {false_positives}/{len(normal_rows)} NORMAL readings wrongly flagged')