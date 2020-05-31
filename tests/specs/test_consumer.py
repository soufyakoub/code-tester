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

    def _on_basic_qos_ok(self, _):
        self.channel.basic_publish("", "tasks", body=b"some message")

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
        on_message=on_message,
    )

    consumer.start()

    assert message_body == b"some message"
    assert consumer.should_reconnect is False


def test_stop_gracefully(rabbitmq: Container, monkeypatch):
    def _on_basic_qos_ok(self, _):
        self.stop()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
    )

    consumer.start()

    assert consumer.should_reconnect is False


def test_close_connection(rabbitmq: Container, monkeypatch):
    def _on_basic_qos_ok(self, _):
        self.connection.close()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
    )

    consumer.start()

    assert consumer.should_reconnect is True


def test_close_channel(rabbitmq: Container, monkeypatch):
    def _on_basic_qos_ok(self, _):
        self.channel.close()

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
    )

    consumer.start()

    assert consumer.should_reconnect is True


def test_on_message_exception(rabbitmq: Container, monkeypatch):
    def on_message(*args):
        raise Exception("something unexpected happened while handling incoming message")

    def _on_basic_qos_ok(self, _):
        self.channel.basic_publish("", "tasks", body=b"some message")

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
        on_message=on_message,
    )

    consumer.start()

    assert consumer.should_reconnect is True


@pytest.mark.parametrize("sig", [signal.SIGKILL, signal.SIGINT])
def test_kill_rabbitmq(rabbitmq: Container, monkeypatch, sig):
    def _on_basic_qos_ok(self, _):
        rabbitmq.kill(sig)

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
    )

    consumer.start()

    assert consumer.should_reconnect is True


def test_remote_consumer_cancel(rabbitmq: Container, monkeypatch):
    def _on_basic_qos_ok(self, _):
        # Force the rabbitmq host to cancel the consumer remotely
        consumer.channel.queue_delete("tasks")

    consumer = set_up_consumer(
        rabbitmq.ips.primary,
        monkeypatch,
        _on_basic_qos_ok=_on_basic_qos_ok,
    )

    consumer.start()

    assert consumer.should_reconnect is True


def test_without_rabbitmq():
    consumer = set_up_consumer("non_available_host")

    consumer.start()

    assert consumer.should_reconnect is True


def test_on_message_param_type():
    with pytest.raises(TypeError):
        consumer = set_up_consumer(
            "non_available_host",
            on_message="something that's not a callable"
        )
