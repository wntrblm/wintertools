# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import pyvisa

from . import config

_resource_manager = None


def global_resource_manager():
    global _resource_manager

    if _resource_manager is None:
        _resource_manager = pyvisa.ResourceManager(
            config.get("visa.interface", default="@py")
        )

    return _resource_manager


class Instrument:
    TIMEOUT = 2000

    def __init__(self, resource_manager=None, resource_name=None):
        self.connect(resource_manager, resource_name)

    def connect(self, resource_manager, resource_name):

        if resource_manager is None:
            resource_manager = global_resource_manager()

        if resource_name is None:
            resource_name = config.get(
                f"{self.__class__.__name__.lower()}.visa_resource_name"
            )

        try:
            resource = resource_manager.open_resource(resource_name)
        except pyvisa.errors.VisaIOError as exc:
            raise RuntimeError(
                f"Couldn't connect to VISA instrument {self.__class_.__name__} at {resource_name}"
            ) from exc

        resource.timeout = self.TIMEOUT
        self.port = resource

    def close(self):
        self.port.close()

    def write(self, command):
        self.port.write(command)

    def read(self):
        return self.port.read()

    def query(self, command):
        return self.port.query(command)
