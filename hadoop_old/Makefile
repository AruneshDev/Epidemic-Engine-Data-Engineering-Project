# DOCKER_NETWORK = word_count_python_default
DOCKER_NETWORK = hadoop_default
ENV_FILE = hadoop.env
current_branch := 2.0.0-hadoop3.2.1-java8
CONTAINER_CMD = docker
RUN_PARAMS = --network ${DOCKER_NETWORK} --env-file ${ENV_FILE} bde2020/hadoop-base:$(current_branch)


wordcount-python:
#	chmod a+x ./add-python.sh
	chmod a+x ./*
	$(CONTAINER_CMD) build -t hadoop-wordcount-python ./word_count_python
	./add-python.sh
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /output || : #ignore doesn't exist
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /input  || : #ignore doesn't exist
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -mkdir -p /input/
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -mkdir -p /output/
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -mkdir -p /output/output_event_location/
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -mkdir -p /output/output_event_type/
#	MSYS_NO_PATHCONV=1 docker run --volume //c/Users/sriha/Downloads/epidemic-engine-project-harshahrishavarunesh/hadoop:/app --network hadoop_default --env-file hadoop.env bde2020/hadoop-base:2.0.0-hadoop3.2.1-java8 hadoop fs -copyFromLocal /app/simulated_health_events.csv /input/
#	$(CONTAINER_CMD) run --volume ./:/app $(RUN_PARAMS) hadoop fs -copyFromLocal /app/simulated_health_events.csv /input/
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -copyFromLocal -f /opt/hadoop-3.2.1/README.txt /input/
	$(CONTAINER_CMD) run --network ${DOCKER_NETWORK} --env-file ${ENV_FILE} hadoop-wordcount-python
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -cat /output/*
#	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /output
#	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /input

event-counter: ;
	$(CONTAINER_CMD) build -t hadoop-eventcount ./event_count_by_location_python
	$(CONTAINER_CMD) run --network ${DOCKER_NETWORK} --env-file ${ENV_FILE} hadoop-eventcount
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -cat /output/output_event_type/*

location-mapreducer: ;
	$(CONTAINER_CMD) build -t hadoop-locationcount ./event_count_by_type_python
	$(CONTAINER_CMD) run --network ${DOCKER_NETWORK} --env-file ${ENV_FILE} hadoop-locationcount
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -cat /output/output_event_location/*

hadoop_solved: wordcount-python event-counter location-mapreducer
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /output
	$(CONTAINER_CMD) run $(RUN_PARAMS) hadoop fs -rm -r /input