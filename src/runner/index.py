import logging
import signal
from errno import ECONNABORTED
from os import getenv

from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from consumer import Consumer

logging.basicConfig(
    format=getenv("LOG_FORMAT", "%(asctime)s - [%(levelname)s] : %(message)s"),
    level=getenv("LOGGER_LEVEL", "INFO").upper(),
)

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
    host=getenv("RABBITMQ_HOST", "rabbitmq"),
    queue=getenv("TASKS_QUEUE_NAME", "tasks"),
    prefetch_value=getenv("PREFETCH_VALUE", 1),
    on_message=on_message,
)

# This is a blocking method
consumer.start()

if consumer.should_reconnect:
    # Raise error to make the service container exit with a non-zero code
    raise ConnectionAbortedError(ECONNABORTED, "Service should be restarted")
