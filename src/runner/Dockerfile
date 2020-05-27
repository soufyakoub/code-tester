FROM python:3.8-alpine

RUN python -m pip install docker pika

WORKDIR /root

COPY .  ./

RUN chmod +x ./wait-for-it && mv ./wait-for-it /bin

# waiting for rabbitmq to be ready before starting
ENTRYPOINT ["wait-for-it" , "rabbitmq:5672" , "--"]
CMD ["python" , "index.py"]
