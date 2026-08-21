"""Data-provider contracts and built-in providers."""

from campnet.providers.at import (
    CONTINUOUS_COMMANDS,
    ONE_OFF_COMMANDS,
    OPTIMIZE_COMMANDS,
    PASSIVE_SCAN_COMMANDS,
    SIM_SPECIFIC_COMMANDS,
    ATProvider,
)
from campnet.providers.base import CollectionContext, DataProvider
from campnet.providers.gnss import GNSSProvider
from campnet.providers.multisim import MultiSIMProvider
from campnet.providers.quectel_sim import QuectelATSimSlotController
from campnet.providers.speedtest import SpeedTestProvider, SSHSpeedTestAdapter
from campnet.providers.system import SystemProvider

__all__ = [
    "ATProvider",
    "CONTINUOUS_COMMANDS",
    "CollectionContext",
    "DataProvider",
    "GNSSProvider",
    "ONE_OFF_COMMANDS",
    "OPTIMIZE_COMMANDS",
    "PASSIVE_SCAN_COMMANDS",
    "SIM_SPECIFIC_COMMANDS",
    "MultiSIMProvider",
    "QuectelATSimSlotController",
    "SSHSpeedTestAdapter",
    "SpeedTestProvider",
    "SystemProvider",
]
