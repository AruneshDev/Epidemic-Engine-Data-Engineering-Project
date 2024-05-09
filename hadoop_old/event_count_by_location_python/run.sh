#!/bin/bash

# Define paths for mapper, reducer, and input
MAPPER="mapper.py"
REDUCER="reducer.py"
INPUT="/input/simulated_health_events.csv" # Adjust this path as necessary
OUTPUT="/output/output_event_location" # Define the HDFS output directory

echo "Attempting to run Hadoop Streaming job..."

hadoop jar /opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar \
    -file /app/$MAPPER -mapper $MAPPER \
    -file /app/$REDUCER -reducer $REDUCER \
    -input $INPUT -output $OUTPUT

echo "Job Completed."

# echo Attempting to run (no hadoop test):
# echo "cat $INPUT | ./$MAPPER | sort | ./$REDUCER > ./output"

# cat $INPUT | ./$MAPPER | sort | ./$REDUCER > ./local-output-reduced
# hadoop fs -rm -r /local-output-reduced || :
# hadoop fs -put ./local-output-reduced /local-output-reduced

# echo Completed