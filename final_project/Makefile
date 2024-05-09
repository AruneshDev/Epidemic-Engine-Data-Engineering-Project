CONTAINER_CMD = docker
COMPOSE_CMD = docker-compose
PYTHON_CMD = python3

# Define your kafka broker IP and topic for test predictions, adding default topic and IP for example
# KAFKA_BROKER_IP = 44.201.154.178:9092
# KAFKA_TOPIC = health_events

# Targets
.PHONY: final_project down ml_predict_kafka setup_env test

final_project:
	$(COMPOSE_CMD) up

down:
	$(COMPOSE_CMD) down

ml_predict_kafka:
#	kafka_producer_ip=$(KAFKA_BROKER_IP) default_topic=$(KAFKA_TOPIC) $(COMPOSE_CMD) -f ml_model/docker-compose-ml-predict.yml up
	$(COMPOSE_CMD) -f ml_model/docker-compose-ml-predict.yml up

setup_env:
	$(COMPOSE_CMD) up

test: setup_env
	$(PYTHON_CMD) -m pytest -v --disable-warnings pytest_script.py
	$(MAKE) down
