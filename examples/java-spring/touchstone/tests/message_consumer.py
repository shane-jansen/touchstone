import json

from touchstone.lib.touchstone_test import TouchstoneTest

mongo_database = 'myapp'
mongo_collection = 'orders'


class Order(TouchstoneTest):
    def processing_period(self) -> float:
        return 0.5

    def given(self) -> object:
        return {
            'userId': 1,
            'item': 'Foo',
            'quantity': 2
        }

    def when(self, given) -> object:
        self.mocks.rabbitmq.setup.publish('order-placed.exchange', json.dumps(given))
        return None

    def then(self, given, result) -> bool:
        return self.mocks.mongodb.verify.document_exists(mongo_database, mongo_collection, given, num_expected=1)