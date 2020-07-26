### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ITEMS ###

# To add a new item handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.

def Coin(context, action, other_item, item_is_secondary):
    if (not item_is_secondary) and (not other_item == None):
        if (other_item["key"] == "COINSLOT") or (other_item["key"] == "JUKEBOX"):
            if not "COIN" in context.player.inventory:
                context.Print("You're not holding the coin.")
                return True    
            context.Print("The coin drops into the coin slot with a satisfying clunk. Lights on the numeric keypad on the jukebox begin to flash slowly.")
            context.player.inventory.remove("COIN")
            context.items["KEYPAD"]["awaiting_input?"] = True
            return True
    return False

def Jukebox(context, action, other_item, item_is_secondary):
  if (action["key"] == "EXAMINE") and (other_item == None):
    printstr = "It's a modern jukebox but fashioned to look like a 1950s classic. There is a coin slot, and a numeric keypad"
    if context.items["KEYPAD"]["awaiting_input?"]:
      printstr += ", which is faintly flashing"
    printstr += ".\n\nSONG MENU\n\n001 . . . . . . . . . . Take On Me, by Aha\n002 . . . . . . . . . . Old Town Road, by Lil Nas X"
    context.Print(printstr)
    return True
  return False

def JukeboxKeypad(context, action, other_item, item_is_secondary):
  if (action["key"] == "EXAMINE") and (other_item == None):
    printstr = "It's a standard numeric keypad"
    if context.items["KEYPAD"]["awaiting_input?"]:
      printstr += ", which is faintly flashing"    
    printstr += ". If you want to type a number, you can just say 'type 12345'."
    context.Print(printstr)
    return True
  return False

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    items = context.items
    items.AddItemHandler("COIN", Coin)
    items.AddItemHandler("JUKEBOX", Jukebox)
    items.AddItemHandler("KEYPAD", JukeboxKeypad)
