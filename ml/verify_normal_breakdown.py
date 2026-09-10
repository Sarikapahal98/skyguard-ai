from data_simulator import generate_dataset
from detect import detect_anomaly

data = generate_dataset(n=500, fault_rate=0.15)
normal_rows = [r for r in data if r['label'] == 'NONE']
type_counts = {}
for row in normal_rows:
    reading = {k: row[k] for k in ['station_code','temperature','humidity','pressure','rainfall','wind_speed']}
    result = detect_anomaly(reading)
    t = result['anomaly_type']
    type_counts[t] = type_counts.get(t, 0) + 1
print(type_counts)