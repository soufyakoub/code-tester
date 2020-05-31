from _pytest.monkeypatch import MonkeyPatch

from src.runner.consumer import Consumer


def set_up_consumer(target_host: str, monkeypatch: MonkeyPatch = None, **kwargs) -> Consumer:
    """
    Set up a consumer instance with hooks.

    Hooks are called with the real method or callback arguments after they're done executing.
    """
    consumer = Consumer(
        target_host,
        "tasks",
        1,
        kwargs.pop("on_message", lambda *args: None),
    )

    if monkeypatch:
        for method_name, callback in kwargs.items():
            original_method = getattr(consumer, method_name)

            def mock_method(*args, **kwargs):
                original_method(*args, **kwargs)
                callback(consumer, *args, **kwargs)

            monkeypatch.setattr(consumer, method_name, mock_method)

    return consumer
