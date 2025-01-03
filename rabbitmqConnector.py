import pika
import os
import configparser

config_path = os.path.join(os.path.dirname(__file__), './config.cfg')
config = configparser.ConfigParser()
config.sections()
config.read(config_path)

HOST = config['rabbitmq']['host']
USERNAME = config['rabbitmq']['username']
PASSWORD = config['rabbitmq']['password']

def connect():
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=HOST, credentials=credentials, heartbeat=600, blocked_connection_timeout=300)
    )

    channel = connection.channel()

    return channel, connection
