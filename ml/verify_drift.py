from data_simulator import generate_dataset
from detect import detect_anomaly

data = generate_dataset(n=500, fault_rate=0.15)
drift_rows = [r for r in data if r['label'] == 'DRIFT']
caught = 0
for row in drift_rows:
    reading = {k: row[k] for k in ['station_code','temperature','humidity','pressure','rainfall','wind_speed']}
    result = detect_anomaly(reading)
    if result['anomaly_detected']:
        caught += 1
print(f'Caught {caught}/{len(drift_rows)} DRIFT-labeled readings')
