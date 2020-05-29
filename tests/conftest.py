from pytest_docker_tools import container, wrappers


class RabbitMQContainer(wrappers.Container):
    def ready(self):
        """Returns True when rabbitmq host is ready to receive messages."""
        if super().ready():
            return "5672" in self.get_open_tcp_ports()
        return False


rabbitmq = container(image="rabbitmq:management-alpine", wrapper_class=RabbitMQContainer, timeout=60)
