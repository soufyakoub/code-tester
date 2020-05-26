import logging
import signal
from errno import ECONNABORTED
from os import environ

from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from consumer import Consumer

logging.basicConfig(format=environ["LOG_FORMAT"], level=environ["LOGGER_LEVEL"].upper())
LOGGER = logging.getLogger()

# Handle SIGTERM and SIGQUIT the same way SIGINT is handled
signal.signal(signal.SIGTERM, signal.default_int_handler)
signal.signal(signal.SIGQUIT, signal.default_int_handler)


def on_message(channel: Channel, method: Basic.Deliver, props: BasicProperties, body: bytes):
    """Called when a message is delivered from RabbitMQ."""
    LOGGER.info(f"Received message # {method.delivery_tag} from {props.app_id}")

    LOGGER.info(f"Acknowledging message # {method.delivery_tag}")
    channel.basic_ack(method.delivery_tag)


consumer = Consumer(
    host=environ["RABBITMQ_HOST"],
    queue=environ["TASKS_QUEUE_NAME"],
    prefetch_value=int(environ["PREFETCH_VALUE"]),
    on_message=on_message,
)

# This is a blocking method
consumer.start()

if consumer.should_reconnect:
    # Raise error to make the service container exit with a non-zero code
    raise ConnectionAbortedError(ECONNABORTED, "Service should be restarted")
