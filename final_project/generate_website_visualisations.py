from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from time import sleep
from pandas.plotting import table
import seaborn as sns

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
        print("Connection:", con, "\Loading tables from DB now")
        load_db_connection_flag = True
    except Exception as e:
        print("Exception when connecting to Load DB")
        print(str(e))
        print("Sleeping to retry again!")
        sleep(5)


load_table_flag = False
while not load_table_flag:
    try:
        kafka_df_pd = pd.read_sql_table("health_events_kafka_stream", con=con)
        given_df = pd.read_sql_table("health_events_given_data", con=con)
        kafka_df_predicted = pd.read_sql_table("health_events_kafka_stream_predicted_anomaly", con=con)
        print("Finished loading tables")
        load_table_flag = True
    except Exception as e:
        print("Exception when loading tables")
        print(str(e))
        print("Sleeping to retry again!")
        sleep(10)

print("Reading from generate_visualisations script:")
print("Kafka Stream Data:\n", kafka_df_pd.head())
print("Kafka Stream Data with Predicted Is_Anomaly:\n", kafka_df_predicted.head())
print("Given Data of 1m Rows:\n", given_df.head())

# Combine the Dataframes
# combined_df = given_df.append(kafka_df_pd, ignore_index=True)
combined_df = pd.concat([kafka_df_pd, given_df[['EventType', 'Timestamp', 'Location', 'Severity', 'Details', 'Is_Anomaly']]], ignore_index=True)
# Convert the "Timestamp" column to datetime format if it's not already in datetime format
combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'])
given_df['Timestamp'] = pd.to_datetime(given_df['Timestamp'])

# Plotting Kafka Data Stream
kafka_df_pd['Timestamp'] = pd.to_datetime(kafka_df_pd['Timestamp'])
kafka_df_pd = kafka_df_pd.sort_values(by='Timestamp', ascending=False)
# Get the latest rows
latest_10 = kafka_df_pd.head(5)
fig, ax = plt.subplots(figsize=(12, 6))
ax.axis('off')  # Remove the axes
tbl = table(ax, latest_10, loc='center', cellLoc='center')
plt.savefig('static_website/stream_data_latest_10_rows.png')



# Plotting the Most Prevelant Locations and EventTypes for given data
old_anomalies = given_df[given_df["Is_Anomaly"] == 1]
old_location_anomalies = old_anomalies.groupby("Location").size().sort_values(ascending=False)
old_event_type_anomalies = old_anomalies.groupby("EventType").size().sort_values(ascending=False)
old_location_colors = sns.color_palette("Blues", len(old_location_anomalies))
old_event_type_colors = sns.color_palette("Oranges", len(old_event_type_anomalies))
# Plot bar graph grouped by Location, sorted by count
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].bar(old_location_anomalies.index, old_location_anomalies.values, color=old_location_colors)
axes[0].set_title("Anomalies by Location on Given Data", fontsize=15)
axes[0].set_xlabel("Location", fontsize=12)
axes[0].set_ylabel("Count", fontsize=12)
# Plot bar graph grouped by EventType, sorted by count
axes[1].bar(old_event_type_anomalies.index, old_event_type_anomalies.values, color=old_event_type_colors)
axes[1].set_title("Anomalies by EventType on Given Data", fontsize=15)
axes[1].set_xlabel("EventType", fontsize=12)
axes[1].set_ylabel("Count", fontsize=12)
plt.tight_layout()
plt.savefig('static_website/given_data_visualisations.png')


# Plotting the Most Prevelant Locations and EventTypes for predicted anomalies
# anomalies = kafka_df_predicted[kafka_df_predicted["Is_Anomaly"] == 1]
# location_anomalies = anomalies.groupby("Location").size().sort_values(ascending=False)
# event_type_anomalies = anomalies.groupby("EventType").size().sort_values(ascending=False)
# location_colors = sns.color_palette("Blues", len(location_anomalies))
# event_type_colors = sns.color_palette("Oranges", len(event_type_anomalies))
# # Plot bar graph grouped by Location, sorted by count
# fig, axes = plt.subplots(1, 2, figsize=(14, 6))
# axes[0].bar(location_anomalies.index, location_anomalies.values, color=location_colors)
# axes[0].set_title("Anomalies by Location on Predicted Label", fontsize=15)
# axes[0].set_xlabel("Location", fontsize=12)
# axes[0].set_ylabel("Count", fontsize=12)
# # Plot bar graph grouped by EventType, sorted by count
# axes[1].bar(event_type_anomalies.index, event_type_anomalies.values, color=event_type_colors)
# axes[1].set_title("Anomalies by EventType on Predicted Label", fontsize=15)
# axes[1].set_xlabel("EventType", fontsize=12)
# axes[1].set_ylabel("Count", fontsize=12)
# plt.tight_layout()


location_grouped = kafka_df_predicted.groupby(["Location", "Is_Anomaly"]).size().unstack(fill_value=0)
event_type_grouped = kafka_df_predicted.groupby(["EventType", "Is_Anomaly"]).size().unstack(fill_value=0)
sns.set_palette("Set2", 2)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
location_grouped.plot(kind='bar', stacked=True, ax=axes[0], colormap='coolwarm')
axes[0].set_title("Anomalies vs. Non-Anomalies by Location", fontsize=15)
axes[0].set_xlabel("Location", fontsize=12)
axes[0].set_ylabel("Count", fontsize=12)
axes[0].legend(["Non-Anomaly", "Anomaly"])
event_type_grouped.plot(kind='bar', stacked=True, ax=axes[1], colormap='coolwarm')
axes[1].set_title("Anomalies vs. Non-Anomalies by EventType", fontsize=15)
axes[1].set_xlabel("EventType", fontsize=12)
axes[1].set_ylabel("Count", fontsize=12)
axes[1].legend(["Non-Anomaly", "Anomaly"])

plt.savefig('static_website/predicted_data_visualisations.png')



# # Filter dataframe for anomalies
# anomalies_df = given_df[given_df['Is_Anomaly'] == 1]
# anomalies_df['Timestamp'] = pd.to_datetime(anomalies_df['Timestamp'])
# # Plotting previous Anomalies
# sns.set_theme(style="whitegrid")
# plt.figure(figsize=(10, 6))
# sns.countplot(data=anomalies_df, x='EventType')
# plt.title('Anomaly Count per EventType')
# plt.xlabel('Event Type')
# plt.ylabel('Count')
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.savefig('static_website/anomaly_event_type_count.png')


# Event Severity Distribution Pie Chart
severity_counts = combined_df['Severity'].value_counts()
plt.figure(figsize=(8, 6))
plt.pie(severity_counts, labels=severity_counts.index, autopct='%1.1f%%', startangle=140)
plt.title('Event Severity Distribution')
plt.savefig('static_website/graph_Severity_Distribution.png')


# Event Frequency Over Time Plot
# Create a temporary DataFrame with the "Timestamp" column as the index for plotting
temp_df = given_df.set_index('Timestamp')
# Resample the data to get the event frequency over time (e.g., per day, per hour, etc.) Here, we're resampling to get the event frequency per day ('D' for daily frequency)
event_frequency = temp_df.resample('D').size()
plt.figure(figsize=(10, 6))
event_frequency.plot()
plt.title('Event Frequency Over Time')
plt.xlabel('Date')
plt.ylabel('Event Frequency')
plt.savefig('static_website/graph_Event_Frequency_Over_Time.png')


# Distribution of Severity of Event Types by Time of Day Heatmap
given_df['Hour'] = given_df['Timestamp'].dt.hour
severity_distribution = given_df.groupby(['Hour', 'Severity']).size().reset_index(name='Count')
pivot_table = severity_distribution.pivot(index='Severity', columns='Hour', values='Count')
plt.figure(figsize=(10, 6))
plt.imshow(pivot_table, cmap='YlGnBu', interpolation='nearest')
plt.xlabel('Time of Day (Hour)')
plt.ylabel('Severity')
plt.title('Distribution of Severity of Event Types by Time of Day')
plt.colorbar(label='Count')
plt.xticks(range(len(pivot_table.columns)), pivot_table.columns)
plt.yticks(range(len(pivot_table.index)), pivot_table.index)
plt.savefig('static_website/graph_Distribution_of_Severity_of_Event_Types_by_Time_of_Day.png')






