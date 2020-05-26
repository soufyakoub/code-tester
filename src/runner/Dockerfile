FROM python:3.8-alpine

RUN python -m pip install docker pika

WORKDIR /root

COPY .  ./

RUN chmod +x ./wait-for-it.sh

# waiting for rabbitmq to be ready before starting
ENTRYPOINT ["./wait-for-it.sh" , "rabbitmq:5672" , "--"]
CMD ["python" , "index.py"]
