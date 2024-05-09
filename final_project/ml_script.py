from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from time import sleep
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

load_table_flag = False
while not load_table_flag:
    try:
        kafka_df_pd = pd.read_sql_table("health_events_kafka_stream", con=con)
        given_df = pd.read_sql_table("health_events_given_data", con=con)
        print("Finished loading tables")
        load_table_flag = True
    except Exception as e:
        print("Exception when loading tables")
        print(str(e))
        print("Sleeping to retry again!")
        sleep(10)

print("Reading from ml script:")
print("Kafka Stream Data:\n", kafka_df_pd.head())
print("Given Data of 1m Rows:\n", given_df.head())

# Convert Timestamp to datetime and create new features
given_df['Timestamp'] = pd.to_datetime(given_df['Timestamp'])
given_df['Hour'] = given_df['Timestamp'].dt.hour
given_df['DayOfWeek'] = given_df['Timestamp'].dt.dayofweek + 1
given_df['DayOfMonth'] = given_df['Timestamp'].dt.day
given_df['Month'] = given_df['Timestamp'].dt.month
given_df['Year'] = given_df['Timestamp'].dt.year
given_df['TimestampUnix'] = given_df['Timestamp'].astype(int) // 10**9

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

# Define feature columns and the target
feature_columns = ["EventTypeIndex", "LocationIndex", "SeverityIndex", "Hour", "DayOfWeek", "DayOfMonth", "Month", "Year", "TimestampUnix"]
X = given_df[feature_columns]
y = given_df["Is_Anomaly"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define RandomForestClassifier and GridSearchCV
classifier = RandomForestClassifier(random_state=42, n_jobs=-1)
param_grid = {'max_depth': [5], 'n_estimators': [100]}

grid_search = GridSearchCV(estimator=classifier, param_grid=param_grid, cv=5, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train)

# Save the trained model
joblib.dump(grid_search, 'ml_model/model.pkl')

# Predict on the test set
y_pred = grid_search.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy On Test Set: {accuracy * 100:.2f}%")
f1 = f1_score(y_test, y_pred)
print(f"Model F1 Score: {f1:.2f}")

# Create confusion matrix
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix: Test Predictions')
plt.savefig('static_website/ml_test_confusion_matrix.png')

# Encode Kafka stream data and make predictions
kafka_df_pd['Timestamp'] = pd.to_datetime(kafka_df_pd['Timestamp'])
kafka_df_pd['Hour'] = kafka_df_pd['Timestamp'].dt.hour
kafka_df_pd['DayOfWeek'] = kafka_df_pd['Timestamp'].dt.dayofweek + 1
kafka_df_pd['DayOfMonth'] = kafka_df_pd['Timestamp'].dt.day
kafka_df_pd['Month'] = kafka_df_pd['Timestamp'].dt.month
kafka_df_pd['Year'] = kafka_df_pd['Timestamp'].dt.year
kafka_df_pd['TimestampUnix'] = kafka_df_pd['Timestamp'].astype(int) // 10**9

# Encode categorical columns while handling unseen labels
for column in ['EventType', 'Location', 'Severity']:
    if column in label_encoders:  # Use existing encoders
        le = label_encoders[column]
        kafka_df_pd[column + 'Index'] = transform_with_unseen_handling(le, kafka_df_pd[column])
    else:
        raise ValueError(f"No LabelEncoder found for column: {column}")

X_kafka = kafka_df_pd[feature_columns]
kafka_df_pd['Is_Anomaly'] = grid_search.predict(X_kafka)

print('Predicted DF:')
print(kafka_df_pd[['EventType', 'Location', 'Severity', 'Details', 'Is_Anomaly']])


# Write Predicted Label kafka stream DF to Postgres
print("Writing the predicted label DF now to Postgres in table \"health_events_kafka_stream_predicted_anomaly\"")
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
    kafka_df_pd[['EventType', 'Location', 'Severity', 'Details', 'Is_Anomaly']].to_sql(name="health_events_kafka_stream_predicted_anomaly", con=con, if_exists="replace", index=False)
    print("Finished writing tables")
except Exception as e:
    print("Exception")
    print(str(e))






