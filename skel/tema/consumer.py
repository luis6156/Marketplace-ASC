"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread, Lock
import time


class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time
        self.kwargs = kwargs
        self.lock = Lock()

    def add_to_cart(self, cart_id, product, quantity):
        """ Adds quantity products to the cart with the given id. """
        num_products_added = 0

        # Add as many items as needed
        while num_products_added < quantity:
            status = self.marketplace.add_to_cart(cart_id, product)
            if status is False:
                # Wait and retry again
                time.sleep(self.retry_wait_time)
            else:
                # Increment number of items
                num_products_added += 1

    def remove_from_cart(self, cart_id, product, quantity):
        """ Removes quantity products to the cart with the given id. """
        num_products_removed = 0

        # Remove as many products as needed
        while num_products_removed < quantity:
            self.marketplace.remove_from_cart(cart_id, product)
            num_products_removed += 1

    def print_cart(self, cart):
        """ Print products in cart """
        for product in cart:
            print(self.kwargs['name'], "bought", product)

    def run(self):
        for cart in self.carts:
            # Generate a new cart
            cart_id = self.marketplace.new_cart()
            for operation in cart:
                op_type = operation['type']
                op_prod = operation['product']
                op_quantity = operation['quantity']
                if op_type == 'add':
                    # Add product to cart
                    self.add_to_cart(cart_id, op_prod, op_quantity)
                elif op_type == 'remove':
                    # Remove product from cart
                    self.remove_from_cart(cart_id, op_prod, op_quantity)
                else:
                    # Unknown operation -> discard it
                    continue

            # Checkout
            self.print_cart(self.marketplace.place_order(cart_id))
