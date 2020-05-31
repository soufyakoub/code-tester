import logging
from typing import Union

from pika import ConnectionParameters, SelectConnection
from pika.adapters import IOLoop
from pika.channel import Channel
from pika.spec import Basic, Queue

LOGGER = logging.getLogger()


class Consumer:
    """
    A consumer class that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, the consumer will stop and indicate
    that reconnection is needed (you should check the `should_reconnect` property).

    NOTE : The default exchange is used.
    """
    ioloop: Union[IOLoop, None]
    connection: Union[SelectConnection, None]
    channel: Union[Channel, None]
    should_reconnect: bool

    def __init__(self, host: str, queue: str, prefetch_value: int, on_message: callable):
        # state
        self.should_reconnect = False
        self._closing = False
        self._consuming = False

        # rabbitmq parameters
        self._host = str(host)
        self._queue = str(queue)
        self._prefetch_count = int(prefetch_value)
        self._on_message = on_message
        self._consumer_tag = None

        # objects
        self.ioloop = None
        self.connection = None
        self.channel = None

    def _on_connection_open(self, connection: SelectConnection):
        """Called once the connection to RabbitMQ has been established."""
        LOGGER.info("Connection opened")
        LOGGER.info("Creating a new channel ...")
        connection.channel(on_open_callback=self._on_channel_open)

    def _on_connection_open_error(self, connection: SelectConnection, err: Exception):
        """Called if the connection to RabbitMQ can't be established."""
        LOGGER.error(f"Connection open failed : {err}")
        self.should_reconnect = True
        self.stop()

    def _on_connection_closed(self, connection: SelectConnection, reason: Exception):
        """Called when the connection to RabbitMQ is closed unexpectedly."""
        self.channel = None

        if self._closing:
            self.ioloop.stop()
        else:
            LOGGER.warning(f"Connection closed : {reason}")
            self.should_reconnect = True
            self.stop()

    def _on_channel_open(self, channel: Channel):
        """Called when the channel has been opened."""
        LOGGER.info("Channel opened")
        self.channel = channel
        channel.add_on_close_callback(self._on_channel_closed)

        LOGGER.info(f'Declaring queue "{self._queue}" ...')
        channel.queue_declare(queue=self._queue, callback=self._on_queue_declare_ok)

    def _on_channel_closed(self, channel: Channel, reason: Exception):
        """
        Called when RabbitMQ unexpectedly closes the channel.

        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters.
        """
        LOGGER.warning(f"Channel was closed {channel} : {reason}")
        self._consuming = False

        if self.connection.is_closing or self.connection.is_closed:
            LOGGER.info("Connection is closing or already closed")
        else:
            LOGGER.info("Closing connection ...")
            self.connection.close()

    def _on_queue_declare_ok(self, method: Queue.DeclareOk):
        """Called when the Queue.Declare RPC call has completed."""
        self.channel.basic_qos(prefetch_count=self._prefetch_count, callback=self._on_basic_qos_ok)

    def _on_basic_qos_ok(self, method: Basic.QosOk):
        """Called when the Queue.Declare RPC call has completed."""
        LOGGER.info(f"QOS set to : {self._prefetch_count}")
        self.channel.add_on_cancel_callback(self._on_consumer_cancelled)

        LOGGER.info("Issuing consumer related RPC commands")
        # used to uniquely identify the consumer with RabbitMQ.
        # We keep the value to use it when we want to cancel consuming.
        self._consumer_tag = self.channel.basic_consume(self._queue, self._on_message)

        LOGGER.info("!!! Waiting for messages !!!")
        self._consuming = True

    def _on_consumer_cancelled(self, method: Basic.Cancel):
        """Called when RabbitMQ sends a Basic.Cancel for a consumer receiving messages."""
        LOGGER.info(f"Consumer was cancelled remotely, shutting down : {method}")
        if self.channel:
            self.channel.close()

    def _on_consumer_cancel_ok(self, method: Basic.CancelOk):
        """Called when RabbitMQ acknowledges the cancellation of a consumer."""
        LOGGER.info("RabbitMQ acknowledged the cancellation")
        self._consuming = False

        LOGGER.info("Closing the channel ...")
        self.channel.close()

    def start(self):
        """connect to RabbitMQ and then start the IOLoop."""
        try:
            LOGGER.info(f'Connecting to the host "{self._host}" ...')
            self.connection = SelectConnection(
                parameters=ConnectionParameters(self._host),
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed,
            )

            # noinspection PyTypeChecker
            self.ioloop = self.connection.ioloop

            # This is a blocking method
            self.ioloop.start()

        except:
            self.stop()

    def stop(self):
        """Gracefully shutdown the connection."""
        if self._closing:
            return

        LOGGER.info("Stopping ...")
        self._closing = True

        if not self._consuming:

            self.ioloop.stop()

        elif self.channel:

            LOGGER.info(f"Sending a Basic.Cancel RPC command to RabbitMQ from the consumer # {self._consumer_tag}")
            self.channel.basic_cancel(self._consumer_tag, self._on_consumer_cancel_ok)

            # When a KeyboardInterrupt exception is raised the IOLoop stops.
            # It needs to be running for pika to communicate with RabbitMQ.
            # Commands issued prior to restarting it will be buffered but not processed.
            self.ioloop.start()

        LOGGER.info("Stopped gracefully")
        self._closing = False
