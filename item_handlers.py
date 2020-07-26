### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ITEMS ###

# To add a new item handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.

def Coin(context, action, other_item, item_is_secondary):
    if (not item_is_secondary) and (not other_item == None):
        if (other_item["key"] == "COINSLOT") or (other_item["key"] == "JUKEBOX"):
            if not "COIN" in context.player.inventory:
                context.Print("You're not holding the coin.")
                return True    
            context.Print("The coin drops into the coin slot with a satisfying clunk.")
            context.player.inventory.remove("COIN")
            return True
    return False

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    items = context.items
    items.AddItemHandler("COIN", Coin)