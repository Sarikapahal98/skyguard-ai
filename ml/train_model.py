"""
SkyGuard AI — Model Training (P3's starting point)

Trains an IsolationForest on synthetic "normal" data, so it learns what
normal readings look like and can score new readings by how unusual they are.

Run:
    python train_model.py

Produces: model.joblib (loaded by detect.py at inference time)
"""
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

from data_simulator import generate_dataset

FEATURES = ["temperature", "humidity", "pressure", "rainfall", "wind_speed"]


def main():
    print("Generating synthetic training data...")
    data = generate_dataset(n=3000, fault_rate=0.05)
    df = pd.DataFrame(data)

    # Train only on data labeled NONE (i.e. "normal") so the model learns
    # what normal looks like — this mirrors how you'd train on real historical data.
    normal_df = df[df["label"] == "NONE"][FEATURES]

    print(f"Training IsolationForest on {len(normal_df)} normal readings...")
    model = IsolationForest(
        n_estimators=150,
        contamination=0.05,   # expected proportion of anomalies
        random_state=42,
    )
    model.fit(normal_df)

    joblib.dump(model, "model.joblib")
    print("Saved model.joblib")

    # Quick sanity check on the full (labeled) dataset
    df["predicted_anomaly"] = model.predict(df[FEATURES]) == -1
    df["actual_anomaly"] = df["label"] != "NONE"
    accuracy = (df["predicted_anomaly"] == df["actual_anomaly"]).mean()
    print(f"Rough sanity-check accuracy on synthetic data: {accuracy:.2%}")


if __name__ == "__main__":
    main()
