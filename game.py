# This is the main file for Erik and Tom's text adventure.
# game.py contains all class definitions and core game logic.

# You probably don't need to modify this file unless you want to change something about the deep logic of the game

import json
import action_handlers
import globals
import item_handlers
import location_handlers
import textwrap

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

    def Print(self, print_string):
        strings = print_string.split('\n')
        for string in strings:
            print(textwrap.fill(string, 75))

    def PrintItemInString(self, default_string, item):
        self.Print(default_string.replace("@", "the " + item.get("name")))
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
        self.waiting_for_number= False
        self.waiting_for_second_object = False
        self.waiting_to_disambiguate_object = False
        self.waiting_to_disambiguate_second_object = False
        self.disambiguate_list = []
        self.this_action = None
        self.this_object = None
        self.this_second_object = None
        self.last_action = None
        self.last_object = None
        self.last_second_object = None
        self.this_user_input = None
        self.this_user_words = []
        self.last_user_input = None
        self.last_user_words = []
        self.parse_successful = False
        self.oops_index = None
        self.oops_words = None

    def ClearFlags(self):
        self.quit_pending = False
        self.waiting_for_object = False
        self.waiting_for_number = False
        self.waiting_for_second_object = False
        self.waiting_to_disambiguate_object = False
        self.waiting_to_disambiguate_second_object = False
        self.last_action = None
        self.last_object = None
        self.last_second_object = None

    # This is called at the end of each turn; it remembers this period's user input and commands for recall next period
    def PostProcess(self):
        if self.parse_successful:
            if (not self.waiting_for_object) and (not self.waiting_for_second_object) and (not self.waiting_to_disambiguate_object) and (not self.waiting_to_disambiguate_second_object) and (not self.waiting_for_number):
                events.CheckEvents(self.turn_counter)
                self.turn_counter += 1
            self.last_action = self.this_action
            self.last_object = self.this_object
            self.last_second_object = self.this_second_object
            self.last_user_input = self.this_user_input
            self.last_user_words = self.this_user_words
            self.oops_index = None
            self.oops_words = None

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
        
        # Test whether the location key in this location is a string description; if so, print it.
        if ' ' in new_location_key:
          Print(new_location_key)
        elif (new_location_key != None) and (len(new_location_key) > 0):
            self.EnterRoom(new_location_key)
        else:
            Print("You can't go in that direction.")

    # This function moves the player to a new location and prints room location
    def EnterRoom(self, new_location_key):
        new_location = self.locations_dictionary[new_location_key]
        first_time_here = not new_location["touched?"]
        enter_handler = new_location.get("enter_handler")
        if (enter_handler != None) and enter_handler(context, first_time_here):
            return True
        if not first_time_here:
            player.SetPlayerLocation(new_location_key)
            Print(new_location["brief_desc"])
            if not self.IsDark():
                self.DescribeItemsInLocation()
        else:
            player.SetPlayerLocation(new_location_key)
            self.DoLook()

    # This function implements a LOOK action
    def DoLook(self):
        location = self.locations_dictionary[player.location]
        Print(location["brief_desc"])
        if self.IsDark():
            Print("It is pitch dark in here.")
        else:
            location["touched?"] = True
            Print(location["long_desc"])
            self.DescribeItemsInLocation()

    # Describes all items in a particular location
    def DescribeItemsInLocation(self):
        location = self.locations_dictionary[player.location]
        first_item = True
        if len(location["items"]) > 0:
            for item_key in location["items"]:
                if items[item_key].get("do_not_list?"):
                    continue
                if first_item:
                    print()
                    first_item = False
                Print("There is a " + items.GetLongDescription(item_key) + " here.")

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
        self.all_prepositions = []
        self.all_actions = []
        for action_key in self.actions_dictionary:
            self.actions_dictionary[action_key]["key"] = action_key
            self.actions_dictionary[action_key]["handler"] = None

            for action in self.actions_dictionary[action_key]["words"]:
                if not action in self.all_actions:
                    self.all_actions.append(action)

            prepositions_list = self.actions_dictionary[action_key].get("prepositions")
            if prepositions_list != None:
              for preposition in prepositions_list:
                if not preposition in self.all_prepositions:
                  self.all_prepositions.append(preposition)

    # This allows you to type "actions[<key>]" for convenience
    def __getitem__(self, key): return self.actions_dictionary[key]

    # Add a function to handle an action
    def AddActionHandler(self, action_key, handler):
        self.actions_dictionary[action_key]["handler"] = handler

    # Is this word in the list of swears (defined in the globals)
    def CheckForSwear(self, word):
        if word in self.swear_words:
            Print(self.swear_response)
            return True
        return False

    # Did the player type an unknown word?
    def CheckForUnknownWords(self, command_words):
        for x in range(len(command_words)):
            word = command_words[x]
            if (not word in self.all_actions) and (not word in self.all_prepositions) and (not word in items.all_nouns) and (not word in items.all_adjectives) and (not word.isdigit()):
                Print("I don't understand the word \"" + word + "\".")
                state.oops_index = x
                oops_words = []
                for xx in range(len(command_words)):
                  if not x == xx:
                    oops_words.append(command_words[xx])
                state.oops_words = oops_words
                return True
        return False

    # It can be used to reference the object you mentioned in the last move
    def HandleIt(self, command_words):
        for x in range(len(command_words)):
            if (command_words[x] == "IT"):
                if len(state.last_user_words) > 1:
                    command_words[x] = state.last_object
                    state.this_user_words[x] = state.last_user_words[1]
                else:
                    Print("I don't understand what \"IT\" is referring to in that command.")
                    return False
        return True

    # Remove any references to adjectives in the command string
    def HandleAdjectives(self, command_words):
      unhandled_adjectives = []
      for item_key in items.items_dictionary:
        adjectives_list = items.items_dictionary[item_key].get("adjectives")
        if adjectives_list != None:
          for adjective in adjectives_list:
            indices = [i for i, x in enumerate(command_words) if x == adjective]
            for adj_index in indices:
              if (adj_index < len(command_words) - 1) and (command_words[adj_index+1] in items.items_dictionary[item_key]["words"]):
                # remove the adjective from the input words list
                del command_words[adj_index]

                #...and replace the word with the item's unique ID
                command_words[adj_index] = adjectives_list[0] + "_" + items.items_dictionary[item_key]["words"][0]

                #...and combine adjective+noun in the words list stored in state
                state.this_user_words.remove(adjective)
                state.this_user_words[adj_index] = adjective + " " + state.this_user_words[adj_index]
              elif not adjective in items.all_nouns:
                unhandled_adjectives.append(adjective)
      
      # Test for adjectives used on the wrong nouns
      for adjective in unhandled_adjectives:
        if adjective in command_words:
          if command_words.index(adjective) < len(command_words) - 1:
            for item_key in items.items_dictionary:
                if command_words[command_words.index(adjective)+1] in items.items_dictionary[item_key]["words"]:
                  Print("You can't see any " + str.lower(adjective) + " " + str.lower(command_words[command_words.index(adjective)+1]) + " here!")
                  return False
          Print("I don't understand that use of the word \"" + adjective + "\".")
          return False
    
      return True

    # If we are waiting for the user to disambiguate between several items, detect whether all command words are associated with one of the items
    def AttemptToDisambiguate(self, command_words):
        new_disambiguate_list = []
        for candidate_item in state.disambiguate_list:
            is_candidate = True
            item_words = []
            for item_word in items.items_dictionary[candidate_item]["words"]:
                item_words.append(item_word)
            adjectives = items.items_dictionary[candidate_item].get("adjectives")
            if not adjectives == None:
                item_words.extend(adjectives)
            for word in command_words:
                if not word in item_words:
                    is_candidate = False
                    break
            if is_candidate:
                new_disambiguate_list.append(candidate_item)
        return new_disambiguate_list

    # Parse the user's command (this is the first function called)
    def ParseCommand(self, command_string):
        state.this_user_input = command_string
        state.parse_successful = False
        command_string = str.upper(command_string).replace("PICK UP", "GET").replace("L AT", "EXAMINE").replace(
            "LOOK AT", "EXAMINE").strip()
        command_words = command_string.split(' ')

        for word in command_words:
            if self.CheckForSwear(word):
                return
                
        if self.CheckForUnknownWords(command_words):
            return

        if (command_words[0] == "OOPS") and (len(command_words)>1) and (not state.oops_index == None):
          new_command_words = []
          for word in state.oops_words:
            new_command_words.append(word)
          for x in range(len(command_words)-1):
              new_command_words.insert(state.oops_index + x, command_words[x+1])
          command_words = new_command_words

        if state.waiting_to_disambiguate_object:
            new_disambiguate_list = self.AttemptToDisambiguate(command_words)
            if len(new_disambiguate_list) == 1:
                command_words = state.last_user_words
                command_words[1] = items.items_dictionary[new_disambiguate_list[0]]["words"][0]
                adjectives = items.items_dictionary[new_disambiguate_list[0]].get("adjectives")
                if not adjectives is None:
                    command_words.insert(1, adjectives[0])
            state.this_user_input = " ".join(command_words)
            state.waiting_to_disambiguate_object = False

        if state.waiting_to_disambiguate_second_object:
            new_disambiguate_list = self.AttemptToDisambiguate(command_words)
            if len(new_disambiguate_list) == 1:
                command_words = state.last_user_words
                command_words[3] = items.items_dictionary[new_disambiguate_list[0]]["words"][0]
                adjectives = items.items_dictionary[new_disambiguate_list[0]].get("adjectives")
                if not adjectives is None:
                    command_words.insert(3, adjectives[0])
            state.this_user_input = " ".join(command_words)
            state.waiting_to_disambiguate_second_object = False

        state.this_user_words = []
        for word in command_words:
          state.this_user_words.append(word)

        if not self.HandleAdjectives(command_words):
          return

        if not self.HandleIt(command_words):
            return

        if len(command_words) > 4:
            Print("That sentence has too many words.")
            return

        if len(command_string) == 0:
            Print("Eh?")
            return

        # Handle case where we're waiting to see if the user confirmed a QUIT (by typing Y or N)
        if state.quit_pending and (len(command_words) == 1):
            if (command_string == 'Y') or (command_string == 'YES'):
                Print("Quitting...")
                state.quit_confirmed = True
                return
            if (command_string == 'N') or (command_string == 'NO'):
                Print("Okay, Quit cancelled.")
                state.quit_pending = False
                return

        if state.waiting_for_number and command_words[0].isdigit():
            self.ParseCommand(state.last_action + " " + command_words[0])
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
        if (word_one_item != None) and state.waiting_for_second_object:
            self.ParseCommand(state.last_user_input + " " + command_words[0])
            return

        if (len(command_words) > 2) and (not command_words[2] in self.all_prepositions):
            Print("I don't understand the word \"" + command_words[2] + "\" in that context.")
            return

        action_word = False
        for action_key in self.actions_dictionary:
            if command_words[0] in self.actions_dictionary[action_key]["words"]:
                #Handle 'AGAIN' command
                if action_key == "AGAIN":
                    if state.last_user_input == None:
                      Print("You haven't entered a command yet.")
                    else:
                      self.ParseCommand(state.last_user_input)
                    return
                
                action_word = True
                if len(command_words) <= 2:
                    self.ParseAction(action_key, command_words)
                    return
                prepositions = self.actions_dictionary[action_key].get("prepositions")
                if (not prepositions == None) and (command_words[2] in prepositions):
                    self.ParseAction(action_key, command_words)
                    return

        if action_word or (word_one_item != None):
            Print("I don't understand that command.")
            return

        Print("I don't understand the word \"" + command_words[0] + "\" in that context.")

    # For a given item word, figure out the item (if possible) that the user might be referring to.
    # (Note that the word will already have been modified by any adjectives the user provided.)
    # If no resolution is possible, we prompt the user and return None
    def ResolveItem(self, command_word, user_word, is_secondary_item):
        # If the word is a number, just return the number (as a string)
        if command_word.isdigit():
          return command_word

        item_candidates = items.MatchStringToItems(command_word)
        
        if len(item_candidates) == 0:
            Print("I don't understand the word \"" + command_word + "\" in that context.")
            return None
        if len(item_candidates) > 1:
            
            # First, see if we can resolve ambiguity based on which items are here and visible
            item_candidates_available = []
            for item_candidate in item_candidates:
                item = items.items_dictionary[item_candidate]
                if (item["key"] in player.inventory) or ((item["key"] in player.GetPlayerLocation()["items"]) and not locations.IsDark()):
                    item_candidates_available.append(item_candidate)
            if len(item_candidates_available) == 0:
                return item_candidates[0]
            if len(item_candidates_available) == 1:
                return item_candidates_available[0]

            query_string = "Which " + str.lower(user_word) + " do you mean:"
            for item_candidate in item_candidates_available:
                if item_candidate == item_candidates_available[len(item_candidates_available)-1]:
                    query_string += " or"
                query_string += " the " + items.items_dictionary[item_candidate]["name"]
                if (not item_candidate == item_candidates_available[len(item_candidates_available)-1]) and (len(item_candidates_available) > 2):
                    query_string += ","
            print(query_string + "?")
            state.disambiguate_list = []
            for item_candidate in item_candidates_available:
                 state.disambiguate_list.append(item_candidate)
            if is_secondary_item:
                state.parse_successful = True
                state.waiting_to_disambiguate_second_object = True
            else:
                state.parse_successful = True
                state.waiting_to_disambiguate_object = True
            return None

        return item_candidates[0]

    # Once we know what action the user has typed, we continue parsing (this is the second parsing function called)
    def ParseAction(self, action_key, command_words):
        action = self.actions_dictionary[action_key]
        state.this_action = action_key
        state.waiting_for_object = False
        state.waiting_for_number = False
        state.quit_pending = False

        # Handle one word command (e.g. inventory, north, etc)
        if len(command_words) == 1:
            state.this_object = None
            state.parse_successful = True
            if action.get("requires_object?") or action.get("requires_number?"):
                if len(command_words[0]) == 1:
                    Print("What do you want to " + str.lower(action["words"][0]) + "?")
                else:
                    Print("What do you want to " + str.lower(command_words[0]) + "?")
                
                if action.get("requires_object?"):
                  state.waiting_for_object = True
                else:
                  state.waiting_for_number = True
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

        # Handle standard two or four word command (e.g. get sword or insert coin in slot)
        # First word is action, second is item, third (optional) is preposition, fourth (optional) is secondary item
        item_key = self.ResolveItem(command_words[1], state.this_user_words[1], False)
        if item_key == None:
            return

        second_item_key = None
        if len(command_words) == 4:
            second_item_key = self.ResolveItem(command_words[3], state.this_user_words[3], True)
            if second_item_key == None:
                return
            if second_item_key.isdigit():
                Print("I don't understand that command.")
                return              

        if (item_key == "ALL") and (not action.get("supports_all?")):
            Print("I don't understand that command.")
            return

        if item_key == "NUMBER":
          items.items_dictionary["NUMBER"]["user_value"] = ""

        if item_key.isdigit():
          if not action.get("requires_number?"):
            Print("I don't understand that command.")
            return
          items.items_dictionary["NUMBER"]["user_value"] = item_key
          item_key = "NUMBER"
        elif not action.get("requires_object?"):
            Print("I don't understand that command.")
            return

        state.parse_successful = True
        state.this_object = item_key
        item = items.items_dictionary[item_key]
        if second_item_key == None:
            second_item = None
        else:
            second_item = items.items_dictionary[second_item_key]

        if not items.TestIfItemIsHere(item, state.this_user_words[1]):
            return
        if (not second_item_key == None) and (not items.TestIfItemIsHere(second_item, state.this_user_words[3])):
            return

        # Okay, at this point we have a good-looking multi-word command.
        # We recognize all words and any items references are visible.

        # First, test if there is a location handler for this location...
        location_handler = player.GetPlayerLocation()["when_here_handler"]
        if (location_handler != None) and location_handler(context, action, item, second_item):
            return

        # Next, test if there is an item handler for this item that handles the command...
        handler = item["handler"]
        if (not handler == None) and handler(context, action, second_item, False):
            return

        # Next, test if there is an item handler for the secondary item that handles the command...
        if not second_item_key == None:
            handler = second_item["handler"]
            if (not handler == None) and handler(context, action, item, True):
                return

        # ...and if not, check for an action handler
        if not action["handler"] == None:
            if action.get("prepositions") == None:
                action["handler"](context, item)
            else:
                action["handler"](context, item, second_item)

        # If there is no item or action handler that covers this command, print the default result
        else:
            self.PrintActionDefault(action)

    # If we understand the action but the command wasn't handled anywhere else, print a default result.
    def PrintActionDefault(self, action):
        default_result = action.get("default_result")
        if default_result == None:
            Print("You can't do that.")
        else:
            Print(default_result)

######################### ITEMS #########################

# Master object container for items
class ItemsMaster:
    # Constructor
    def __init__(self):
        self.all_adjectives = []
        self.all_nouns = []
        
        with open('items.json') as data_file:
            self.items_dictionary = json.load(data_file)
        for item_key in self.items_dictionary:
            adjectives_list = self.items_dictionary[item_key].get("adjectives")
            if adjectives_list != None:
              # If adjectives are defined, we add a unique identifier to words list (combine first adj + first noun)
              #  This is for situations where there's a red button, a blue button, etc.
              self.items_dictionary[item_key]["words"].append(adjectives_list[0] + "_" + self.items_dictionary[item_key]["words"][0])
              for adjective in adjectives_list:
                if not adjective in self.all_adjectives:
                  self.all_adjectives.append(adjective)
            for word in self.items_dictionary[item_key]["words"]:
              if not word in self.all_nouns:
                self.all_nouns.append(word)
            self.items_dictionary[item_key]["key"] = item_key
            self.items_dictionary[item_key]["handler"] = None

            # Place item in location(s)
            item_loc = self.items_dictionary[item_key].get("init_loc")
            if item_loc == "PLAYER":
              player.inventory.append(item_key)
            elif not item_loc == None:
              if isinstance(item_loc, str):
                locations[item_loc]["items"].append(item_key)
              elif isinstance(item_loc, list):
                if self.items_dictionary[item_key].get("takeable?") and (len(item_loc) > 1):
                  print("ERROR: takeable items can't have multiple init_loc")
                for il in item_loc:
                  locations[il]["items"].append(item_key)

    # This allows you to type "actions[<key>]" for convenience
    def __getitem__(self, key): return self.items_dictionary[key]

    def AddItemHandler(self, item_key, handler):
        self.items_dictionary[item_key]["handler"] = handler

    # Check dictionary for item string
    def MatchStringToItems(self, item_string):
        items_list = []
        for item_key in self.items_dictionary:
            if item_string in self.items_dictionary[item_key]["words"]:
                items_list.append(item_key)
        return items_list

    # Returns true if the item is present (in inventory or in the room) and visible?
    def TestIfItemIsHere(self, item, word):
        if (item["key"] == "ALL") or (item["key"] == "NUMBER"):
            return True
        if item["key"] in player.inventory:
            return True
        if locations.IsDark():
            self.YouCantSeeItemHere(word)
            return False
        if not item["key"] in player.GetPlayerLocation()["items"]:
            self.YouCantSeeItemHere(word)
            return False
        return True

    # Prints a warning that you can't see any such item at the moment
    def YouCantSeeItemHere(self, word):
        Print("You can't see any " + str.lower(word) + " here!")

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
            Print("There is nothing here to take!")

    # Does a get on one item
    def GetItem(self, item_key):
        Print("Taken.")
        player.GetPlayerLocation()["items"].remove(item_key)
        player.inventory.append(item_key)

    # Does a "drop all"
    def DropAll(self):
        # Need to make a copy of the list of items to drop first (because we're updating player.inventory in the loop
        drop_list = []
        for item_key in player.inventory:
            drop_list.append(item_key)

        if len(drop_list) == 0:
            Print("You aren't carrying anything!")
            return

        for item_key in drop_list:
            print(items[item_key]["name"].capitalize() + " : ", end='')
            self.DropItem(item_key)

    # Does a drop on one item
    def DropItem(self, item_key):
        Print("Dropped.")
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
        self.CreateEventInNMoves(lambda x: Print("\n" + string), 0)

    # This adds a simple event in N moves which prints a string
    def PrintStringInNMoves(self, string, n):
        self.CreateEventInNMoves(lambda x: Print("\n" + string), n)

######################### HELPER FUNCTIONS #########################

def Print(string):
    context.Print(string)

def PrintItemInString(default_string, item):
    context.PrintItemInString(default_string, item)

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
    globals.IntroText(context)
    globals.InitialSetup(context)
    locations.DoLook()
    while not state.quit_confirmed:
        print()
        actions.ParseCommand(input("> "))
        state.PostProcess()

if __name__ == "__main__":
    Play()