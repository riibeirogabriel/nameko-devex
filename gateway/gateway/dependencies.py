from nameko import config
from nameko.extensions import DependencyProvider
import redis

from gateway.exceptions import ProductNotFoundInCache, ProductAlreadyExistsInCache
from typing import Iterator

REDIS_URI_KEY = 'REDIS_URI'


class CacheWrapper:
    """
    Product cache

    A cache for products based on Redis key value store.

    """

    ProductNotFound = ProductNotFoundInCache
    ProductAlreadyExists = ProductAlreadyExistsInCache

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
            raise ProductNotFoundInCache('Product ID {} does not exist in cache'.format(product_id))
        else:
            return self._from_hash(product)

    def list(self) -> Iterator[dict]:
        keys = self.client.keys(self._format_key('*'))
        for key in keys:
            yield self._from_hash(self.client.hgetall(key))

    def create(self, product: dict) -> None:
        product_inserted = self.client.hgetall(self._format_key(product['id']))
        if product_inserted:
            raise ProductAlreadyExistsInCache(
                'Product ID {} already exists in cache'.format(product['id']))
        self.client.hmset(
            self._format_key(product['id']),
            product)


class Cache(DependencyProvider):
    """
    Cache

    A cache using same redis instance of products service, but using a different database inside redis.

    """

    def setup(self) -> None:

        self.client = redis.StrictRedis.from_url(config.get(REDIS_URI_KEY), db=3)

    def get_dependency(self, worker_ctx) -> CacheWrapper:
        return CacheWrapper(self.client)
