from _pytest.monkeypatch import MonkeyPatch

from src.runner.consumer import Consumer


def set_up_consumer(
        target_host: str,
        monkeypatch: MonkeyPatch = None,
        *,
        on_basic_qos_ok: callable = None,
        on_message: callable = None
) -> Consumer:
    if not callable(on_message):
        def on_message(*args):
            pass

    consumer = Consumer(target_host, "tasks", 1, on_message)

    if monkeypatch and callable(on_basic_qos_ok):
        old_on_basic_qos_ok = consumer._on_basic_qos_ok

        def mock_on_basic_qos_ok(*args):
            old_on_basic_qos_ok(*args)
            on_basic_qos_ok(consumer)

        monkeypatch.setattr(consumer, "_on_basic_qos_ok", mock_on_basic_qos_ok)

    # This is a blocking method
    consumer.start()

    return consumer
