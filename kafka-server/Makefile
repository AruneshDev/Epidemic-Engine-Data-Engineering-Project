CONTAINER_CMD = docker

kafka-consumer:
	$(CONTAINER_CMD) build -t kafka-consumer -f Dockerfile.kafka_consumer .
#	$(CONTAINER_CMD) run -v ./kafka_consumer:/app -it kafka-consumer 
	$(CONTAINER_CMD) run -v .:/app -it kafka-consumer
	docker-compose up