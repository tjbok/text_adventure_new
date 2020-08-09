### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ACTIONS ###

# To add a new action handler, first create a function for your action
#  and then "bind" the handler to your action in the bottom section of the file.
# Unlike location or item handlers, note that if you define an action handler, you NEED
#  to handle every user input
#
# Different types of actions get different parameters:
#   * one-word actions (e.g. INVENTORY) just get passed context.
#   * two-word actions (e.g. OPEN) and three-word actions (e.g. TURN ON) get passed context and a single item object.
#   * four word actions (e.g. PUT ITEM IN ITEM) get passed context and two objects

# Ideally, these action handlers are generic and don't reference specific items or locations.
# But that's up to you...

# NOTES ON ACTIONS.JSON
#       "words" : a list containing all words for the action
#       "requires_object?" : true if the item needs an object (required for all 2-, 3-, and 4-word actions)
#       "prepositions" : list containing all prepositions associated with the action (required for 3- and 4-word actions)
#                   -- note that prepositions are key for disambiguating between actions with overlapping words
#                       (e.g. "PUT IN" vs "PUT ON").
#                   -- You can't have two actions with overlapping words AND overlapping prepositions
#       "no_second_item?" : set to true for items with prepositions but only one item (e.g. TURN ON ITEM)
#                   -- this distinguishes 3-word actions from 4-word actions
#       "is_move?" : true if this is a movement action (always one word)
#       "suports_all?" : true if the action supports the ALL object (e.g. TAKE ALL)
#       "suppress_in_actions_list?" : true if you don't want this action to show up when player types ACTIONS

def Get(context, item):
    if item["key"] == "ALL":
        context.items.GetAll()
    elif item["key"] in context.player.inventory:
        context.PrintItemInString("You're already carrying @.", item)
    elif (not item.get("takeable?")):
        context.Print("You can't pick that up!")
    else:
        context.items.GetItem(item["key"])

def Drop(context, item):
    if item["key"] == "ALL":
        context.items.DropAll()
    elif not (item["key"] in context.player.inventory):
        context.PrintItemInString("You're not carrying @.", item)
    else:
        context.items.DropItem(item["key"])

def Examine(context, item):
    examine_string = item.get("examine_string")
    if (not examine_string == None) and (len(examine_string) > 0):
        context.Print(examine_string)
    else:
        context.PrintItemInString("You see nothing special about @.", item)

def Open(context, item):
  if item.get("openable?"):
    if not item.get("is_open?"):
      if item.get("is_locked?"):
        context.PrintItemInString("@ is locked.", item)
      elif (item.get("is_container?") and len(item["contents"])):
        context.Print("Opening the " + item["name"] + " reveals:")
        context.items.ListItems(item["contents"], indent=2)
      else:
        context.PrintItemInString("You open @.", item)
      item["is_open?"] = True
    else:
      context.PrintItemInString("@ is already open.", item)
  else:
    context.Print("You can't open that.")

def Close(context, item):
  if item.get("openable?"):
    if item.get("is_open?"):
      context.PrintItemInString("You close @.", item)
      item["is_open?"] = False
    else:
      context.PrintItemInString("@ isn't open.", item)
  else:
    context.Print("You can't close that.")

def TurnOn(context, item):
    context.Print("You can't turn that on.")

def TurnOff(context, item):
    context.Print("You can't turn that off.")

def Inventory(context):
    context.Print("You are carrying:")
    context.items.ListItems(context.player.inventory, indent=2)    

def Dance(context):
    context.Print("You put a couple of moves together, but aren't feeling it.") 

def Help(context):
    context.Print("This is a text adventure game.")
    context.Print("Enter commands like \'NORTH\' or \'TAKE COIN\' to tell the computer what you would like to do.")
    context.Print("For a full list of commands, type \'ACTIONS\'.")

def PrintAction(context, action_key):
    print_string = "  " + context.actions[action_key]["words"][0]
    if context.actions[action_key].get("requires_object?"):
            print_string += " item"
    preps = context.actions[action_key].get("prepositions")
    if preps:
        print_string += " "
        for j in range(len(preps)):
            if (j>0):
                print_string += "/"
            print_string += preps[j]
        if not context.actions[action_key].get("no_second_item?"):
            print_string += " item"

    if len(context.actions[action_key]["words"]) > 1:
        print_string += " ... (or "
        for i in range(1,len(context.actions[action_key]["words"])):
            if i > 1:
                print_string += "/"
            print_string += context.actions[action_key]["words"][i]
        print_string += ")"
        
    context.Print(print_string)

def Actions(context):
    print("Movement:")
    for action_key in context.actions.actions_dictionary:
        if context.actions[action_key].get("suppress_in_actions_list?"):
            continue
        if not context.actions[action_key].get("is_move?"):
            continue

        PrintAction(context, action_key)
    
    print("\nOther actions:")
    for action_key in sorted(context.actions.actions_dictionary):
        if context.actions[action_key].get("suppress_in_actions_list?"):
            continue
        if context.actions[action_key].get("is_move?"):
            continue

        PrintAction(context, action_key)

def Quit(context):
    context.state.quit_pending = True
    context.Print("Are you sure you want to quit (Y/N)?")

def Yes(context):
    context.Print("You sound really positive!")

def No(context):
    context.Print("You sound awfully negative!")

def Wait(context):
    context.Print("Time passes...")

def Insert(context, item):
    context.Print("You can't insert that.")    

def PutIn(context, item, second_item):
    if not item["key"] in context.player.inventory:
        context.PrintItemInString("You're not holding the @.", item)
    elif (not second_item == None) and second_item.get("is_container?"):
        if second_item.get("openable?") and not second_item.get("is_open?"):
            context.PrintItemInString("The @ is closed.", second_item)
        else:
            context.Print("Done.")
            context.player.inventory.remove(item["key"])
            second_item["contents"].append(item["key"])
    else:
      context.Print("You can't do that.")

def Type(context, item):
    context.Print("You can't type that.")

def TypeOn(context, item, second_item):
    context.Print("You can't do that.")

def Attack(context, item):
    context.Print("You should try to relax.")

def Debug(context):
    context.state.debug = not context.state.debug
    context.Print("Debugging toggled.")

# Here is where you "bind" your action handler function to a specific action.
def Register(context):
    actions = context.actions
    actions.AddActionHandler("GET", Get)
    actions.AddActionHandler("DROP", Drop)
    actions.AddActionHandler("EXAMINE", Examine)
    actions.AddActionHandler("OPEN", Open)
    actions.AddActionHandler("CLOSE", Close)
    actions.AddActionHandler("INSERT", Insert)
    actions.AddActionHandler("PUT_INTO", PutIn)
    actions.AddActionHandler("INVENTORY", Inventory)
    actions.AddActionHandler("HELP", Help)
    actions.AddActionHandler("ACTIONS", Actions)
    actions.AddActionHandler("QUIT", Quit)
    actions.AddActionHandler("YES", Yes)
    actions.AddActionHandler("NO", No)
    actions.AddActionHandler("WAIT", Wait)
    actions.AddActionHandler("TYPE", Type)
    actions.AddActionHandler("TYPE_ON", TypeOn)
    actions.AddActionHandler("ATTACK", Attack)
    actions.AddActionHandler("DEBUG", Debug)
    actions.AddActionHandler("TURN_ON", TurnOn)
    actions.AddActionHandler("TURN_OFF", TurnOff)