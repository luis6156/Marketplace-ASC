"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""


from math import prod
from threading import Lock
import logging
import time
import unittest
from logging.handlers import RotatingFileHandler

from yaml import Mark

class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-5s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    logging.Formatter.converter = time.gmtime
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler('marketplace.log', maxBytes=10000, backupCount=10)
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
        self.carts = {}
        self.products = {}
        self.lock_add_cart = Lock()
        self.lock_add_product = Lock()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        producer_id = self.num_producers
        self.num_producers += 1
        self.products_per_producer.append(0)
        
        self.logger.info('Method \'register producer\' returns int: %d', producer_id)
        return producer_id
    
    def add_product(self, producer_id, product):
        self.logger.info('Method \'add_product\' has params producer_id (int): %d, product (object): %s', producer_id, str(product))
        
        if (self.products.get(product) == None):
                self.products[product] = {producer_id : 1}
        else:
            if (self.products[product].get(producer_id) == None):
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
        self.logger.info('Method \'publish\' has params producer_id (int): %d, product (object): %s', producer_id, str(product))
        
        if (self.products_per_producer[producer_id] < self.queue_size_per_producer):
            self.products_per_producer[producer_id] += 1
            
            self.lock_add_product.acquire()
            self.add_product(producer_id, product)
            self.lock_add_product.release()
            self.logger.info('Method \'publish\' returns bool: True')
            return True
        else:
            self.logger.info('Method \'publish\' returns bool: False')
            return False

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        cart_id = self.num_carts
        self.carts[cart_id] = {}
        self.num_carts += 1
        
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
        self.logger.info('Method \'add_to_cart\' has params cart_id (int): %d, product (object): %s', cart_id, str(product))
        
        if (self.products.get(product) == None):
            logging.info('Method \'add_to_cart\' returns bool: False')
            return False
        
        self.lock_add_cart.acquire()
        
        producer_id = next(iter(self.products[product]))
        # Decrement the quantity of the required product that the producer has in the marketplace
        self.products[product][producer_id] -= 1
        if (self.products[product][producer_id] == 0):
            del(self.products[product][producer_id])
            
        if (len(self.products[product]) == 0):
            del(self.products[product])     
            
        self.lock_add_cart.release()
        
        if (self.carts[cart_id].get(product) == None):
            self.carts[cart_id][product] = [[producer_id, 1]]
        else:
            for cart_product in self.carts[cart_id][product]:
                if (cart_product[0] == producer_id):
                    cart_product[1] += 1
                    break
            else:
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
        self.logger.info('Method \'remove_from_cart\' has params cart_id (int): %d, product (object): %s', cart_id, str(product))
        
        if (self.carts[cart_id].get(product) == None):
            return
        
        producer_id = self.carts[cart_id][product][0][0]
        self.carts[cart_id][product][0][1] -= 1
        if (self.carts[cart_id][product][0][1] == 0):
            del(self.carts[cart_id][product][0])
        if (self.carts[cart_id][product] == []):
            del(self.carts[cart_id][product])
            
        self.lock_add_product.acquire()   
        self.add_product(producer_id, product)
        self.lock_add_product.release()

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        self.logger.info('Method \'place_order\' has params cart_id (int): %d', cart_id)
        
        cart_list = []
        
        for product in self.carts[cart_id]:
            for producer in self.carts[cart_id][product]:
                for _ in range(producer[1]):
                    self.products_per_producer[producer[0]] -= 1
                    cart_list.append(product)
            
        del(self.carts[cart_id])
        
        self.logger.info('Method \'place_order\' returns cart (list): %s', str(cart_list))
        return cart_list
    
class MarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.marketplace = Marketplace(5)
    
    def test_register_producer(self):
        self.assertEqual(0, self.marketplace.register_producer())
        self.assertEqual(1, self.marketplace.register_producer())

    def test_add_product(self):
        self.marketplace.add_product(0, 'Chocolate')
        self.assertIsNotNone(self.marketplace.products.get('Chocolate'))
        self.assertDictEqual({0: 1}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(0, 'Chocolate')
        self.assertDictEqual({0: 2}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(0, 'Vanilla')
        self.assertDictEqual({0: 1}, self.marketplace.products['Vanilla'])
        self.marketplace.add_product(1, 'Chocolate')
        self.assertDictEqual({0: 2, 1: 1}, self.marketplace.products['Chocolate'])
        self.marketplace.add_product(1, 'Chocolate')
        self.assertDictEqual({0: 2, 1: 2}, self.marketplace.products['Chocolate'])
        self.assertIsNone(self.marketplace.products.get('None'))
        
    def test_publish(self):
        producer_id = self.marketplace.register_producer()
        
        for i in range(5):
            self.assertTrue(self.marketplace.publish(producer_id, 'Cocoa'))
            self.assertDictEqual({producer_id: i + 1}, self.marketplace.products['Cocoa'])
            self.assertEqual(i + 1, self.marketplace.products_per_producer[producer_id])
            
        self.assertFalse(self.marketplace.publish(producer_id, 'Cocoa'))
        self.assertDictEqual({producer_id: 5}, self.marketplace.products['Cocoa'])
        self.assertEqual(5, self.marketplace.products_per_producer[producer_id])
        
    def test_new_cart(self):
        self.assertEqual(0, self.marketplace.new_cart())
        self.assertEqual(1, self.marketplace.new_cart())
        
    def test_add_to_cart(self):
        cart = self.marketplace.new_cart()
        producer_id = self.marketplace.register_producer()
        producer_id_new = self.marketplace.register_producer()
        
        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Cocoa')
        self.marketplace.publish(producer_id, 'Vanilla')
        self.assertTrue(self.marketplace.add_to_cart(cart, 'Cocoa'))
        self.assertDictEqual({'Cocoa': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id, 2]]}, self.marketplace.carts[cart])
        self.marketplace.add_to_cart(cart, 'Vanilla')
        self.assertDictEqual({'Cocoa': [[producer_id, 2]], 'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id, 2]], 'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.publish(producer_id_new, 'Cocoa')
        self.marketplace.add_to_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id, 2], [producer_id_new, 1]], 'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])

        self.assertIsNone(self.marketplace.carts[cart].get('None'))
        self.assertFalse(self.marketplace.add_to_cart(cart, 'None'))
        
        self.assertIsNone(self.marketplace.products.get('Cocoa'))
        self.assertEqual(3, self.marketplace.products_per_producer[producer_id])
        
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
        self.assertDictEqual({'Cocoa': [[producer_id, 1], [producer_id_new, 1]], 'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.assertDictEqual({producer_id: 1}, self.marketplace.products['Cocoa'])
        
        self.assertEqual(3, self.marketplace.products_per_producer[producer_id])
        
        self.marketplace.remove_from_cart(cart, 'Cocoa')
        self.assertDictEqual({'Cocoa': [[producer_id_new, 1]], 'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        
        self.marketplace.remove_from_cart(cart, 'Cocoa')
        self.assertDictEqual({'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'None')
        self.assertDictEqual({'Vanilla': [[producer_id, 1]]}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'Vanilla')
        self.assertDictEqual({}, self.marketplace.carts[cart])
        self.marketplace.remove_from_cart(cart, 'None')
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
        
        self.assertEqual(['Cocoa', 'Cocoa', 'Cocoa', 'Vanilla'], self.marketplace.place_order(cart))
        self.assertIsNone(self.marketplace.carts.get(cart))
        self.assertEqual(0, self.marketplace.products_per_producer[producer_id])
        self.assertIsNone(self.marketplace.products.get('Cocoa'))
        self.assertIsNone(self.marketplace.products.get('Vanilla'))
        
        