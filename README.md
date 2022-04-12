# Copyright Micu Florian-Luis 2022 - Assignment 1

# Organization
This assignment makes use of Python's multithreading capabilities whilst also trying to solve
a Multiple Producers Multiple Consumers problem.

The code was made to have short methods and be easy to understand. The general flow follows the
creation of a producer which continuously adds products. A product has the following fields:
name, quantity and wait time. When a product is successfully added, the producer has to wait
its specific wait time, otherwise it tries again in a few moments. A product is added only
when the counter of objects added to the marketplace has not reached the limit. The consumer
tries to acquire carts in which he adds/removes products. At the end of the operations, the
consumer places the order which removes definitely the products from the marketplace and
decreases the counter of objects for the producers that sold the products in the cart. The
marketplace retains retains the products available and the carts and does various operations
on them.

An optimization could have been made to the cart generation method, as after an order has been
placed the cart is destroyed, thus its ID becomes available. However, in this implementation
the IDs just continue to be generated in a sequential way. This could become problematic as
the data type could become larger to accommodate for a larger number of carts.

# Implementation
## Consumer
In the run method, firstly a cart is generated then the operation for the current product is
determined and the according method is called (add/remove). Since multiple products should be
added/removed, the corresponding marketplace methods are called in a "while" loop. After the
operations are done, the "place_order" method is called and the resulting cart is printed.

## Producer
In the run method, the "producer_id" is generated and an infinite loop is ran so that he can
add products to the marketplace continuously. The product is published and the return status
is checked, in case the status is True the thread waits for the product's wait time, otherwise
it waits and tries again.

## Marketplace
### Register Producer
A counter variable is used to store the current amount of producers and it returns the current
value when a producer needs an ID.

### Add Product
It adds to the list of products the current product so that it can be bought by any consumer.
The product is added to a dictionary as a key, the value being another dictionary where the
key is the producer's ID and the value is the quantity of the product. This is useful as after
any operation the program knows which producer has sold any products so that it can decrement
its queue size.

### Publish
Calls the "Add Product" method whilst also increasing the queue size of the producer. If the
queue size hits the upper limit then the product is not added and the method returns false,
otherwise true.

### New Cart
Works exactly like the "Register Producer" except it also creates an entry in a list for the
producer that corresponds to the number of items the producer currently has in the marketplace.

### Add to Cart
If the product is not in the marketplace, it returns false, otherwise it gets the product from
the first producer available in the list and adds it to the cart. The quantity of the product
from the producer is decremented in the market (to mark it unavailable) and if the product does
not have any producers left it is removed. The last two operations are performed only by one
thread as two or more threads in the same area of code would result in an ambiguous result. The
cart is a dictionary where the key is the cart ID and the value is another dictionary where the
value is the key is the product and the value is a list of pairs (producer_id, quantity) of the
product. This is helpful when a product needs to be returned to the marked or checked out to
maintain notice of the producer that sells the product.

### Remove from Cart
If the product does not exist in the cart, the method returns, otherwise the first occurrence of
the product is removed from the cart and added back to the market by calling the "Add Product"
method (this operation is very similar to "Publish" however the queue size counter for the
producer should not be altered in this case). The quantity of the product from the producer is
decremented in the cart and if the product does not have any producers it is removed. The "Add
Product" method is called using a lock as two threads could add the same product twice.

### Place Order
The cart is iterated through and since the cart maintains the producers' IDs, their respective
queue size is decreased so that they can add more products to the market. Moreover, a list of
products is created and returned to the consumer to be printed.

## Unit Testing
I tested various cases for each method to reassure that every situation is covered and works
accordingly.

## Logging
The logger uses GMT time and RotatingHandler for better debug reasons. Moreover, every method
parameter is logged as well as every return.

## Git
The git folder was added to the archive.
