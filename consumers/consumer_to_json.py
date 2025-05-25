from kafka import KafkaConsumer
import json
import os
from datetime import datetime

# Configuration
KAFKA_SERVER = 'localhost:9093'
TOPICS = ['all-matches', 'live-matches']
OUTPUT_DIR = 'kafka_data'

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Kafka consumer
consumer = KafkaConsumer(
    *TOPICS,
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='json-storage-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# Open file handles for each topic
file_handles = {
    topic: open(os.path.join(OUTPUT_DIR, f"{topic.replace('-', '_')}_data.json"), "a", encoding="utf-8")
    for topic in TOPICS
}

print("Listening for messages... Press Ctrl+C to stop.")

try:
    for message in consumer:
        topic = message.topic
        data = message.value

        json.dump(data, file_handles[topic])
        file_handles[topic].write("\n")  # Write each record on a new line
        file_handles[topic].flush()

        print(f"[{datetime.now()}] Stored message from topic: {topic}")
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    for f in file_handles.values():
        f.close()
    consumer.close()
