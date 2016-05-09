import json

import action_handlers
import globals
import item_handlers
import location_handlers

######################### CONTEXT #########################

# This class is a package of all of the major object containers which can easily be passed to action handlers
class Context:
    def __init__(self, player, locations, actions, items, state, events):
        self.player = player
        self.locations = locations
        self.actions = actions
        self.items = items
        self.state = state
        self.events = events

######################### PLAYER #########################

# This class contains player status information
class Player:
    def __init__(self):
        self.hp = 100
        self.inventory = []
        self.location = ""
        self.quit_requested = False

    def IsAlive(self):
        return self.hp > 0

    def SetPlayerLocation(self, new_location):
        self.location = new_location

    def GetPlayerLocation(self):
        return locations[self.location]

######################### GLOBAL CONDITIONS #########################

# This class is used to track various state variables and history
class State:
    def __init__(self):
        self.turn_counter = 0
        self.quit_confirmed = False
        self.quit_pending = False
        self.waiting_for_object = False
        self.this_action = None
        self.this_object = None
        self.last_action = None
        self.last_object = None
        self.this_user_input = None
        self.this_user_words = []
        self.last_user_input = None
        self.last_user_words = []
        self.parse_successful = False

    def ClearFlags(self):
        self.quit_pending = False
        self.waiting_for_object = False
        self.last_action = None
        self.last_object = None

    # This is called at the end of each turn; it remembers this period's user input and commands for recall next period
    def PostProcess(self):
        self.last_user_input = self.this_user_input
        self.last_user_words = self.this_user_words

        if self.parse_successful:
            if not self.waiting_for_object:
                events.CheckEvents(self.turn_counter)
                self.turn_counter += 1
            self.last_action = self.this_action
            self.last_object = self.this_object

######################### LOCATIONS #########################

# Master object container for locations
class LocationsMaster:
    # Constructor
    def __init__(self):
        with open('locations.json') as data_file:
            self.locations_dictionary = json.load(data_file)
        for loc_key in self.locations_dictionary:
            self.locations_dictionary[loc_key]["key"] = loc_key
            self.locations_dictionary[loc_key]["touched?"] = False
            self.locations_dictionary[loc_key]["items"] = []
            self.locations_dictionary[loc_key]["enter_handler"] = None
            self.locations_dictionary[loc_key]["when_here_handler"] = None

    # This allows you to type "locations[<key>]" for convenience
    def __getitem__(self, key): return self.locations_dictionary[key]

    # Add a function to trigger on entering this location
    def AddEnterHandler(self, loc_key, handler):
        self.locations_dictionary[loc_key]["enter_handler"] = handler

    # Add a function to run as a handler whenever the player is at this location
    def AddWhenHereHandler(self, loc_key, handler):
        self.locations_dictionary[loc_key]["when_here_handler"] = handler

    # This function handles a move in a certain direction.
    def HandleMove(self, direction):
        new_location_key = self.locations_dictionary[player.location].get(str.lower(direction))
        if (new_location_key != None) and (len(new_location_key) > 0):
            self.EnterRoom(new_location_key)
        else:
            print("You can't go in that direction.")

    # This function moves the player to a new location and prints room location
    def EnterRoom(self, new_location_key):
        new_location = self.locations_dictionary[new_location_key]
        first_time_here = not new_location["touched?"]
        enter_handler = new_location.get("enter_handler")
        if (enter_handler != None) and enter_handler(context, first_time_here):
            return True
        if not first_time_here:
            player.SetPlayerLocation(new_location_key)
            print(new_location["brief_desc"])
            if not self.IsDark():
                self.DescribeItemsInLocation()
        else:
            player.SetPlayerLocation(new_location_key)
            self.DoLook()

    # This function implements a LOOK action
    def DoLook(self):
        location = self.locations_dictionary[player.location]
        print(location["brief_desc"])
        if self.IsDark():
            print("It is pitch dark in here.")
        else:
            location["touched?"] = True
            print(location["long_desc"])
            self.DescribeItemsInLocation()

    # Describes all items in a particular location
    def DescribeItemsInLocation(self):
        location = self.locations_dictionary[player.location]
        first_item = True
        if len(location["items"]) > 0:
            for item_key in location["items"]:
                if items[item_key].get("do_not_list"):
                    continue
                if first_item:
                    print()
                    first_item = False
                print("There is a " + items.GetLongDescription(item_key) + " here.")

    # Is the current location dark (and is there no light source in the room or in player inventory?)
    def IsDark(self):
        player_loc = player.GetPlayerLocation()
        if not player_loc.get("dark?"):
            return False

        # Dark room ... need to check for light source in room or inventory
        for item_key in player_loc["items"]:
            item = items[item_key]
            if (item.get("light_source?")):
                return False

        for item_key in player.inventory:
            item = items[item_key]
            if (item.get("light_source?")):
                return False

        return True

######################### ACTIONS #########################

# Master object container for actions
class ActionsMaster:
    # Constructor
    def __init__(self):
        with open('actions.json') as data_file:
            self.actions_dictionary = json.load(data_file)
        for action_key in self.actions_dictionary:
            self.actions_dictionary[action_key]["key"] = action_key
            self.actions_dictionary[action_key]["handler"] = None

    # This allows you to type "actions[<key>]" for convenience
    def __getitem__(self, key): return self.actions_dictionary[key]

    # Add a function to handle an action
    def AddActionHandler(self, action_key, handler):
        self.actions_dictionary[action_key]["handler"] = handler

    # Parse the user's command (this is the first function called)
    def ParseCommand(self, command_string):
        state.this_user_input = command_string
        command_string = str.upper(command_string).replace("PICK UP", "GET").replace("L AT", "EXAMINE").replace(
            "LOOK AT", "EXAMINE").strip()
        command_words = command_string.split(' ')
        state.this_user_words = command_words

        if len(command_words) > 2:
            print("That sentence has too many words.")
            return

        if len(command_string) == 0:
            print("Eh?")
            return

        # Handle case where we're waiting to see if the user confirmed a QUIT (by typing Y or N)
        if state.quit_pending and (len(command_words) == 1):
            if (command_string == 'Y') or (command_string == 'YES'):
                print("Quitting...")
                state.quit_confirmed = True
                return
            if (command_string == 'N') or (command_string == 'NO'):
                print("Okay, Quit cancelled.")
                state.quit_pending = False
                return

        word_one_item = None
        for item_key in items.items_dictionary:
            if command_words[0] in items.items_dictionary[item_key]["words"]:
                word_one_item = item_key
                break

        # Handle case where we're waiting for the user to type in an item name (after 'what do you want to <action>?')
        if (word_one_item != None) and state.waiting_for_object:
            self.ParseCommand(state.last_action + " " + command_words[0])
            return

        for action_key in self.actions_dictionary:
            if command_words[0] in self.actions_dictionary[action_key]["words"]:
                self.ParseAction(action_key, command_words)
                return

        if word_one_item != None:
            print("I don't understand that command.")
            return

        print("I don't understand the word \"" + command_words[0] + "\".")

    # Once we know what action the user has typed, we continue parsing (this is the second parsing function called)
    def ParseAction(self, action_key, command_words):
        action = self.actions_dictionary[action_key]
        state.this_action = action_key
        state.waiting_for_object = False
        state.quit_pending = False

        # Handle one word command (e.g. inventory, north, etc)
        if len(command_words) == 1:

            #Handle 'AGAIN' command
            if action_key == "AGAIN":
                state.this_user_words = state.last_user_words
                state.this_user_input = state.last_user_input
                self.ParseAction(state.last_action, state.last_user_words)
                return

            state.this_object = None
            state.parse_successful = True
            if action.get("requires_object?"):
                if len(command_words[0]) == 1:
                    print("What do you want to " + str.lower(action["words"][0]) + "?")
                    state.waiting_for_object = True
                else:
                    print("What do you want to " + str.lower(command_words[0]) + "?")
                    state.waiting_for_object = True
                return
            location_handler = player.GetPlayerLocation()["when_here_handler"]
            if (location_handler != None) and location_handler(context, action, None):
                return
            elif not action["handler"] == None:
                action["handler"](context)
            elif action.get("is_move?"):
                locations.HandleMove(action_key)
            elif action_key == "LOOK":
                locations.DoLook()
            else:
                self.PrintActionDefault(action)
            return

        # Handle two word command (e.g. get sword)
        item = items.MatchStringToItem(command_words[1])
        if item == None:
            print("I don't understand the word \"" + command_words[1] + "\".")
            return
        state.last_object = item
        state.parse_successful = True
        if (not action.get("requires_object?")) or ((item["key"] == "ALL") and (not action.get("supports_all?"))):
            print("I don't understand that command.")
        elif not items.TestIfItemIsHere(item):
            return
        else:
            # First, test if there is a location handler for this location...
            location_handler = player.GetPlayerLocation()["when_here_handler"]
            if (location_handler != None) and location_handler(context, action, item):
                return

            # Next, test if there is an item handler for this action that handles the command...
            handler = item["handler"]
            if (not handler == None) and handler(context, action):
                return

            # ...and if not, check for an action handler
            if not action["handler"] == None:
                action["handler"](context, item)

            # If there is no item or action handler that covers this command, print the default result
            else:
                self.PrintActionDefault(action)

    # If we understand the action but the command wasn't handled anywhere else, print a default result.
    def PrintActionDefault(self, action):
        default_result = action.get("default_result")
        if default_result == None:
            print("You can't do that.")
        else:
            print(default_result)

######################### ITEMS #########################

# Master object container for items
class ItemsMaster:
    # Constructor
    def __init__(self):
        with open('items.json') as data_file:
            self.items_dictionary = json.load(data_file)
        for item_key in self.items_dictionary:
            self.items_dictionary[item_key]["key"] = item_key
            self.items_dictionary[item_key]["handler"] = None
            item_loc = self.items_dictionary[item_key].get("init_loc")
            if not item_loc == None:
                locations[item_loc]["items"].append(item_key)

    # This allows you to type "actions[<key>]" for convenience
    def __getitem__(self, key): return self.items_dictionary[key]

    def AddItemHandler(self, item_key, handler):
        self.items_dictionary[item_key]["handler"] = handler

    # Check dictionary for item string
    def MatchStringToItem(self, item_string):
        for item_key in self.items_dictionary:
            if item_string in self.items_dictionary[item_key]["words"]:
                return self.items_dictionary[item_key]

        # No match found
        return None

    # Returns true if the item is present (in inventory or in the room) and visible?
    def TestIfItemIsHere(self, item):
        if item["key"] == "ALL":
            return True
        if item["key"] in player.inventory:
            return True
        if locations.IsDark():
            self.YouCantSeeItemHere()
            return False
        if not item["key"] in player.GetPlayerLocation()["items"]:
            self.YouCantSeeItemHere()
            return False
        return True

    # Prints a warning that you can't see any such item at the moment
    def YouCantSeeItemHere(self):
        print("You can't see any " + str.lower(state.this_user_words[1]) + " here!")

    # Obtains a long description for the item (with backups if that field hasn't been specified in the locations file)
    def GetLongDescription(self, item_key):
        item = self.items_dictionary[item_key]
        item_desc = item.get("long_desc")
        if (item_desc == None) or (len(item_desc) == 0):
            return item["name"]
        else:
            return item_desc

    # Does a "get all"
    def GetAll(self):
        # Need to make a copy of the list of items to get first (because we're updating loc["items"] in the loop
        get_list = []
        for item_key in player.GetPlayerLocation()["items"]:
            get_list.append(item_key)

        taken_items = 0
        for item_key in get_list:
            if items[item_key].get("takeable?"):
                print(items[item_key]["name"].capitalize() + " : ", end='')
                self.GetItem(item_key)
                taken_items += 1

        if taken_items == 0:
            print("There is nothing here to take!")

    # Does a get on one item
    def GetItem(self, item_key):
        print("Taken.")
        player.GetPlayerLocation()["items"].remove(item_key)
        player.inventory.append(item_key)

    # Does a "drop all"
    def DropAll(self):
        # Need to make a copy of the list of items to drop first (because we're updating player.inventory in the loop
        drop_list = []
        for item_key in player.inventory:
            drop_list.append(item_key)

        if len(drop_list) == 0:
            print("You aren't carrying anything!")
            return

        for item_key in drop_list:
            print(items[item_key]["name"].capitalize() + " : ", end='')
            self.DropItem(item_key)

    # Does a drop on one item
    def DropItem(self, item_key):
        print("Dropped.")
        player.GetPlayerLocation()["items"].append(item_key)
        player.inventory.remove(item_key)

######################### EVENTS #########################

class Event:
    # Constructor
    def __init__(self, trigger_turn, event_func):
        self.trigger_turn = trigger_turn
        self.event_func = event_func

class EventsMaster:
    # Constructor
    def __init__(self):
        self.events = []

    # Each turn, we go through the event queue to see if any are supposed to trigger this turn.
    def CheckEvents(self, turn_counter):
        new_events = []
        for event in self.events:
            if event.trigger_turn == turn_counter:
                event.event_func(context)
            elif event.trigger_turn > turn_counter:
                new_events.append(event)
        self.events = new_events

    # Add an event to the queue, happening in n moves
    def CreateEventInNMoves(self, event_func, n):
        self.events.append(Event(state.turn_counter + n, event_func))

    # This is useful if you want to add a statement to the bottom of whatever will normally be printed.
    def PrintBelow(self, string):
        self.CreateEventInNMoves(lambda x: print("\n" + string), 0)

    # This adds a simple event in N moves which prints a string
    def PrintStringInNMoves(self, string, n):
        self.CreateEventInNMoves(lambda x: print("\n" + string), n)

######################### HELPER FUNCTIONS #########################

def PrintDefaultActionString(default_string, item):
    print(default_string.replace("@", "the " + item.get("name")))

######################### MAIN LOOP #########################

# Set up the master object containers and the context container
player = Player()
locations = LocationsMaster()
actions = ActionsMaster()
items = ItemsMaster()
events = EventsMaster()
state = State()
context = Context(player, locations, actions, items, state, events)
action_handlers.Register(context)
item_handlers.Register(context)
location_handlers.Register(context)

# Here is the MAIN LOOP
def Play():
    globals.IntroText()
    globals.InitialSetup(context)
    locations.DoLook()
    while not state.quit_confirmed:
        print()
        actions.ParseCommand(input("> "))
        state.PostProcess()

if __name__ == "__main__":
    Play()