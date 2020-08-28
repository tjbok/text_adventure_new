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
        default_string = default_string.replace("@", "the " + item.get("name"))
        if default_string.startswith("the"):
            default_string = "T" + default_string[1:]
        self.Print(default_string)



######################### TOKEN #########################

# This class contains token information (for parsed tokens)
class Token:
    def __init__(self, token_type, token_key, token_user_words):
        self.type = token_type
        self.key = token_key
        self.user_words = token_user_words

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

    def Kill(self, death_text = "*** YOU HAVE DIED! ***"):
        if death_text:
            Print("\n" + death_text)
        Print("")
        Print("Do you want to restart (Y/N)?")
        state.restart_pending = True
        self.hp = 0

######################### GLOBAL CONDITIONS #########################

# This class is used to track various state variables and history
class State:
    def __init__(self):
        self.turn_counter = 0
        self.quit_confirmed = False
        self.quit_pending = False
        self.restart_confirmed = False
        self.restart_pending = False
        self.waiting_for_item = False
        self.disambiguate_list = []
        self.this_parsed_command = []
        self.last_parsed_command = []
        self.this_user_input = None
        self.last_user_input = None
        self.parse_successful = False
        self.oops_index = None
        self.oops_words = None
        self.debug = False

    def ClearPending(self):
        self.quit_pending = False
        self.restart_pending = False
        self.waiting_for_item = False
        self.disambiguate_list = []
        self.this_parsed_command = []
        self.this_user_input = None
        self.oops_index = None
        self.oops_words = None       

    # This is called at the end of each turn; it remembers this period's user input and commands for recall next period
    def PostProcess(self):
        if self.parse_successful:
            events.CheckEvents(self.turn_counter)
            self.turn_counter += 1
            self.last_parsed_command = self.this_parsed_command
            self.last_user_input = self.this_user_input
            self.oops_index = None
            self.oops_words = None
            self.waiting_for_item = False
            self.disambiguate_list = []

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
        self[loc_key]["enter_handler"] = handler

    # Add a function to run as a handler whenever the player is at this location
    def AddWhenHereHandler(self, loc_key, handler):
        self[loc_key]["when_here_handler"] = handler

    # Add a function to run as a handler whenever the player is at this location
    def AddLookHandler(self, loc_key, handler):
        self[loc_key]["look_handler"] = handler

    # This function handles a move in a certain direction.
    def HandleMove(self, direction):
        new_location_key = self[player.location].get(str.lower(direction))
        
        # Test whether the location key in this location is a string description; if so, print it.
        if ' ' in new_location_key:
          Print(new_location_key)
        
        # Test for a door (denoted with the "LOCATION|DOOR" notation)
        if '|' in new_location_key:
            new_loc_array = new_location_key.split('|')
            if not items[new_loc_array[1]].get("is_open?"):
                Print("The " + items[new_loc_array[1]].get("name") + " is closed.")
            else:
                self.EnterRoom(new_loc_array[0])
       
        elif self.IsDark() and ((new_location_key == None) or (len(new_location_key) == 0) or not locations[new_location_key].get("touched?")):
            Print("It's hard to tell in the dark if it's possible to move in that location.")

        elif (new_location_key != None) and (len(new_location_key) > 0):
            self.EnterRoom(new_location_key)
        else:
            Print("You can't go in that direction.")

    # This function moves the player to a new location and prints room location
    def EnterRoom(self, new_location_key):
        new_location = self[new_location_key]
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
        location = self[player.location]
        Print(location["brief_desc"])
        if self.IsDark():
            Print("It is pitch dark in here.")
        else:
            location["touched?"] = True
            look_handler = locations[player.location].get("look_handler")
            if look_handler:
                look_handler(context)
            else:
                Print(location["long_desc"])
            self.DescribeItemsInLocation()

    # Describes all items in a particular location
    def DescribeItemsInLocation(self):
        items.ListItems(self[player.location]["items"], decorate = "There is @ here.", article = "a", indent = 0, blank_line = True, announce_if_nothing = False)

    # Is the current location dark (and is there no light source in the room or in player inventory?)
    def IsDark(self):
        player_loc = player.GetPlayerLocation()
        if not player_loc.get("dark?"):
            return False

        # Dark room ... need to check for light source in room or inventory
        for item_key in items.ListItemsPresent():
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
        self[action_key]["handler"] = handler

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
            if (not word in self.all_actions) and (not word in self.all_prepositions) and (not word in items.all_nouns) and (not word in items.all_adjectives) and (not word.isdigit()) and (not word in ["GO","THE","A"]):
                Print("I don't understand the word \"" + word + "\".")
                state.oops_index = x
                oops_words = []
                for xx in range(len(command_words)):
                  if not x == xx:
                    oops_words.append(command_words[xx])
                state.oops_words = oops_words
                return True
        return False

    # Given a list of words, attempt to resolve to a single item in the game. Complain and return None if this is impossible.
    def ParseItem(self, command_substring):
        if state.debug:
            print("Parse Item: " + ' '.join(command_substring))
        
        command_substring = [x for x in command_substring if not x in["THE","A"]]
        if command_substring == []:
            Print("I don't understand that command.")
            return None
        
        # Handle "IT"
        if (len(command_substring) == 1) and (command_substring[0] == "IT"):
            if (len(state.last_parsed_command) > 1) and (not state.last_parsed_command[1] == None):
                return state.last_parsed_command[1]
            else:
                Print("I don't understand what \"IT\" is referring to in that command.")
                return None

        # Handle "ALL"
        if (len(command_substring) == 1) and (command_substring[0] == "ALL"):
            return Token("Item","ALL",["ALL"])

        # Handle numbers
        if (len(command_substring) == 1) and (command_substring[0].isdigit()):
            return Token("Item","NUMBER",[command_substring[0]])

        # First, find all possible item matches for these command words
        item_candidates = []

        # If we are waiting on the player to disambiguate between several items, narrow the search universe to just those items
        item_universe = items.items_dictionary
        if len(state.disambiguate_list) > 0:
            item_universe = state.disambiguate_list

        for item_key in item_universe:
            mismatch = False
            for word in command_substring:
                if (not word in items[item_key]["words"]) and ((not items[item_key].get("adjectives")) or (not word in items[item_key]["adjectives"])):
                    mismatch = True
                    break
            if not mismatch:
                item_candidates.append(item_key)

        if len(item_candidates) == 0:
            Print("I don't understand that command.")
            return None

        if len(item_candidates) == 1:
            # Success!
            return Token("Item",item_candidates[0],command_substring)
        
        # Need to disambiguate. Start by narrowing the candidates to items that are here.
        item_candidates_here = []
        for item_candidate in item_candidates:
            if items.TestIfItemIsIn(item_candidate, player.inventory) or ((not locations.IsDark()) and items.TestIfItemIsIn(item_candidate, player.GetPlayerLocation()["items"])):
                item_candidates_here.append(item_candidate)
        
        if len(item_candidates_here) == 1:
            # Success!
            return Token("Item",item_candidates_here[0],command_substring)

        if len(item_candidates_here) == 0:
            # Player has mentioned several items but none are here. Pick the first candidate and let the ParseAction() function deal with it
            return Token("Item",item_candidates[0],command_substring)

        # Finally, see if we can narrow the list by ignoring items that were only matched to an adjective
        item_candidates_here_nounsonly = []
        for item_candidate in item_candidates_here:
            for word in command_substring:
                if word in items[item_candidate]["words"]:
                    item_candidates_here_nounsonly.append(item_candidate)
                    break
        
        if len(item_candidates_here_nounsonly) == 1:
            # Success!
            return Token("Item",item_candidates_here_nounsonly[0],command_substring)

        if len(item_candidates_here_nounsonly) > 1:
            item_candidates_here = item_candidates_here_nounsonly

        query_string = "Which " + str.lower(' '.join(command_substring)) + " do you mean:"
        for item_candidate in item_candidates_here:
            if item_candidate == item_candidates_here[len(item_candidates_here)-1]:
                query_string += " or"
            query_string += " the " + items[item_candidate]["name"]
            if (not item_candidate == item_candidates_here[len(item_candidates_here)-1]) and (len(item_candidates_here) > 2):
                query_string += ","
        Print(query_string + "?")
        state.disambiguate_list = []
        for item_candidate in item_candidates_here:
                state.disambiguate_list.append(item_candidate)
        
        state.waiting_for_item = True
        return None
    
    # Here is the main command parser function. You pass in a string and it parses it into known tokens and then reacts to them.
    def ParseCommand(self, command_string):
        state.this_user_input = command_string
        state.parse_successful = False
        command_string = str.upper(command_string).strip()
        command_words = command_string.split(' ')

        for word in command_words:
            if self.CheckForSwear(word):
                return
        
        if len(command_string) == 0:
            Print("Eh?")
            return
            
        if self.CheckForUnknownWords(command_words):
            return

        # Handle OOPS
        if (command_words[0] == "OOPS"):
            if (len(command_words)>1) and (not state.oops_index == None):
                new_command_words = []
                for word in state.oops_words:
                    new_command_words.append(word)
                for x in range(len(command_words)-1):
                    new_command_words.insert(state.oops_index + x, command_words[x+1])
                command_words = new_command_words
            else:
                Print("You can use 'OOPS' to correct typing mistakes. Just type 'OOPS' and then the word you meant to type.")
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

        # Handle case where we're waiting to see if the user confirmed a RESTART (by typing Y or N)
        if state.restart_pending and (len(command_words) == 1):
            if (command_string == 'Y') or (command_string == 'YES'):
                Print("Restarting...\n\n")
                state.restart_confirmed = True
                return
            if (command_string == 'N') or (command_string == 'NO'):
                if (player.hp <= 0):
                    Print("Quitting...")
                    state.quit_confirmed = True
                else:
                    Print("Okay, Restart cancelled.")
                    state.restart_pending = False
                return

        if player.hp <= 0:
            Print("You can't do that on account of the fact that you're dead.")
            player.Kill("")
            return

        # Basically just ignore "GO" (e.g. "GO NORTH" or "GO INSIDE")
        if command_words[0] == "GO":
            if len(command_words) == 1:
                Print("Where would you like to go?")
                return
            del command_words[0]

        # Locate prepositions in the command (if any)
        preposition_index = -1
        preps_found = 0
        for x in range(len(command_words)):
            if command_words[x] in self.all_prepositions:
                # If a preposition is also a command, then assume it's being used as a command if it's the first word
                #  Example: 'IN' vs 'PUT COIN IN SLOT'
                if (x == 0) and (command_words[x] in self.all_actions):
                    continue
                preposition_index = x
                preps_found = preps_found + 1
        if preps_found > 1:
            Print("There were too many prepositions in that command.")
            return

        # Check if first word is an action (the usual type of command)
        action_matches = []
        for action_key in self.actions_dictionary:
            if command_words[0] in self[action_key]["words"]:
                action_matches.append(action_key)

        if len(action_matches) > 0:

            # First word matches at least one action ... may need to disambiguate using prepositions
            final_action_matches = []

            for potential_match in action_matches:
                if preps_found and ((not self[potential_match].get("prepositions")) or (not command_words[preposition_index] in self[potential_match].get("prepositions"))):
                    continue
                if (not preps_found) and (self[potential_match].get("prepositions")):
                    continue
                # Action matched against both action words and prepositions (if any)
                final_action_matches.append(potential_match)

            if len(final_action_matches) == 0:
                # Did player type in a preposition that doesn't match this verb?
                if preps_found > 0:
                    Print("I don't understand that command.")
                    return
                
                # ... or did player just fail to type in a preposition at all ... then assume preposition and proceed
                final_action_matches.append(action_matches[0])
            
            # We assume that the player's action can't be ambiguous at this point
            # If it is ambiguous, then there are two actions with the same words and matching prepositions (not allowed)
            # Just in case, we set the action to the first matched action.
            action_key = final_action_matches[0]

            user_action_words = [command_words[0]]
            if preps_found:
                user_action_words.append(command_words[preposition_index])
            state.ClearPending()
            state.this_parsed_command = [Token("Action", action_key, user_action_words)]

            # Handle actions that mimic other actions
            mimic_action = self[action_key].get("mimic")
            if mimic_action:
                if state.debug:
                    Print("MIMIC action detected")
                state.this_parsed_command[0].key = mimic_action
            
            if preps_found:
                # Handle case with one object, e.g. TURN ON FLASHLIGHT
                if self[action_key].get("no_second_item?"):
                    user_item_words = []
                    for x in range(1,len(command_words)):
                        if not x == preposition_index:
                            user_item_words.append(command_words[x])
                    if len(user_item_words) > 0:
                        state.this_parsed_command.append(self.ParseItem(user_item_words))
                
                # Handle case with two objects, e.g. PUT X IN Y
                else:
                                     
                    # Can't have preposition right after action or last word in command
                    if (preposition_index < 2) or (preposition_index == len(command_words) - 1):
                        
                        Print("I don't understand that command.")
                        return
                    
                    # Add tokens to parsed_command for objects on either side of the preposition:
                    state.this_parsed_command.append(self.ParseItem(command_words[1:preposition_index]))
                    if not state.this_parsed_command[1] == None:
                        state.this_parsed_command.append(self.ParseItem(command_words[preposition_index+1:]))

            elif len(command_words) > 1:
                state.this_parsed_command.append(self.ParseItem(command_words[1:]))

            for this_token in state.this_parsed_command:
                if not this_token:
                    return

        elif state.waiting_for_item:
            # First word was not an action.
            # If we reach this point in the code, there are only three valid possibilities:
            #  (1) We have prompted the player to disambiguate between several items by typing in a more specific item
            #  (2) We have prompted the player to type in an object ("what do you want to attack?")
            #  (3) We have prompted the player to type in a number

            # In all three cases, we will parse the command as an item and then attempt to put it into the right spot in the previous parsed command
            new_token = self.ParseItem(command_words)
            if not new_token:
                return
            action_key = state.this_parsed_command[0].key
            if len(state.this_parsed_command) == 1:
                state.this_parsed_command.append(new_token)
            elif state.this_parsed_command[1] == None:
                state.this_parsed_command[1] = new_token
                if (len(state.this_parsed_command) == 3) and state.this_parsed_command[2] == None:
                    del state.this_parsed_command[-1]
            elif len(state.this_parsed_command) == 2:
                state.this_parsed_command.append(new_token)
            else:
                state.this_parsed_command[2] = new_token

        else:
            Print("I don't understand that command.")
            return

        # Check for incomplete commands, like "OPEN" or "PUT COIN", and prompt for more words if necessary
        if actions[action_key].get("requires_object?") and (len(state.this_parsed_command) == 1):
            prompt_string = "What do you want to " + state.this_parsed_command[0].user_words[0].lower()
            if actions[action_key].get("no_second_item?"):
                if preps_found:
                    prompt_string += " " + command_words[preposition_index].lower()
                elif actions[action_key].get("prepositions"):
                    prompt_string += " " + actions[action_key]["prepositions"][0].lower()
            Print(prompt_string + "?")
            state.waiting_for_item = True
        elif actions[action_key].get("prepositions") and (not actions[action_key].get("no_second_item?")) and len(state.this_parsed_command) < 3:
            prompt_string = "What do you want to " + state.this_parsed_command[0].user_words[0].lower()
            if not items[state.this_parsed_command[1].key].get("no_article?"):
                prompt_string += " the"
            prompt_string += " " + ' '.join(state.this_parsed_command[1].user_words).lower() + " "
            if len(state.this_parsed_command[0].user_words) == 2:
                prompt_string += state.this_parsed_command[0].user_words[1].lower()
            else:
                prompt_string += actions[action_key]["prepositions"][0].lower()
            Print(prompt_string + "?")    
            state.waiting_for_item = True
        else:
            # Successful parse!

            # Handle AGAIN
            if (action_key == "AGAIN") and (len(state.this_parsed_command) == 1):
                if not state.last_parsed_command:
                    Print("You can't type 'AGAIN' before doing something.")
                    return
                state.this_parsed_command = []
                for t in state.last_parsed_command:
                    state.this_parsed_command.append(t)

            self.ParseAction(state.this_parsed_command)

    # Once we have parsed the command into tokens with at least one action, we continue to parse...
    def ParseAction(self, parsed_command):
        
        state.parse_successful = True
        # (setting this flag means that this command is considered parsed and counts as a player turn)

        # Obtain objects for action and items (if any) and make sure any referenced items are present
        action = self[parsed_command[0].key]
        if state.debug:
            print("ACTION: " + action["key"])
        item1 = None
        if len(parsed_command) > 1:
            if not action.get("requires_object?"):
                Print("I don't understand that command.")
                return
            item1 = items[parsed_command[1].key]
            if state.debug:
                print("ITEM1: " + item1["key"])
            if not items.TestIfItemIsHere(item1):
                items.YouCantSeeItemHere(' '.join(parsed_command[1].user_words))
                return
            if (item1["key"] == "ALL") and not action.get("supports_all?"):
                self.PrintActionDefault(action)
                return
        item2 = None
        if len(parsed_command) > 2:
            item2 = items[parsed_command[2].key]
            if state.debug:
                print("ITEM2: " + item2["key"])
            if not items.TestIfItemIsHere(item2):
                items.YouCantSeeItemHere(' '.join(parsed_command[2].user_words))
                return
            if item2["key"] == "ALL":
                self.PrintActionDefault(action)
                return

        # Check location handler
        location_handler = player.GetPlayerLocation().get("when_here_handler")
        if location_handler and location_handler(context, action, item1, item2):
            return

        # Handle 1-word commands
        if len(parsed_command) == 1:
            if not action["handler"] == None:
                action["handler"](context)
            elif action.get("is_move?"):
                locations.HandleMove(action["key"])
            elif action["key"] == "LOOK":
                locations.DoLook()
            else:
                self.PrintActionDefault(action)
            return

        # Next, test if there is an item handler for this item that handles the command...
        handler = item1["handler"]
        if (not handler == None) and handler(context, action, item2, False):
            return

        # Next, test if there is an item handler for the secondary item that handles the command...
        if not item2 == None:
            handler = item2["handler"]
            if (not handler == None) and handler(context, action, item1, True):
                return

        # ...and if not, check for an action handler
        if not action["handler"] == None:
            if action.get("prepositions") and (not action.get("no_second_item?")):
                action["handler"](context, item1, item2)
            else:
                action["handler"](context, item1)

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
            self.items_dictionary[item_key]["contents"] = []
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
            if isinstance(item_loc, str):
                self.PlaceItemIn(item_key, item_loc)
            elif isinstance(item_loc, list):
                if self.items_dictionary[item_key].get("takeable?") and (len(item_loc) > 1):
                  print("ERROR: takeable items can't have multiple init_loc")
                for il in item_loc:
                  self.PlaceItemIn(item_key, il)

    # This allows you to type "actions[<key>]" for convenience
    def __getitem__(self, key): return self.items_dictionary[key]

    def AddItemHandler(self, item_key, handler):
        self[item_key]["handler"] = handler

    # Returns the key of an item, checking first to see if the item is already a key
    # Point of this is to make it easy to create helper functions that take an item
    #  as a parameter and allow you to pass in either the item or the item's key
    def ItemKey(self, item):
        if isinstance(item,str):
            return item
        else:
            return item["key"]

    # return list of string keys of items that are available here (in inventory or in room, including open containers)
    def ListItemsPresent(self):
        items_present = []
        for item in player.inventory:
            items_present.append(item)
        for item in player.GetPlayerLocation()["items"]:
            items_present.append(item)
        return self.FindItemsInside(items_present)
    
    # appends the item contents to the end of the item description
    def AppendItemContentsToDescription(self, item_string, item_key, indent):
        item = self[item_key]
        if item.get("is_container?") and (not item.get("openable?") or item.get("is_open?")):
            if item_string[len(item_string)-1] == '.':
                item_string += " It"
            else:
                item_string += ", which"
            if len(item["contents"]) == 0:
                context.Print(item_string + " is empty")
            else:
                context.Print(item_string + " contains:")
                self.ListItems(item["contents"], indent=indent+2)
        else:
            context.Print(item_string)    

    # List a set of items, passed in by key (e.g. player inventory), including container contents
    def ListItems(self, item_list, decorate = "@", article = "a", indent = 0, blank_line = False, announce_if_nothing = True):
        if (len(item_list) == 0) and announce_if_nothing:
            Print(' ' * indent + "Nothing")
        else:
            first_item = True
            if decorate == "":
                decorate = "@"
            decorate = decorate.split('@')
            
            for item_key in item_list:
                if self[item_key].get("do_not_list?"):
                    continue
                if first_item:
                    if blank_line:
                        print()
                    first_item = False
                item_string = ' ' * indent + decorate[0] + self.GetLongDescription(item_key, article) + decorate[1]
                self.AppendItemContentsToDescription(item_string, item_key, indent)

    # return list of string keys of items in the passed-in list along with any other items contained in these items
    def FindItemsInside(self, items_list):
        return_list = items_list
        for item in items_list:
            if self[item].get("is_open?"):
                for item_inside in self[item]["contents"]:
                    return_list.append(item_inside)
        return return_list

    # is this item in the list of item keys (looking into containers)
    def TestIfItemIsIn(self, item, container, container_must_be_open = True):
        item_key = self.ItemKey(item)
        container_contents = []
        if isinstance(container, list):
            container_contents = container
        else:
            container_key = self.ItemKey(container)
            contents = self[container_key].get("contents")
            if contents:
                container_contents = contents

        if item_key in container_contents:
            return True
        for item in container_contents:
            if self.TestIfItemIsIn(item_key, self[item]["contents"]) and ((not container_must_be_open) or self[item].get("is_open?")):
                return True            
        return False

    # Returns true if the item is present (in inventory or in the room) and visible?
    def TestIfItemIsHere(self, item):
        item_key = self.ItemKey(item)
        if (item_key == "ALL") or (item_key == "NUMBER"):
            return True
        if self.TestIfItemIsIn(item_key, player.inventory):
            return True
        if locations.IsDark() or (not self.TestIfItemIsIn(item_key, player.GetPlayerLocation()["items"])):
            return False
        return True

    # Prints a warning that you can't see any such item at the moment
    def YouCantSeeItemHere(self, word):
        Print("You can't see any " + str.lower(word) + " here!")

    # Obtains a long description for the item (with backups if that field hasn't been specified in the locations file)
    def GetLongDescription(self, item, article = ""):
        item_key = self.ItemKey(item)
        item = self[item_key]
        item_desc = item.get("long_desc")
        if (item_desc == None) or (len(item_desc) == 0):
            item_desc = item["name"]

        # Add article (a, the), if requested
        if len(article) > 0:
            starts_with_vowel = (item_desc[0] in "aeiou")
            if not article[len(article)-1] == ' ':
                item_desc = " " + item_desc
            if (article in ["a","A"]) and starts_with_vowel:
                item_desc = "n" + item_desc
            item_desc = article + item_desc
            
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

    # Does a "get all from"
    def GetAllFrom(self, container):
        container_key = self.ItemKey(container)

        # Is this a container?
        if (not self[container_key].get("is_container?")) and (not self[container_key].get("contents")):
            Print("You can't do that.")
            return

        # Need to make a copy of the list of items to get first (because we're updating loc["items"] in the loop
        get_list = []
        for item_key in self[container_key]["contents"]:
            get_list.append(item_key)

        taken_items = 0
        for item_key in get_list:
            if self[item_key].get("takeable?"):
                print(self[item_key]["name"].capitalize() + " : ", end='')
                self.GetItem(item_key)
                taken_items += 1

        if taken_items == 0:
            Print("There is nothing inside to take!")

    # Does a get on one item
    def GetItem(self, item):
        item_key = self.ItemKey(item)
        Print("Taken.")
        if item_key in player.GetPlayerLocation()["items"]:
            player.GetPlayerLocation()["items"].remove(item_key)
        else:
            for container_key in self.items_dictionary:
                if item_key in self[container_key]["contents"]:
                    self[container_key]["contents"].remove(item_key)
                    
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

    def PutAllIn(self, container):
        container_key = self.ItemKey(container)

        if self[container_key].get("openable?") and not self[container_key].get("is_open?"):
            context.PrintItemInString("The @ is closed.", self[container_key])
            return

        # Need to make a copy of the list of items to put first (because we're updating player.inventory in the loop
        put_list = []
        for item_key in player.inventory:
            if (not item_key == container_key) and (not self.TestIfItemIsIn(container_key, item_key)):
                put_list.append(item_key)

        if len(put_list) == 0:
            print_str = "You aren't carrying anything"
            if len(player.inventory) >= 1:
                print_str += " that you can place in the pack"
            Print(print_str + "!")
            return

        for item_key in put_list:
            print(items[item_key]["name"].capitalize() + " : Done.")
            self.MoveItemTo(item_key, container_key)

    # Does a drop on one item
    def DropItem(self, item):
        item_key = self.ItemKey(item)
        Print("Dropped.")
        player.GetPlayerLocation()["items"].append(item_key)
        player.inventory.remove(item_key)

    # Removes an item from the game (can always be re-added to inventory or a location or container)
    def RemoveItemFromGame(self, item):
        item_key = self.ItemKey(item)
        if item_key in player.inventory:
            player.inventory.remove(item_key)
        for container_key in self.items_dictionary:
            contents = self[container_key].get("contents")
            if contents and (item_key in contents):
                self[container_key]["contents"].remove(item_key)
        for location_key in locations.locations_dictionary:
            contents = locations.locations_dictionary[location_key].get("items")
            if contents and (item_key in contents):
                self[location_key]["items"].remove(item_key)

    # Moves an item from its current location to a new location (location can also be "PLAYER" or a container item key)
    def MoveItemTo(self, item, location_key):
        item_key = self.ItemKey(item)
        self.RemoveItemFromGame(item_key)
        self.PlaceItemIn(item_key, location_key)

    # Places an item in a new location (location can also be "PLAYER" or a container item key)
    # (Doesn't remove item from any locations it may already be; location_key cannot be a list)
    def PlaceItemIn(self, item, location_key):
        item_key = self.ItemKey(item)
        if location_key == "PLAYER":
            player.inventory.append(item_key)
        elif not location_key == None:
            # Attempt to place item in location
            item_placed = False
            for place_key in locations.locations_dictionary:
                if place_key == location_key:
                    locations[place_key]["items"].append(item_key)
                    item_placed = True
                    break

            # Attempt to place item in a container
            if not item_placed:
                for container_key in self.items_dictionary:
                    if (container_key == location_key) and (self.items_dictionary[container_key].get("is_container?")):
                        self.items_dictionary[container_key]["contents"].append(item_key)
                        break

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
    while not state.quit_confirmed:
        globals.IntroText(context)
        globals.InitialSetup(context)
        locations.DoLook()
        while not (state.quit_confirmed or state.restart_confirmed):
            print()
            actions.ParseCommand(input("> "))
            state.PostProcess()

        # Handle restart
        if state.restart_confirmed:
            player.__init__()
            locations.__init__()
            actions.__init__()
            items.__init__()
            events.__init__()
            state.__init__()
            context.__init__(player, locations, actions, items, state, events)
            action_handlers.Register(context)
            item_handlers.Register(context)
            location_handlers.Register(context)

if __name__ == "__main__":
   Play()