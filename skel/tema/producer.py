"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
import time


class Producer(Thread):
    """
    Class that represents a producer.
    """

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.kwargs = kwargs

    def run(self):
        # Generate producer ID
        producer_id = self.marketplace.register_producer()

        while True:
            for product in self.products:
                current_quantity_added = 0
                prod_name = product[0]
                prod_quantity = product[1]
                prod_wait_time = product[2]

                # Publish as many products as needed
                while current_quantity_added < prod_quantity:
                    status = self.marketplace.publish(producer_id, prod_name)
                    if status is False:
                        # Retry again in a few moments
                        time.sleep(self.republish_wait_time)
                    else:
                        # Produce the product and increment the counter
                        time.sleep(prod_wait_time)
                        current_quantity_added += 1
