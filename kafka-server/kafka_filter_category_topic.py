import csv
import sys
from confluent_kafka import Producer

def delivery_report(err, msg):
    """Delivery report callback called on successful or failed message delivery."""
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def produce_events(csv_file, category, topic):
    producer = Producer({'bootstrap.servers': 'kafka:9092'})

    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row[category] == topic:
                # Produce message to topic
                print("Kafka Producer Broadcasting Maessage:", row)
                producer.produce(topic=topic, value=str(row), callback=delivery_report)
                producer.flush()  # Ensure message delivery

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python produce_events.py <category> <topic>")
        sys.exit(1)

    csv_file = 'health_events.csv'
    category = sys.argv[1]
    topic = sys.argv[2]

    produce_events(csv_file, category, topic)


# import csv
# import sys

# def filter_events(csv_file, category, topic):
#     with open(csv_file, newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             if row[category] == topic:
#                 print(row)

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Invalid Arguments!\nUsage: python kafka_filter_category_topic.py <category> <topic>")
#         sys.exit(1)

#     csv_file = 'health_events.csv'
#     category = sys.argv[1]
#     topic = sys.argv[2]

#     filter_events(csv_file, category, topic)
