"""
 Combining them together it is possible to have the following scenarios:
    position 
    order MM
    order PT
 
    There are 2 major scenarios:
        1. There is no open position 
            a. There is no open order
            b. There are equal number of open buy and sell orders
            c. There are non-sense open orders
        2. There is an open position
            a. There is no Order_MM and no Order_PT
            b. There is Order_MM and no Order_PT
            c. There is Order_MM and Order_PT
            d. There is no Order_MM and Order_PT
         

    Scenario      |   Position   |   Order_MM    |   Order_PT    |   Action
    1a            |   None       |   None        |   None        |   Place buy and sell orders
    1b            |   None       |   X           |   X           |   Pass as long as #_order_buy = #_order_sell
    1c            |   None       |   Irrelevant  |   Irrelevant  |   Cancel all
    ---------------------------- ---------------------------------------------------------------------------------------------------------------------
    Scenario      |   Position   |   Order_MM    |   Order_PT    |   Action
                  |              | Buy   | Sell  | Buy  | Sell   |
     
    2a.1          |      x       | None  | None  | None | None   |   place PT order in oposite direction
    ---------------------------- -----------------------------------------------
    2b.1          |      x       |   X   | None  | None | None   |   Cancel order_MM and place PT order in oposite direction
    2b.2          |      x       | None  |  X    | None | None   |   Cancel order_MM and place PT order in oposite direction
    2b.3          |      x       |  X    |  X    | None | None   |   Cancel order_MM and place PT order in oposite direction
    ---------------------------- -----------------------------------------------
    2c.1          |      x       |  X    | None  |  X   | None   |   Cancel PT order and place PT order in oposite direction
    2c.2          |      x       |  X    | None  | None |  X     |   Check size of position and order, if different, cancel order_MM and place PT order in oposite direction
    2c.3          |      x       |  X    | None  |  X   |  X     |   Cancel PT order and check size of position and order, if different, cancel order_MM and place PT order in oposite direction
     
    2c.4          |      x       | None  |  X    |  X   | None   |   Check size of position and order, if different, cancel order_MM and place PT order in oposite direction
    2c.5          |      x       | None  |  X    | None |  X     |   Cancel PT order and place PT order in oposite direction
    2c.6          |      x       | None  |  X    |  X   |  X     |   Cancel PT order and check size of position and order, if different, cancel order_MM and place PT order in oposite direction
    ---------------------------- -----------------------------------------------
    2d.1          |      x       | None  | None  |  X   | None   |   Cancel order PT and place PT order in oposite direction
    2d.2          |      x       | None  | None  | None |  X     |   Cancel order PT and place PT order in oposite direction
    2d.3          |      x       | None  | None  |  X   |  X     |   Cancel order PT and place PT order in oposite direction
    ---------------------------- -----------------------------------------------
                  | Long | Short | Buy   | Sell  | Buy  | Sell   |
    2c.7          |  x   |       |  X    |  X    |  X   | None   |   Cancel Order_MM_Buy and Order_PT_Buy
    2c.8          |  x   |       |  X    |  X    | None |  X     |   Cancel Order_MM_Buy
    2c.9          |  x   |       |  X    |  X    |  X   |  X     |   Cancel Order_MM_Buy and Order_PT_Buy
    2c.10         |      |  x    |  X    |  X    |  X   | None   |   Cancel Order_MM_Sell and Order_PT_Sell 
    2c.11         |      |  x    |  X    |  X    | None |  X     |   Cancel Order_MM_Sell
    2c.12         |      |  x    |  X    |  X    |  X   |  X     |   Cancel Order_MM_Sell and Order_PT_Sell
    ---------------------------- -----------------------------------------------
   """


# create a check point where I check that no changes in order and postions have been made
# if no changes, then do nothing
# if changes, then go to the scenarios

def check_positions():
    # check if there are any open positions
