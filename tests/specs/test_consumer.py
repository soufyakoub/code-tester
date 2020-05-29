import signal

import pytest
from pytest_docker_tools.wrappers import Container

from tests.helpers import set_up_consumer


def test_normal_workflow(rabbitmq: Container, monkeypatch):
    message_body = None

    def on_message(channel, method, props, body):
        nonlocal message_body
        message_body = body

        # Simulate a KeyboardInterrupt which should make the consumer stop gracefully
        signal.raise_signal(signal.SIGINT)

    def on_basic_qos_ok(consumer):
        consumer.channel.basic_publish("", "tasks", body=b"some message")

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
        on_message=on_message,
    )

    assert message_body == b"some message"
    assert consumer.should_reconnect is False


def test_stop_gracefully(rabbitmq: Container, monkeypatch):
    def on_basic_qos_ok(consumer):
        consumer.stop()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
    )

    assert consumer.should_reconnect is False


def test_close_connection(rabbitmq: Container, monkeypatch):
    def on_basic_qos_ok(consumer):
        consumer.connection.close()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
    )

    assert consumer.should_reconnect is True


def test_close_channel(rabbitmq: Container, monkeypatch):
    def on_basic_qos_ok(consumer):
        consumer.channel.close()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
    )

    assert consumer.should_reconnect is True


def test_on_message_exception(rabbitmq: Container, monkeypatch):
    def on_message(*args):
        raise Exception("something unexpected happened while handling incoming message")

    def on_basic_qos_ok(consumer):
        consumer.channel.basic_publish("", "tasks", body=b"some message")

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
        on_message=on_message,
    )

    assert consumer.should_reconnect is True


@pytest.mark.parametrize("sig", [signal.SIGKILL, signal.SIGINT])
def test_kill_rabbitmq(rabbitmq: Container, monkeypatch, sig):
    def on_basic_qos_ok(consumer):
        rabbitmq.kill(sig)

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        on_basic_qos_ok=on_basic_qos_ok,
    )

    assert consumer.should_reconnect is True


def test_without_rabbitmq():
    consumer = set_up_consumer(
        "non_available_host",
        on_message=lambda *args: None,
    )

    assert consumer.should_reconnect is True
