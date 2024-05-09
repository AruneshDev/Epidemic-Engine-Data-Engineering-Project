import os
default_kafka_broker = "44.201.154.178:9092"
default_topic = "health_events"
# Retrieve the environment variables
kafka_broker = os.getenv('kafka_producer_ip', default_kafka_broker)
topic = os.getenv('kafka_producer_topic', default_topic)
print("Making Predictions From Following Kafka Broker:")
print("Kafka Broker:", kafka_broker)
print("Topic:", topic)


import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, date_format, sum, count, date_trunc
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql import functions as F
import time
from sqlalchemy import create_engine
from time import sleep

spark = SparkSession.builder \
    .appName("KafkaDataSparkAnalysis") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0") \
    .getOrCreate()
kafka_source = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", topic) \
    .option("startingOffsets", "earliest") \
    .load()
defined_schema = StructType([
    StructField("EventType", StringType()),
    StructField("Timestamp", TimestampType()),
    StructField("Location", StringType()),
    StructField("Severity", StringType()),
    StructField("Details", StringType())
])
kafka_stream = kafka_source.selectExpr("CAST(value AS STRING)")  
kafka_stream = kafka_stream.select(from_json("value", defined_schema).alias("data")).select("data.*")
kafka_stream

query = kafka_stream \
    .writeStream \
    .outputMode("append") \
    .format("memory") \
    .queryName("health_events_stream") \
    .start()

# Wait for the stream to finish
# query.awaitTermination()
# Wait to collect all data then stop instead of waiting forever
time.sleep(30)
query.stop()

input_kafka_df = spark.sql("SELECT * FROM health_events_stream")
input_kafka_df = input_kafka_df.toPandas()
print("Given Input Data:\n", input_kafka_df.head())


from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, ConfusionMatrixDisplay
import joblib

from sqlalchemy import create_engine

# Loading data from postgres db to get untransformed data
pg_user = "root"
pg_pass = "root"
pg_host = "db"
pg_port = 5432
pg_db = "health_events_db"

load_db_connection_flag = False
while not load_db_connection_flag:
    try:
        engine = create_engine(f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")
        con = engine.connect()
        print("Connection:", con, "\nLoading tables from DB now")
        load_db_connection_flag = True
    except Exception as e:
        print("Exception when connecting to Load DB")
        print(str(e))
        print("Sleeping to retry again!")
        sleep(5)
given_df = pd.read_sql_table("health_events_given_data", con=con)

feature_columns = ["EventTypeIndex", "LocationIndex", "SeverityIndex", "Hour", "DayOfWeek", "DayOfMonth", "Month", "Year", "TimestampUnix"]
# Use LabelEncoder to encode the categorical features
label_encoders = {}

for column in ['EventType', 'Location', 'Severity']:
    le = LabelEncoder()
    given_df[column + 'Index'] = le.fit_transform(given_df[column])
    label_encoders[column] = le

# Function to transform and handle unseen labels
def transform_with_unseen_handling(le, data):
    unique_classes = set(le.classes_)
    return data.apply(lambda x: le.transform([x])[0] if x in unique_classes else -1)



# Do Feature Engineering on Input Data for ML Model prediction
input_kafka_df['Timestamp'] = pd.to_datetime(input_kafka_df['Timestamp'])
input_kafka_df['Hour'] = input_kafka_df['Timestamp'].dt.hour
input_kafka_df['DayOfWeek'] = input_kafka_df['Timestamp'].dt.dayofweek + 1
input_kafka_df['DayOfMonth'] = input_kafka_df['Timestamp'].dt.day
input_kafka_df['Month'] = input_kafka_df['Timestamp'].dt.month
input_kafka_df['Year'] = input_kafka_df['Timestamp'].dt.year
input_kafka_df['TimestampUnix'] = input_kafka_df['Timestamp'].astype(int) // 10**9

# Encode categorical columns while handling unseen labels
for column in ['EventType', 'Location', 'Severity']:
    if column in label_encoders:  # Use existing encoders
        le = label_encoders[column]
        input_kafka_df[column + 'Index'] = transform_with_unseen_handling(le, input_kafka_df[column])
    else:
        raise ValueError(f"No LabelEncoder found for column: {column}")

# Load Model saved in the same folder
model = joblib.load('model.pkl')

input_kafka_df['Is_Anomaly'] = model.predict(input_kafka_df[feature_columns])

print('Input DF with Predicted Anomalies (Omitting Feature Engineered Columns):')
print(input_kafka_df[['EventType', 'Location', 'Severity', 'Details', 'Is_Anomaly']])

try:
    input_kafka_df[['EventType', 'Location', 'Severity', 'Details', 'Is_Anomaly']].to_sql(name="input_kafka_data_with_predicted_anomaly", con=con, if_exists="replace", index=False)
    print("Finished writing tables")
except Exception as e:
    print("Exception")
    print(str(e))

