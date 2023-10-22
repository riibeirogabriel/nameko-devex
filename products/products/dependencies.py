from nameko import config
from nameko.extensions import DependencyProvider
import redis

from products.exceptions import NotFound, ProductAlreadyExists
from products.schemas import Product
from typing import Iterator

REDIS_URI_KEY = 'REDIS_URI'


class StorageWrapper:
    """
    Product storage

    A very simple example of a custom Nameko dependency. Simplified
    implementation of products database based on Redis key value store.
    Handling the product ID increments or keeping sorted sets of product
    names for ordering the products is out of the scope of this example.

    """

    NotFound = NotFound
    ProductAlreadyExists = ProductAlreadyExists

    def __init__(self, client) -> None:
        self.client = client

    def _format_key(self, product_id: str) -> str:
        return 'products:{}'.format(product_id)

    def _from_hash(self, document: dict) -> dict:
        return {
            'id': document[b'id'].decode('utf-8'),
            'title': document[b'title'].decode('utf-8'),
            'passenger_capacity': int(document[b'passenger_capacity']),
            'maximum_speed': int(document[b'maximum_speed']),
            'in_stock': int(document[b'in_stock'])
        }

    def get(self, product_id: str) -> dict:
        product = self.client.hgetall(self._format_key(product_id))
        if not product:
            raise NotFound('Product ID {} does not exist'.format(product_id))
        else:
            return self._from_hash(product)

    def list(self) -> Iterator[dict]:
        keys = self.client.keys(self._format_key('*'))
        for key in keys:
            yield self._from_hash(self.client.hgetall(key))

    def create(self, product: dict) -> None:
        product_inserted = self.client.hgetall(self._format_key(product['id']))
        if product_inserted:
            raise ProductAlreadyExists(
                'Product ID {} already exists'.format(product['id']))
        self.client.hmset(
            self._format_key(product['id']),
            product)

    def decrement_stock(self, product_id: str, amount: int) -> int:
        return self.client.hincrby(
            self._format_key(product_id), 'in_stock', -amount)


class Storage(DependencyProvider):

    def setup(self) -> None:
        self.client = redis.StrictRedis.from_url(config.get(REDIS_URI_KEY))

    def get_dependency(self, worker_ctx) -> StorageWrapper:
        return StorageWrapper(self.client)
