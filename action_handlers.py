### THIS FILE CONTAINS ACTION HANDLERS FOR YOUR ACTIONS ###

# To add a new action handler, first create a function for your action
#  and then "bind" the handler to your action in the bottom section of the file.

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

def Inventory(context):
    context.Print("You are carrying:")
    if len(context.player.inventory) == 0:
        context.Print("  Nothing")
    else:
        for item_key in context.player.inventory:
            context.Print("  a " + context.items.GetLongDescription(item_key))

def Help(context):
    context.Print("This is a text adventure game.")
    context.Print("Enter commands like \'GO NORTH\' or \'TAKE ROCK\' to tell the computer what you would like to do.")
    context.Print("Most commands are either one or two words.")
    context.Print("For a full list of commands, type \'ACTIONS\'.")

def Actions(context):
    print("Available actions:")
    for action_key in sorted(context.actions.actions_dictionary):
        if context.actions[action_key].get("suppress_in_actions_list?"):
            continue

        print_string = "  "
        i = 0
        for word in context.actions.actions_dictionary[action_key]["words"]:
            if i > 0:
                print_string += " / "
            print_string += word
            i += 1
        context.Print(print_string)

def Quit(context):
    context.state.quit_pending = True
    context.Print("Are you sure you want to quit (Y/N)?")

def Yes(context):
    context.Print("You sound really positive!")

def No(context):
    context.Print("You sound awfully negative!")

def Wait(context):
    context.Print("Time passes...")

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