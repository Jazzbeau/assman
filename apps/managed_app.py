import asyncio
import os
import subprocess
from abc import ABC, abstractmethod

import psutil

from apps.types import ProcessConfig, ProcessProperties, XWindowProperties
from config import config


class ManagedApp(ABC):
    process_config: ProcessConfig
    process_properties: ProcessProperties | None

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

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

    def get_process_properties(self) -> ProcessProperties:
        if not self.process_properties:
            raise ValueError(
                "Attempted to fetch Process Properties before initilisation"
            )
        return self.process_properties

    def find_window_name(self):
        window_id = self.get_process_properties().window_id
        result = subprocess.check_output(
            ["xprop", "-id", str(window_id), "WM_NAME"]
        ).decode()
        return result

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
        return await self.is_running()

    async def is_running(self) -> bool:
        if not (self.process_properties and self.process_properties.process_id):
            return False
        process = psutil.Process(self.process_properties.process_id)
        if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            return True
        return False

    @abstractmethod
    async def is_locatable(self) -> bool:
        pass

    @abstractmethod
    async def is_interactable(self) -> bool:
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
