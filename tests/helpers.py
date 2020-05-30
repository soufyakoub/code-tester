from src.runner.consumer import Consumer


def set_up_consumer(target_host: str, **kwargs) -> Consumer:
    consumer = Consumer(
        target_host,
        "tasks",
        1,
        kwargs.get("on_message", lambda *args: None),
    )

    monkeypatch = kwargs.get("monkeypatch")

    if monkeypatch:

        on_basic_qos_ok = kwargs.get("on_basic_qos_ok")

        if callable(on_basic_qos_ok):
            old_on_basic_qos_ok = consumer._on_basic_qos_ok

            def mock_on_basic_qos_ok(*args):
                old_on_basic_qos_ok(*args)
                on_basic_qos_ok(consumer)

            monkeypatch.setattr(consumer, "_on_basic_qos_ok", mock_on_basic_qos_ok)

    # This is a blocking method
    consumer.start()

    return consumer
