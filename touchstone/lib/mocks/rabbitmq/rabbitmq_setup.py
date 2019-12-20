from threading import Thread

import pika
from pika import spec
from pika.adapters.blocking_connection import BlockingChannel

from touchstone.lib.mocks.mock_case import Setup
from touchstone.lib.mocks.rabbitmq.rmq_context import RmqContext


class MessageConsumer(Thread):
    def __init__(self, connection_params: pika.ConnectionParameters, rmq_context: RmqContext):
        super().__init__()
        self.__connection_params = connection_params
        self.__rmq_context = rmq_context

        connection = pika.BlockingConnection(self.__connection_params)
        self.channel: BlockingChannel = connection.channel()

    def run(self) -> None:
        super().run()
        self.channel.start_consuming()

    def consume(self, exchange: str, routing_key: str, queue: str):
        def message_received(channel: BlockingChannel, method: spec.Basic.Deliver, properties: spec.BasicProperties,
                             body: bytes):
            payload = str(body)
            # TODO: use exchange/routing key here
            self.__rmq_context.shadow_queue_payload_received(queue, payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue, message_received)


class RabbitmqSetup(Setup):
    def __init__(self, channel: BlockingChannel, connection_params: pika.ConnectionParameters, rmq_context: RmqContext):
        super().__init__()
        self.__channel = channel
        self.__rmq_context = rmq_context

        self.__message_consumer: MessageConsumer = MessageConsumer(connection_params, rmq_context)
        self.__exchanges: list = []
        self.__queues: list = []

    def load_defaults(self, defaults: dict):
        for exchange in defaults['exchanges']:
            self.__create_exchange(exchange['name'], exchange['type'])
            for queue in exchange['queues']:
                routing_key = queue.get('routingKey', None)
                self.__create_queue(queue['name'], exchange['name'], routing_key)
        if not self.__message_consumer.is_alive():
            self.__message_consumer.start()

    def reset(self):
        self.__rmq_context.reset()
        for queue in self.__queues:
            self.__channel.queue_purge(queue)

    def stop_listening(self):
        def callback():
            self.__message_consumer.channel.stop_consuming()

        self.__message_consumer.channel.connection.add_callback_threadsafe(callback)
        self.__message_consumer.join()

    def __create_exchange(self, name: str, exchange_type: str = 'direct'):
        if name not in self.__exchanges:
            self.__channel.exchange_declare(name, exchange_type=exchange_type)
            self.__exchanges.append(name)

    def __create_queue(self, name: str, exchange: str, routing_key: str = ''):
        if name not in self.__queues:
            self.__channel.queue_declare(name)
            self.__channel.queue_bind(name, exchange, routing_key=routing_key)
            self.__queues.append(name)

            shadow_queue_name = name + '.touchstone-shadow'
            self.__channel.queue_declare(shadow_queue_name)
            self.__channel.queue_bind(shadow_queue_name, exchange, routing_key=routing_key)
            self.__queues.append(shadow_queue_name)
            self.__rmq_context.add_shadow_queue(shadow_queue_name)
            self.__message_consumer.consume(shadow_queue_name)
