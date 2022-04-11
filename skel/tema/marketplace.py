"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""


from threading import Lock
import logging
import time
import unittest
from logging.handlers import RotatingFileHandler


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    # Logger preamble
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-5s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logging.Formatter.converter = time.gmtime
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        'marketplace.log', maxBytes=10000, backupCount=10)
    handler.setFormatter(formatter)
    logger.propagate = False
    logging.Formatter.converter = time.gmtime
    logger.addHandler(handler)

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.num_carts = 0
        self.num_producers = 0
        self.products_per_producer = []
        self.carts = {}     # {cart_id : {product : [[producer_id, quantity]]}}
        self.products = {}  # {producer : {producer_id, quantity}}
        self.lock_add_cart = Lock()
        self.lock_add_product = Lock()
        self.lock_producer = Lock()
        self.lock_cart = Lock()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        # Does not let two threads have the same producer id
        self.lock_producer.acquire()
        producer_id = self.num_producers
        self.num_producers += 1
        self.lock_producer.release()

        # Create object counter for producer
        self.products_per_producer.append(0)

        self.logger.info(
            'Method \'register producer\' returns int: %d', producer_id)
        return producer_id

    def add_product(self, producer_id, product):
        self.logger.info(
            'Method \'add_product\' has params producer_id (int): %d, product (object): %s',
            producer_id, str(product))

        # Add product alongside the quantity each producer provides
        if self.products.get(product) is None:
            # Product does not exist -> add it as one product
            self.products[product] = {producer_id: 1}
        else:
            # Product does exist -> increment producer's product count
            if self.products[product].get(producer_id) is None:
                self.products[product][producer_id] = 1
            else:
                self.products[product][producer_id] += 1

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        self.logger.info(
            'Method \'publish\' has params producer_id (int): %d, product (object): %s',
            producer_id, str(product))

        # Check if the maximum queue size has not been reached
        if self.products_per_producer[producer_id] < self.queue_size_per_producer:
            # Increment the count of objects the producer has
            self.products_per_producer[producer_id] += 1

            # Let only one thread add a product
            self.lock_add_product.acquire()
            self.add_product(producer_id, product)
            self.lock_add_product.release()

            self.logger.info('Method \'publish\' returns bool: True')
            return True

        self.logger.info('Method \'publish\' returns bool: False')
        return False

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        # Does not let two threads have the same cart id
        self.lock_cart.acquire()
        cart_id = self.num_carts
        self.num_carts += 1
        self.lock_cart.release()

        # Initialize empty dictionary for the generated cart
        self.carts[cart_id] = {}

        self.logger.info('Method \'new_cart\' returns int: %d', cart_id)
        return cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        self.logger.info(
            'Method \'add_to_cart\' has params cart_id (int): %d, product (object): %s',
            cart_id, str(product))

        # Check if the product exists
        if self.products.get(product) is None:
            logging.info('Method \'add_to_cart\' returns bool: False')
            return False

        # Let only one thread occupy a product
        self.lock_add_cart.acquire()

        # Get the product from the first producer available
        producer_id = next(iter(self.products[product]))
        # Decrement the quantity of the required product that the producer has in the marketplace
        self.products[product][producer_id] -= 1

        # If the producer's quantity reaches 0 -> remove him
        if self.products[product][producer_id] == 0:
            del self.products[product][producer_id]

        # If the product does not have any more producers -> remove it
        if len(self.products[product]) == 0:
            del self.products[product]

        self.lock_add_cart.release()

        # Check if the cart already has the product
        if self.carts[cart_id].get(product) is None:
            # The cart does not have the product -> add its producer and quantity
            self.carts[cart_id][product] = [[producer_id, 1]]
        else:
            # The cart does have the product -> increment the quantity of the producer
            for cart_product in self.carts[cart_id][product]:
                if cart_product[0] == producer_id:
                    cart_product[1] += 1
                    break
            else:
                # The producer is not in the list -> add him as a provider and the quantity
                self.carts[cart_id][product].append([producer_id, 1])

        self.logger.info('Method \'add_to_cart\' returns bool: True')
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        self.logger.info(
            'Method \'remove_from_cart\' has params cart_id (int): %d, product (object): %s',
            cart_id, str(product))

        # Check if the cart has the product
        if self.carts[cart_id].get(product) is None:
            return

        # Get the first producer of the product in the cart
        producer_id = self.carts[cart_id][product][0][0]
        # Decrement his quantity
        self.carts[cart_id][product][0][1] -= 1

        # Check if the producer has any quantity left, otherwise remove him
        if self.carts[cart_id][product][0][1] == 0:
            del self.carts[cart_id][product][0]
        # Check if the cart has any product left, otherwise remove it
        if self.carts[cart_id][product] == []:
            del self.carts[cart_id][product]

        # Let only one thread mark the product removed from the cart as available again
        self.lock_add_product.acquire()
        self.add_product(producer_id, product)
        self.lock_add_product.release()

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        self.logger.info(
            'Method \'place_order\' has params cart_id (int): %d', cart_id)

        cart_list = []

        # Iterate through the cart
        for product in self.carts[cart_id]:
            for producer in self.carts[cart_id][product]:
                for _ in range(producer[1]):
                    # Decrease the queue size of the producer
                    self.products_per_producer[producer[0]] -= 1
                    # Add the product to the list
                    cart_list.append(product)

        # Delete the cart
        del self.carts[cart_id]

        self.logger.info(
            'Method \'place_order\' returns cart (list): %s', str(cart_list))
        return cart_list


class MarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.marketplace = Marketplace(5)

    def test_register_producer(self):
        # Check the IDs of the producers
        self.assertEqual(0, self.marketplace.register_producer())
        self.assertEqual(1, self.marketplace.register_producer())

    def test_add_product(self):
        self.marketplace.add_product(0, 'Chocolate')
        # Check if the product is added
        self.assertIsNotNone(self.marketplace.products.get('Chocolate'))
        # Check if the quantity is right
        self.assertDictEqual({0: 1}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(0, 'Chocolate')
        # Check if the quantity has been incremented
        self.assertDictEqual({0: 2}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(0, 'Vanilla')
        # Check if the products is in the dict
        self.assertDictEqual({0: 1}, self.marketplace.products['Vanilla'])
        self.marketplace.add_product(1, 'Chocolate')
        # Check if the quantities are right
        self.assertDictEqual(
            {0: 2, 1: 1}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(1, 'Chocolate')
        # Check if the quantities have been incremented
        self.assertDictEqual(
            {0: 2, 1: 2}, self.marketplace.products['Chocolate'])
        # Check if a search of a non-element return true
        self.assertIsNone(self.marketplace.products.get('None'))

    def test_publish(self):
        producer_id = self.marketplace.register_producer()

        for i in range(5):
            # Check if the method returns True (queue size limit)
            self.assertTrue(self.marketplace.publish(producer_id, 'Cocoa'))
            # Check if the quantity is right
            self.assertDictEqual({producer_id: i + 1},
                                 self.marketplace.products['Cocoa'])
            # Check if the queue size for the producer is right
            self.assertEqual(
                i + 1, self.marketplace.products_per_producer[producer_id])

        # Check if the product has not been added (queue size limit has been reached)
        self.assertFalse(self.marketplace.publish(producer_id, 'Cocoa'))
        self.assertDictEqual(
            {producer_id: 5}, self.marketplace.products['Cocoa'])
        self.assertEqual(
            5, self.marketplace.products_per_producer[producer_id])

    def test_new_cart(self):
        # Check the IDs of the cart
        self.assertEqual(0, self.marketplace.new_cart())
        self.assertEqual(1, self.marketplace.new_cart())

    def test_add_to_cart(self):
        cart = self.marketplace.new_cart()
        producer_id = self.marketplace.register_producer()
        producer_id_new = self.marketplace.register_producer()

        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Vanilla')
        # Check if product was added to cart
        self.assertTrue(self.marketplace.add_to_cart(cart, 'Cocoa'))
        # Check if the product quantity is updated correctly
        self.assertDictEqual(
            {'Cocoa': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual(
            {'Cocoa': [[producer_id, 2]]}, self.marketplace.carts[cart])
        # Check if the cart contains two products
        self.marketplace.add_to_cart(cart, 'Vanilla')
        self.assertDictEqual({'Cocoa': [[producer_id, 2]], 'Vanilla': [
                             [producer_id, 1]]}, self.marketplace.carts[cart])
        # Check if the quantity is incremented correctly
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id, 2]], 'Vanilla': [
                             [producer_id, 1]]}, self.marketplace.carts[cart])
        # Check if the producer ID is correct for every product added
        self.marketplace.publish(producer_id_new, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id, 2], [producer_id_new, 1]], 'Vanilla': [
                             [producer_id, 1]]}, self.marketplace.carts[cart])

        # Check if non-member can be added to cart
        self.assertIsNone(self.marketplace.carts[cart].get('None'))
        # Check if non-member is in cart
        self.assertFalse(self.marketplace.add_to_cart(cart, 'None'))

        # Check if product in cart is still available to other consumers
        self.assertIsNone(self.marketplace.products.get('Cocoa'))
        # Check if queue size for producer is not altered
        self.assertEqual(
            3, self.marketplace.products_per_producer[producer_id])

    def test_remove_from_cart(self):
        cart = self.marketplace.new_cart()
        producer_id = self.marketplace.register_producer()
        producer_id_new = self.marketplace.register_producer()

        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Vanilla')
        self.marketplace.publish(producer_id_new, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Vanilla')

        self.marketplace.remove_from_cart(cart, 'Cocoa')
        # Check if the cart has been updated accordingly
        self.assertDictEqual({'Cocoa': [[producer_id, 1], [producer_id_new, 1]], 'Vanilla': [
                             [producer_id, 1]]}, self.marketplace.carts[cart])
        # Check if the product has been reintroduced in the market
        self.assertDictEqual(
            {producer_id: 1}, self.marketplace.products['Cocoa'])

        # Check if the producer's queue size has not been altered
        self.assertEqual(
            3, self.marketplace.products_per_producer[producer_id])

        # Check if the producer is removed once his quantity is 0
        self.marketplace.remove_from_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id_new, 1]], 'Vanilla': [
                             [producer_id, 1]]}, self.marketplace.carts[cart])

        self.marketplace.remove_from_cart(cart, 'Cocoa')
        # Check if the product is removed once its quantity is 0
        self.assertDictEqual(
            {'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'None')
        # Check if a removal of a non-element affects the cart
        self.assertDictEqual(
            {'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'Vanilla')
        # Check if cart is empty
        self.assertDictEqual({}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'None')
        # Check if cart remains empty
        self.assertDictEqual({}, self.marketplace.carts[cart])

    def test_place_order(self):
        cart = self.marketplace.new_cart()
        producer_id = self.marketplace.register_producer()
        producer_id_new = self.marketplace.register_producer()

        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Vanilla')
        self.marketplace.publish(producer_id_new, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Vanilla')

        # Check if the list returned is correct
        self.assertEqual(['Cocoa', 'Cocoa', 'Cocoa', 'Vanilla'],
                         self.marketplace.place_order(cart))
        # Check if the cart has been removed
        self.assertIsNone(self.marketplace.carts.get(cart))
        # Check if the queue size of the producer has been decremented
        self.assertEqual(
            0, self.marketplace.products_per_producer[producer_id])
        # Check if the products were completely removed
        self.assertIsNone(self.marketplace.products.get('Cocoa'))
        self.assertIsNone(self.marketplace.products.get('Vanilla'))
