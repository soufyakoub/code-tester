"""
This is a consumer module that will handle unexpected interactions
with RabbitMQ such as channel and connection closures.

If RabbitMQ closes the connection, the consumer will stop and indicate
that reconnection is necessary (you should check the `should_reconnect` property).

NOTE : The default exchange is used
"""

import logging

import pika
from pika.channel import Channel
from pika.connection import Connection
from pika.spec import Basic, Queue

LOGGER = logging.getLogger()

# state
should_reconnect = False
_closing = False
_consuming = False

# rabbitmq parameters
_connection: Connection
_channel: Channel
_consumer_tag: str
_queue: str
_prefetch_count: int
_on_message: callable


def _on_connection_open(connection: Connection):
    """Called once the connection to RabbitMQ has been established."""
    LOGGER.info("Connection opened")
    LOGGER.info("Creating a new channel ...")
    connection.channel(on_open_callback=_on_channel_open)


def _on_connection_open_error(connection: Connection, err: Exception):
    """Called if the connection to RabbitMQ can't be established."""
    global should_reconnect

    LOGGER.error(f"Connection open failed : {err}")
    should_reconnect = True
    stop()


def _on_connection_closed(connection: Connection, reason: Exception):
    """Called when the connection to RabbitMQ is closed unexpectedly."""
    global _channel, should_reconnect

    _channel = None

    if _closing:
        connection.ioloop.stop()
    else:
        LOGGER.warning(f"Connection closed : {reason}")
        should_reconnect = True
        stop()


def _on_channel_open(channel: Channel):
    """Called when the channel has been opened."""
    global _channel

    LOGGER.info("Channel opened")
    _channel = channel
    channel.add_on_close_callback(_on_channel_closed)

    LOGGER.info(f'Declaring queue "{_queue}" ...')
    channel.queue_declare(queue=_queue, callback=_on_queue_declare_ok)


def _on_channel_closed(channel: Channel, reason: Exception):
    """
    Called when RabbitMQ unexpectedly closes the channel.

    Channels are usually closed if you attempt to do something that
    violates the protocol, such as re-declare an exchange or queue with
    different parameters.
    """
    global _consuming

    LOGGER.warning(f"Channel was closed {channel} : {reason}")
    _consuming = False

    connection = channel.connection

    if connection.is_closing or connection.is_closed:
        LOGGER.info("Connection is closing or already closed")
    else:
        LOGGER.info("Closing connection ...")
        connection.close()


def _on_queue_declare_ok(method: Queue.DeclareOk):
    """Called when the Queue.Declare RPC call has completed."""
    _channel.basic_qos(prefetch_count=_prefetch_count, callback=_on_basic_qos_ok)


def _on_basic_qos_ok(method: Basic.QosOk):
    """Called when the Queue.Declare RPC call has completed.."""
    global _consumer_tag, _consuming

    LOGGER.info(f"QOS set to : {_prefetch_count}")
    _channel.add_on_cancel_callback(_on_consumer_cancelled)

    LOGGER.info("Issuing consumer related RPC commands")
    # used to uniquely identify the consumer with RabbitMQ.
    # We keep the value to use it when we want to cancel consuming.
    _consumer_tag = _channel.basic_consume(_queue, _on_message)

    LOGGER.info("!!! Waiting for messages !!!")
    _consuming = True


def _on_consumer_cancelled(method: Basic.CancelOk):
    """Called when RabbitMQ sends a Basic.Cancel for a consumer receiving messages."""
    LOGGER.info(f"Consumer was cancelled remotely, shutting down : {method}")
    if _channel:
        _channel.close()


def _on_cancel_ok(method: Basic.CancelOk):
    """Called when RabbitMQ acknowledges the cancellation of a consumer."""
    global _consuming

    LOGGER.info("RabbitMQ acknowledged the cancellation")
    _consuming = False

    LOGGER.info("Closing the channel ...")
    _channel.close()


def start(host: str, queue: str, prefetch_value: int, on_message: callable):
    """connect to RabbitMQ and then start the IOLoop."""
    global _queue, _prefetch_count, _on_message, _connection

    host = str(host)
    _queue = str(queue)
    _prefetch_count = int(prefetch_value)
    _on_message = on_message

    try:
        LOGGER.info(f"Connecting to {host} ...")
        _connection = pika.SelectConnection(
            parameters=pika.ConnectionParameters(host),
            on_open_callback=_on_connection_open,
            on_open_error_callback=_on_connection_open_error,
            on_close_callback=_on_connection_closed,
        )

        _connection.ioloop.start()

    finally:
        stop()


def stop():
    """Gracefully shutdown the connection."""
    global _closing, _consumer_tag

    if _closing:
        return

    LOGGER.info("Stopping ...")
    _closing = True

    if not _consuming:

        _connection.ioloop.stop()

    elif _channel:

        LOGGER.info(f"Sending a Basic.Cancel RPC command to RabbitMQ from the consumer # {_consumer_tag}")
        _channel.basic_cancel(_consumer_tag, _on_cancel_ok)

        # we need to start the IOLoop again because this method is invoked
        # when CTRL-C is pressed, raising a KeyboardInterrupt exception. This
        # exception stops the IOLoop which needs to be running for pika to
        # communicate with RabbitMQ. All of the commands issued prior to starting
        # the IOLoop will be buffered but not processed.
        _connection.ioloop.start()

    LOGGER.info("Stopped gracefully")
