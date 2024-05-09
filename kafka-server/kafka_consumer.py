import csv
import json
from confluent_kafka import Consumer, KafkaError

# Kafka broker address and topic
bootstrap_servers = '44.201.154.178:9092'
topic = 'health_events'

# CSV file configuration
csv_file_path = '/app/health_events.csv'
csv_fieldnames = ['EventType', 'Timestamp', 'Location', 'Severity', 'Details']  # CSV column names

# Consumer configuration
consumer_config = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': 'health_event_consumer_group',  # Specify a consumer group ID
    'auto.offset.reset': 'earliest',  # Start consuming from the beginning of the topic
}

# Create Kafka consumer
consumer = Consumer(consumer_config)

# Subscribe to the topic
consumer.subscribe([topic])

try:
    with open(csv_file_path, 'a', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fieldnames)
        # Write CSV header if the file is empty
        if csv_file.tell() == 0:
            csv_writer.writeheader()

        while True:
            # Poll for messages
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition
                    print('%% %s [%d] reached end at offset %d\n' %
                          (message.topic(), message.partition(), message.offset()))
                elif message.error():
                    # Error
                    print('Error: %s' % message.error())
                    break
            else:
                # Process the received message
                decoded_message = message.value().decode('utf-8')
                parsed_message = json.loads(decoded_message)  # Parse JSON message
                csv_writer.writerow(parsed_message)
                print('Received message:', parsed_message)

except KeyboardInterrupt:
    pass

finally:
    # Close the consumer
    consumer.close()
