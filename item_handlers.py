### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ITEMS ###

# To add a new item handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.

def Coin(context, action, other_item, item_is_secondary):
    if ((action["key"] == "INSERT") or (action["key"] == "PUT_INTO")) and (not item_is_secondary):
        if not other_item:
            if context.player.location == "DINER_INTERIOR":
                context.Print("(in the coinslot)")
                context.Print("")
            else:
                context.PrintItemInString("You can't see anywhere here to insert @.", context.items["COIN"])
                return True
        elif not other_item["key"] in ["COINSLOT","JUKEBOX"]:
            return False
        
        if not "COIN" in context.player.inventory:
            context.Print("You're not holding the coin.")
            return True    
        context.Print("The coin drops into the coin slot with a satisfying clunk. Lights on the numeric keypad on the jukebox begin to flash slowly.")
        context.player.inventory.remove("COIN")
        context.items["KEYPAD"]["awaiting_input?"] = True
        return True
    return False

def Jukebox(context, action, other_item, item_is_secondary):
  if action["key"] == "EXAMINE":
    printstr = "It's a modern jukebox but fashioned to look like a 1950s classic. There is a coin slot, and a numeric keypad"
    if context.items["KEYPAD"]["awaiting_input?"]:
      printstr += ", which is faintly flashing"
    printstr += ".\n\n    SONG MENU\n\n    001 . . . . . . . . . . Take On Me, by Aha\n    002 . . . . . . . . . . Old Town Road, by Lil Nas X"
    context.Print(printstr)
    return True
  return False

def JukeboxKeypad(context, action, other_item, item_is_secondary):
    if action["key"] == "EXAMINE":
        printstr = "It's a standard numeric keypad"
        if context.items["KEYPAD"]["awaiting_input?"]:
            printstr += ", which is faintly flashing"    
        printstr += ". If you want to type a number, you can just say 'type 12345'."
        context.Print(printstr)
        return True
    return False

def Number(context, action, other_item, item_is_secondary):
    if (action["key"] in ["TYPE","TYPE_ON"]) and not item_is_secondary:
        if action["key"] == "TYPE":
            if context.player.location == "DINER_INTERIOR":
                context.Print("(on the jukebox keypad)")
                context.Print("")
            else:
                context.Print("You can't see any way to type numbers here.")
                return True
        elif not other_item["key"] in ["KEYPAD","JUKEBOX"]:
            return False
        
        if context.items["KEYPAD"].get("awaiting_input?"):
            keypad_entry = context.state.this_parsed_command[1].user_words[0]
            if keypad_entry in ["001","002"]:
                context.items["KEYPAD"]["awaiting_input?"] = False
                context.Print("The keypad flashes three times, and then the jukebox bounces to life.")
                context.items["JUKEBOX"]["song_choice"] = keypad_entry
                context.items["JUKEBOX"]["timer"] = 0
                context.events.CreateEventInNMoves(PlayJukebox, 0)
                return True

        context.Print("Nothing happens.")
        return True
    return False

def PlayJukebox(context):
  aha = ["We're talking away ... I don't know what ... I'm to say ...", "...TAAAAAAKE OOOOON MEEEEE (Take On Me)...", "...It's no better to be safe than sorry...", "... I'LL BEEEEEE GOOOOOOOOONE ...", "...Slowly learning that life is okay ..."]

  nas = ["Yeah, I'm gonna take my horse to the old town road...", "...Got the boots that's black to match...", "...I been in the valley ... You ain't been up off that porch, now...", "...Can't nobody tell me nothin'...", "...Cowboy hat from Gucci ... Wrangler on my booty..."]

  if context.player.location == "DINER_INTERIOR":
    printstr = "\nThe jukebox"
    if context.items["JUKEBOX"]["timer"] == 0:
      printstr += " begins playing a song slightly too loud for comfort"
    else:
      printstr += " is playing a loud song"
    printstr += ": \""
    if context.items["JUKEBOX"]["song_choice"] == "001":
      printstr += aha[context.items["JUKEBOX"]["timer"]]
    elif context.items["JUKEBOX"]["song_choice"] == "002":
      printstr += nas[context.items["JUKEBOX"]["timer"]]
    printstr += "\""
    if context.items["JUKEBOX"]["timer"] == 4:
      printstr += "\n\nThe song fades in its closing moments, and the jukebox once again is silent."
    context.Print(printstr)
  elif context.player.location == "OUTSIDE_DINER":
    context.Print("\nYou can hear the jukebox playing from inside the diner.")
  context.items["JUKEBOX"]["timer"] = context.items["JUKEBOX"]["timer"] + 1
  if context.items["JUKEBOX"]["timer"] < 5:
    context.events.CreateEventInNMoves(PlayJukebox, 1)

def PunchingBag(context, action, other_item, item_is_secondary):
    if action["key"] == "ATTACK":
        context.Print("You take some whacks at the punching bag. Ouch, that kind of hurt!")
        return True
    return False

def Flashlight(context, action, other_item, item_is_secondary):
    if action["key"] == "TURN_ON":
        if context.items["FLASHLIGHT"].get("light_source?"):
            context.Print("It's already on.")
        else:
            context.items["FLASHLIGHT"]["light_source?"] = True
            context.Print("You switch on the flashlight.")
        return True
    if action["key"] == "TURN_OFF":
        if context.items["FLASHLIGHT"].get("light_source?"):
            context.items["FLASHLIGHT"]["light_source?"] = False
            context.Print("You switch off the flashlight.")
        else:
            context.Print("It's already off.")
        return True
    if action["key"] == "EXAMINE":
        printstr = "The aluminum flashlight is surprisingly hefty, and is currently switched o"
        if context.items["FLASHLIGHT"].get("light_source?"):
            printstr += "n"
        else:
            printstr += "ff"
        context.Print(printstr + ".")
        return True
    return False

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    items = context.items
    items.AddItemHandler("COIN", Coin)
    items.AddItemHandler("JUKEBOX", Jukebox)
    items.AddItemHandler("KEYPAD", JukeboxKeypad)
    items.AddItemHandler("PUNCHING_BAG", PunchingBag)
    items.AddItemHandler("NUMBER", Number)
    items.AddItemHandler("FLASHLIGHT", Flashlight)