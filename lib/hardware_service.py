import sys
from abc import ABCMeta, abstractmethod

class HardwareService(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def move_one_host(self, host, old_cloud, new_cloud):
        # This function is not necessary. It's a helper for move_hosts
        """ TODO add documentation
        """

    @abstractmethod
    def move_hosts(self, quads, datearg, *args, **kwargs):
        # This function can use HardwareService.move_one_host
        # This correspond to quads_move_hosts
        """ TODO add documentation
        """

_hardware_service = None

def set_hardware_service(hardware_service):
    global _hardware_service
    if _hardware_service is not None:
        sys.exit("Error: _hardware_service already set")
    _hardware_service = hardware_service

def get_hardware_service():
    return _hardware_service