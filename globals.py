# This function is called as the game is starting. Use it to print introduction text.
def IntroText(context):
    context.Print("Welcome adventurer!")
    print()

# This function is called as the game is starting. Use it to initialize game settings
#  like the player's starting location.
def InitialSetup(context):
    context.player.SetPlayerLocation("OUTSIDE_DINER")
    context.actions.swear_words = {"SHIT", "DAMN"}
    context.actions.swear_response = "Hey, watch your language!"