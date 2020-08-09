### THIS FILE CONTAINS HANDLERS FOR YOUR LOCATIONS ###

# There are three types of location handlers:
#   * An "ENTER" HANDLER is called whenever the player enters that location.
#          The handler will be passed the context plus a flag which is true if this is the first
#           time the player has been here.
#   * A "WHEN HERE" HANDLER is called whenever the player does anything at that location
#          The handler will take four arguments: context, action, item1, and item2.
#          Note that some of these arguments may be None if the command is just an action
#            or an action with a single item
#   * A "LOOK" HANDLER is called whenever the player does a look at that location
#          The only parameter passed is context.

# For all types of location handlers, return TRUE to bypass the other handler logic that would otherwise run
#  ...and return FALSE if you want the regular handler logic to do its thing.

# To add a new location handler, first create a function for your item
#  and then "bind" the handler to your item in the bottom section of the file.
# When you bind, make sure you choose the right Add function, depending on whether
#  you are adding an enter handler, look handler, or when-here handler.

# NOTES ON LOCATIONS.JSON
#   * "brief_desc" = room title ("West of House")
#   * "long_desc" is the full description of the location that prints when you do a LOOK
#       -- note that you can create a LOOK handler for a more complicated description
#   * every direction (incl up/down and in/out) have optional string arguments, which can be...
#       - a location key (for simple movement) e.g. "FOREST_PATH"
#       - <location key>|<item key> (allows movement only if the item's "is_open?" flag = true)
#                                e.g. "KITCHEN|SIDE_WINDOW"
#       - a string description explaining why you can't go in that direction
#       [and you can always use a WHEN_HERE location handler to manage more complex moves]
#   * "dark?" = True if the room has no natural light source. (Can omit if false.)
#   * "touched?" = True if the player has seen the look description in this room (with light source)
#       - It's fine to check it, but PLEASE DON'T SET "touched?"!

def JukeboxSound(context):
    if not context.items["JUKEBOX"].get("song_choice"):
        if context.player.location == "DINER_INTERIOR":
            context.Print("\nSuddenly the jukebox comes to life, plays a loud chord amid a dazzle of lights, and then goes silent again.")
        else:
            context.Print("\nFrom inside the diner, you hear the jukebox come to life, play a loud chord, and then go silent again.")

def DinerEnter(context, first_time):
    if first_time:
        context.events.CreateEventInNMoves(JukeboxSound, 5)
        context.events.PrintBelow("As you enter, you notice flashing lights on the jukebox, as if it's trying to get your attention.")
    return False

def DinerWhenHere(context, action, item1, item2):
    if (action["key"] == "DANCE") and (context.items["JUKEBOX"].get("playing?")):
        if context.items["JUKEBOX"]["song_choice"] == "001":
            context.Print("Wow! You had forgotten how incredibly danceable Aha's brand of Scandinavian pop was! You are really getting down!")
        elif context.items["JUKEBOX"]["song_choice"] == "001":
            context.Print("Wow! You had forgotten how incredibly danceable Aha's brand of Scandinavian pop was! You are really getting down!")
        else:
            context.Print("You close your eyes and rock out to the music from the jukebox!")
        return true
    return False

def DinerLook(context):
    look_string = "You are inside the diner, a 2020 take on 1950s retro chic. The black and white tile floor is freshly polished, and red booths line the walls. A lunch counter with barstools separates the kitchen area from the main dining area. A door leads out to the street. A candyapple-red jukebox "
    if context.items["JUKEBOX"].get("playing?"):
        look_string += "against the wall is blaring music."
    else:
        look_string += "is gleaming silently against the far wall."
    context.Print(look_string)

# Here is where you "bind" your item handler function to a specific item.
def Register(context):
    locations = context.locations
    locations.AddEnterHandler("DINER_INTERIOR", DinerEnter)
    locations.AddWhenHereHandler("DINER_INTERIOR", DinerWhenHere)
    locations.AddLookHandler("DINER_INTERIOR", DinerLook)