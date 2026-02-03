from fastapi import APIRouter, Depends

from controllers.DiscordController.discord_controller import DiscordAppController
from controllers.DiscordController.discord_types import DiscordAppTaskType
from dependencies import get_discord_controller

router = APIRouter()


@router.get("/start")
async def start_discord(
    controller: DiscordAppController = Depends(get_discord_controller),
):
    await controller.start()
    await controller.start_playwright()
    return


@router.get("/stop")
async def stop_discord(
    controller: DiscordAppController = Depends(get_discord_controller),
):
    return await controller.stop()


@router.get("/server/learn")
async def learn_servers(
    controller: DiscordAppController = Depends(get_discord_controller),
):
    return await controller.submit_task(DiscordAppTaskType.LEARN_SERVERS, {})
