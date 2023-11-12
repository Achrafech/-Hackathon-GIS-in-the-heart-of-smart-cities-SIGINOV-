from kafka import KafkaProducer, KafkaConsumer
import json
import threading
import requests
import time
import queue

# Kafka configuration
kafka_server = 'ec2-100-25-131-75.compute-1.amazonaws.com:9092'  # Replace with your EC2 Kafka server address
topic_name = 'road1-traffic-data'

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=kafka_server,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Initialize Kafka consumer in a function to avoid threading issues
def init_consumer():
    return KafkaConsumer(
        topic_name,
        group_id='road1-traffic-data-group',
        bootstrap_servers=kafka_server,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

# Function to fetch random traffic rate from an API
def get_random_traffic_rate(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else 0
        else:
            print(f"Warning: Error fetching data from API: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

# Function to calculate traffic jamming
def calculate_traffic_jam(inflow, outflow, road_capacity, initial_traffic, time_elapsed):
    current_traffic = initial_traffic + (inflow - outflow) * time_elapsed
    jamming = current_traffic / road_capacity
    return jamming

# Function to simulate sending traffic data
def send_traffic_data(road_id, api_url_inflow, api_url_outflow, initial_traffic, road_capacity):
    time_elapsed = 0
    while True:
        inflow_rate = get_random_traffic_rate(api_url_inflow)
        outflow_rate = get_random_traffic_rate(api_url_outflow)
        data = {
            'road_id': road_id,
            'inflow': inflow_rate,
            'outflow': outflow_rate,
            'initial_traffic': initial_traffic,
            'road_capacity': road_capacity,
            'time_elapsed': time_elapsed,
            'timestamp': time.time()
        }
        producer.send(topic_name, value=data)
        time_elapsed += 1/60
        time.sleep(5)

# Queue for thread-safe message handling
message_queue = queue.Queue()

# Function to consume and queue traffic data
def consume_and_queue_data():
    consumer = init_consumer()
    for message in consumer:
        message_queue.put(message.value)

# Function to write data to a JSON file
def write_to_json_file(data, filename="traffic_data.json"):
    with open(filename, "a") as file:
        json.dump(data, file)
        file.write("\n")

# Function to process queued traffic data
def process_queued_data():
    while True:
        try:
            data = message_queue.get()
            required_keys = ['inflow', 'outflow', 'road_capacity', 'initial_traffic', 'time_elapsed']
            if all(key in data for key in required_keys):
                traffic_jam = calculate_traffic_jam(data['inflow'], data['outflow'], data['road_capacity'], data['initial_traffic'], data['time_elapsed'])
                print(f"Road {data['road_id']} - Traffic Jam Ratio: {traffic_jam}")
                output_data = data.copy()
                output_data['traffic_jam_ratio'] = traffic_jam
                write_to_json_file(output_data)
            else:
                print("Warning: Some required keys are missing from the data.")
        except Exception as e:
            print(f"Error encountered: {e}")  # Or use 'pass' to ignore the error

# Example API endpoints for random numbers
API_URL_INFLOW = "http://www.randomnumberapi.com/api/v1.0/random?min=0&max=100&count=1"
API_URL_OUTFLOW = "http://www.randomnumberapi.com/api/v1.0/random?min=0&max=100&count=1"

# Start the producer thread
threading.Thread(target=send_traffic_data, args=('road1', API_URL_INFLOW, API_URL_OUTFLOW, 200, 500)).start()


    # Start the consumer thread
threading.Thread(target=consume_and_queue_data).start()

  # Start a few worker threads for processing
for _ in range(5):  # Adjust the number of threads as needed
      threading.Thread(target=process_queued_data).start()
