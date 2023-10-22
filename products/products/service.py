import logging

from nameko.events import event_handler
from nameko.rpc import rpc

from products import dependencies
from products.schemas import Product

from typing import List

logger = logging.getLogger(__name__)


class ProductsService:

    name = 'products'

    storage = dependencies.Storage()

    @rpc
    def get(self, product_id) -> Product:
        logger.info('Getting product: %s', product_id)
        product = self.storage.get(product_id)
        return Product().dump(product).data

    @rpc
    def list(self) -> List[Product]:
        logger.info('Listing products')
        products = self.storage.list()
        return Product(many=True).dump(products).data

    @rpc
    def create(self, product) -> None:
        logger.info('Creating product: %s', product)
        product = Product(strict=True).load(product).data
        self.storage.create(product)

    @event_handler('orders', 'order_created')
    def handle_order_created(self, payload) -> None:
        logger.info('Handling order created: %s', payload)
        for product in payload['order']['order_details']:
            self.storage.decrement_stock(
                product['product_id'], product['quantity'])
