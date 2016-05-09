### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ACTIONS ###

# To add a new action handler, first create a function for your action
#  and then "bind" the handler to your action in the bottom section of the file.

# This is a helper function that prints out your string, but replaces
#  the '@' character with 'the <item name>' for whatever item you pass in.
def PrintDefaultActionString(default_string, item):
    print(default_string.replace("@", "the " + item.get("name")))

def Get(context, item):
    if item["key"] == "ALL":
        context.items.GetAll()
    elif item["key"] in context.player.inventory:
        PrintDefaultActionString("You're already carrying @.", item)
    elif (not item.get("takeable?")):
        print("You can't pick that up!")
    else:
        context.items.GetItem(item["key"])

def Drop(context, item):
    if item["key"] == "ALL":
        context.items.DropAll()
    elif not (item["key"] in context.player.inventory):
        PrintDefaultActionString("You're not carrying @.", item)
    else:
        context.items.DropItem(item["key"])

def Examine(context, item):
    examine_string = item.get("examine_string")
    if (not examine_string == None) and (len(examine_string) > 0):
        print(examine_string)
    else:
        PrintDefaultActionString("You see nothing special about @.", item)

def Inventory(context):
    print("You are carrying:")
    if len(context.player.inventory) == 0:
        print("  Nothing")
    else:
        for item_key in context.player.inventory:
            print("  a " + context.items.GetLongDescription(item_key))

def Help(context):
    print("This is a text adventure game.")
    print("Enter commands like \'GO NORTH\' or \'TAKE ROCK\' to tell the computer what you would like to do.")
    print("Most commands are either one or two words.")
    print("For a full list of commands, type \'ACTIONS\'.")

def Actions(context):
    print("Available actions:")
    for action_key in sorted(context.actions.actions_dictionary):
        if context.actions[action_key].get("suppress_in_actions_list?"):
            continue

        print("  ", end='')
        i = 0
        for word in context.actions.actions_dictionary[action_key]["words"]:
            if i > 0:
                print(" / ", end='')
            print(word, end='')
            i += 1
        print()

def Quit(context):
    context.conditions.quit_pending = True
    print("Are you sure you want to quit (Y/N)?")

def Yes(context):
    print("You sound really positive!")

def No(context):
    print("You sound awfully negative!")

def Wait(context):
    print("Time passes...")

# Here is where you "bind" your action handler function to a specific action.
def Register(context):
    actions = context.actions
    actions.AddActionHandler("GET", Get)
    actions.AddActionHandler("DROP", Drop)
    actions.AddActionHandler("EXAMINE", Examine)
    actions.AddActionHandler("INVENTORY", Inventory)
    actions.AddActionHandler("HELP", Help)
    actions.AddActionHandler("ACTIONS", Actions)
    actions.AddActionHandler("QUIT", Quit)
    actions.AddActionHandler("YES", Yes)
    actions.AddActionHandler("NO", No)
    actions.AddActionHandler("WAIT",Wait)