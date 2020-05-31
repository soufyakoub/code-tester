from pytest_docker_tools import volume, wrappers
from pytest_docker_tools.builder import fixture_factory
from pytest_docker_tools.exceptions import ContainerNotReady, TimeoutError
from pytest_docker_tools.utils import wait_for_callable
from pytest_docker_tools.wrappers import Container


@fixture_factory()
def container(request, docker_client, wrapper_class, **kwargs):
    """
    A temporary solution for this
    `issue <https://github.com/Jc2k/pytest-docker-tools/issues/9#issuecomment-634311572>`_
    until a new version of
    `pytest-docker-tools <https://github.com/Jc2k/pytest-docker-tools>`_
    is released.
    """
    timeout = kwargs.pop('timeout', 30)
    kwargs.update({'detach': True})

    raw_container = docker_client.containers.run(**kwargs)
    request.addfinalizer(lambda: raw_container.remove(force=True) and raw_container.wait(timeout=10))

    wrapper_class = wrapper_class or Container
    container = wrapper_class(raw_container)

    try:
        wait_for_callable('Waiting for container to be ready', container.ready, timeout)
    except TimeoutError:
        raise ContainerNotReady(container, 'Timeout while waiting for container to be ready')

    return container


class RabbitMQContainer(wrappers.Container):
    def ready(self):
        """Returns True when rabbitmq host is ready to receive messages."""
        if super().ready():
            return "5672" in self.get_open_tcp_ports()
        return False


# rabbitmq:management-alpine has a VOLUME instruction in its Dockerfile,
# so when the container is removed after each test case,
# we're left with big volumes.
# this fixture takes care of removing them.
data_volume = volume()

rabbitmq = container(
    image="rabbitmq:management-alpine",
    volumes={
        "{data_volume.name}": {"bind": "/var/lib/rabbitmq"},
    },
    wrapper_class=RabbitMQContainer,
    timeout=60,
)
