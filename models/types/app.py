from typing import TypeVar

from apps.managed_app import ManagedApp

ManagedAppType = TypeVar("ManagedAppType", bound="ManagedApp")
