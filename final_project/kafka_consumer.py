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

kafka_broker = "44.201.154.178:9092"
topic = "health_events"

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

kafka_df = spark.sql("SELECT * FROM health_events_stream")
print(kafka_df.show(5))

kafka_df_pd = kafka_df.toPandas()

# Load given 1m row dataset
# Define the URL of the CSV file
csv_url = "https://langdon.fedorapeople.org/1m_health_events_dataset.csv"
try:
    given_df = pd.read_csv(csv_url)
    print("Given 1m row dataset CSV file loaded successfully into DataFrame.")
    print(given_df.head())
except Exception as e:
    print(f"Error loading CSV file: {e}")

# Write both dataframes to postgres db
pg_user = "root"
pg_pass = "root"
pg_host = "db"
pg_port = 5432
pg_db = "health_events_db"

run_flag = False
while not run_flag:
    try:
        engine = create_engine(f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")
        con = engine.connect()
        print("Connection:", con, f"\nWriting tables to DB - {pg_db} now")
        run_flag = True
    except Exception as e:
        print("Exception in trying to connect to Postgres DB")
        print(str(e))
        print("Sleeping to retry again!")
        sleep(10)

try:
    kafka_df_pd.to_sql(name="health_events_kafka_stream", con=con, if_exists="replace", index=False)
    given_df.to_sql(name="health_events_given_data", con=con, if_exists="replace", index=False)
    print("Finished writing tables")
except Exception as e:
    print("Exception")
    print(str(e))