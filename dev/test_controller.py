from apps.discord_app import DiscordApp
from controllers.DiscordController.discord_controller import DiscordAppController
from utils.broadcaster import Broadcaster

broadcaster = Broadcaster()
discord_controller = DiscordAppController(broadcaster)


async def test_controller():
    print("STARTING CONTROLLER FROM ROUTE")
    await discord_controller.start()
    return
