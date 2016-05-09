### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ITEMS ###

# To add a new item handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.

def Rock(context, action):
    if action["key"] == "ATTACK":
        context.Print("Wow, you really showed that rock who's boss!")
        return True
    return False

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    items = context.items
    items.AddItemHandler("ROCK", Rock)