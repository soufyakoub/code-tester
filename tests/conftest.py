from pytest_docker_tools import container, volume, wrappers


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
