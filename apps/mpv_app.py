from apps.managed_app import ManagedApp
from apps.types import ProcessConfig, ProcessProperties


class MpvApp(ManagedApp):
    process_config = ProcessConfig(
        process_name="mpv",
        process_params=["--player-operation-mode=pseudo-gui"],
        wm_class_target="mpv",
        wm_name_target="mpv",
    )

    process_properties: ProcessProperties | None = None

    def can_locate_window(self) -> bool:
        return True

    def can_interact(self) -> bool:
        return True

    async def focus(self):
        pass
