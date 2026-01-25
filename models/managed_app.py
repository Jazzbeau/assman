import asyncio
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass

import psutil

from config import config


@dataclass
class ProcessConfig:
    """ManagedApp struct for supplying data to new application instances"""

    process_name: str
    process_params: list[str]
    wm_class_target: str
    wm_name_target: str


@dataclass
class ProcessProperties:
    """ManagedApp struct for organising handles for active applications"""

    pg_id: int
    process_id: int
    window_id: int


@dataclass
class XWindowProperties:
    wm_class: str
    wm_pid: int
    wm_name: str


class ManagedApp(ABC):
    name: str
    process_config: ProcessConfig
    process_properties: ProcessProperties | None

    def _list_windows(self) -> list[str]:
        """Fetch list of window id's in current display environment"""
        env = os.environ.copy()
        out = subprocess.check_output(
            ["xdotool", "search", "--name", "--onlyvisible", ""],
            env=env,
            stderr=subprocess.DEVNULL,
        ).decode()
        return out.splitlines()

    def _get_xprop(self, window_id: str) -> XWindowProperties | None:
        """Fetch the name, class and associated pid from a given window id"""
        props = ["WM_NAME", "WM_CLASS", "_NET_WM_PID"]
        result = subprocess.run(
            ["xprop", "-id", window_id, *props],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None

        wm_name = wm_class = None
        wm_pid: int | None = None

        for line in result.stdout.splitlines():
            if " = " not in line:
                # Property was not present in no '=' in response from observation
                continue

            key_type, value = line.split(" = ", 1)
            if key_type.startswith("WM_NAME"):
                wm_name = value
            elif key_type.startswith("WM_CLASS"):
                wm_class = value
            elif key_type.startswith("_NET_WM_PID"):
                try:
                    wm_pid = int(value.strip())
                except ValueError:
                    wm_pid = None
        if not (wm_name and wm_class and wm_pid):
            return None
        return XWindowProperties(wm_class, wm_pid, wm_name)

    async def _start_process_with_window(self):
        """Open an instance of process defined by ManagedApp process_config - wait for timeout and return new window ID's"""
        timeout = config.POLL_TIMEOUT
        env = os.environ.copy()

        # Get window state -> Spawn Process -> Check window state
        prior_window_state = set(self._list_windows())
        process = subprocess.Popen(
            [self.process_config.process_name, *self.process_config.process_params],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        await asyncio.sleep(timeout)
        new_windows = set(self._list_windows()) - prior_window_state
        return process.pid, new_windows

    async def launch(self, *, use_class_target=True, use_name_target=True):
        new_pid, new_window_ids = await self._start_process_with_window()
        valid_property_sets: list[tuple[XWindowProperties, str]] = []

        for window_id in new_window_ids:
            window_props = self._get_xprop(window_id)
            if not window_props:
                continue
            if use_name_target:
                if (
                    self.process_config.wm_name_target
                    not in window_props.wm_name.lower()
                ):
                    continue
            if use_class_target:
                if (
                    self.process_config.wm_class_target
                    not in window_props.wm_class.lower()
                ):
                    continue
            valid_property_sets.append((window_props, window_id))
        if len(valid_property_sets) == 0:
            raise ValueError(
                f"Could not find any windows with valid identifier after attempting to launch {self.process_config.process_name}"
            )
        elif len(valid_property_sets) > 1:
            raise ValueError(
                f"Located multiple valid main window targets when launching {self.process_config.process_name}"
            )
        valid_window_props, valid_window_id = valid_property_sets[0]
        self.process_properties = ProcessProperties(
            process_id=new_pid,
            window_id=int(valid_window_id),
            pg_id=os.getpgid(valid_window_props.wm_pid),
        )
        return self.is_running()

    def is_running(self) -> bool:
        if not (self.process_properties and self.process_properties.process_id):
            return False
        process = psutil.Process(self.process_properties.process_id)
        if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            return True
        return False

    @abstractmethod
    def can_locate_window(self) -> bool:
        pass

    @abstractmethod
    def can_interact(self) -> bool:
        pass

    async def terminate(self) -> bool:
        if not (self.process_properties and self.process_properties.process_id):
            raise ValueError(
                "Attempted to terminate process with no associated process_id"
            )
        process = psutil.Process(self.process_properties.process_id)
        process.kill()
        if self.is_running():
            return False
        return True

    def get_main_window_id(self) -> int:
        if not self.process_properties:
            raise ValueError(
                "Requested main window id, found no associated main window id"
            )
        return self.process_properties.window_id

    @abstractmethod
    async def focus(self):
        pass


class DiscordApp(ManagedApp):
    process_config = ProcessConfig(
        process_name="discord",
        process_params=["--remote-debugging-port=9222"],
        wm_class_target="discord",
        wm_name_target="discord",
    )

    process_properties: ProcessProperties | None = None

    def can_locate_window(self) -> bool:
        return True

    def can_interact(self) -> bool:
        return True

    async def focus(self):
        pass


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


async def test_app():
    dc = DiscordApp()
    print("Launching discord result:\t", end="")
    print(await dc.launch())
    pc = psutil.Process(dc.process_properties.process_id)
    window_info = subprocess.check_output(
        ["xwininfo", "-id", str(dc.process_properties.window_id)],
    ).decode()
    print(window_info)

    print(f"Discord process running:\t{dc.is_running()}")
    print(f"Discord process status: \t{pc.status()}")
    print("Terminating Discord")
    await dc.terminate()
    print(f"Discord process running:\t{dc.is_running()}")
    print(f"Discord process status: \t{pc.status()}")
