import subprocess
import requests
import pytest
import time

# Constants
POSTGRES_PORT = 5432
KAFKA_PORT = 9092
NGINX_PORT = 80

@pytest.fixture(scope="module", autouse=True)
def setup_docker_environment():
    """Start the Docker Compose environment for testing."""
    print("\nStarting Docker Compose environment...")
    subprocess.run(["docker-compose", "up", "-d"])
    print("Waiting for services to initialize...")
    # Allow some time for services to be up and healthy
    time.sleep(10)
    yield
    print("\nShutting down Docker Compose environment...")
    subprocess.run(["docker-compose", "down"])

def test_postgres_healthy():
    """Check if PostgreSQL is up and running on the defined port."""
    print("\nRunning health check for PostgreSQL...")
    result = subprocess.run(
        ["docker-compose", "exec", "-T", "db", "pg_isready", "-U", "root", "-p", str(POSTGRES_PORT)],
        capture_output=True,
        text=True
    )
    if "accepting connections" in result.stdout:
        print("Postgres is healthy and accepting connections.")
    else:
        print(f"Postgres health check failed: {result.stderr}")
    assert "accepting connections" in result.stdout, f"Postgres health check failed: {result.stderr}"

def test_kafka_healthy():
    """Check if Kafka broker is listening on the expected port."""
    print("\nRunning health check for Kafka...")
    result = subprocess.run(
        ["docker-compose", "exec", "-T", "kafka", "bash", "-c", "cat < /dev/null > /dev/tcp/localhost/9092"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Kafka is healthy and broker is accessible.")
    else:
        print("Kafka health check failed.")
    assert result.returncode == 0, "Kafka health check failed"

def test_nginx_healthy():
    """Check if the Nginx server is up and responding correctly."""
    print("\nRunning health check for Nginx...")
    response = requests.get(f"http://localhost:{NGINX_PORT}")
    if response.status_code == 200:
        print("Nginx is healthy and responding with status code 200.")
    else:
        print(f"Nginx health check failed with status code: {response.status_code}")
    assert response.status_code == 200, "Nginx health check failed"
