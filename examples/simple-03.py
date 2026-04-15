# example3_anomaly.py
import numpy as np
from czoi.neural.components import AnomalyDetector

# Generate synthetic normal access patterns
np.random.seed(42)
normal_logs = []
for _ in range(1000):
    # Features: user_id (0-9), zone_id (0-4), role_id (0-4), operation_id (0-9), hour (0-23)
    user = np.random.randint(0, 10)
    zone = np.random.randint(0, 5)
    role = np.random.randint(0, 5)
    op = np.random.randint(0, 10)
    hour = np.random.normal(14, 2)  # most access around 2 PM
    normal_logs.append([user, zone, role, op, hour])

normal_logs = np.array(normal_logs)

# Generate some anomalous logs (e.g., odd hours, rare user-zone combos)
anomalous_logs = []
for _ in range(20):
    user = np.random.randint(0, 10)
    zone = np.random.randint(0, 5)
    role = np.random.randint(0, 5)
    op = np.random.randint(0, 10)
    hour = np.random.uniform(0, 23)
    anomalous_logs.append([user, zone, role, op, hour])
anomalous_logs = np.array(anomalous_logs)

# Combine for training (normal only)
train_data = normal_logs

# Train detector
detector = AnomalyDetector(contamination=0.05)
detector.train(train_data)

# Score some samples
test_normal = normal_logs[:5]
test_anomalous = anomalous_logs[:5]

print("Normal sample scores (should be low):")
for sample in test_normal:
    score = detector.predict(sample.reshape(1, -1))
    print(f"  {sample} -> {score:.3f}")

print("\nAnomalous sample scores (should be higher):")
for sample in test_anomalous:
    score = detector.predict(sample.reshape(1, -1))
    print(f"  {sample} -> {score:.3f}")