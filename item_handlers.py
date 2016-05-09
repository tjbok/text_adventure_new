### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ITEMS ###

# To add a new item handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.

# This is a helper function that prints out your string, but replaces
#  the '@' character with 'the <item name>' for whatever item you pass in.
def PrintDefaultActionString(default_string, item):
    print(default_string.replace("@", "the " + item.get("name")))

def Rock(context, action):
    if action["key"] == "ATTACK":
        print("Wow, you really showed that rock who's boss!")
        return True
    return False

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    items = context.items
    items.AddItemHandler("ROCK", Rock)