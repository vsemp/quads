import sys
from abc import ABCMeta, abstractmethod

class InventoryService(object):

    __metaclass__ = ABCMeta
    
    # Probably, some of the methods are static. Let's see.

    @abstractmethod
    def init_quads(self, quads):
        # Should be used in Quads __init__
        """ TODO add documentation
        """

    @abstractmethod
    def load_data(self, quads, force):
        # this code goes here for Juniper
        # try:
        #     stream = open(config, 'r')
        #     self.data = yaml.load(stream)
        #     stream.close()
        # except Exception, ex:
        #     self.logger.error(ex)
        #     exit(1)
        """ TODO add documentation
        """
    
    @abstractmethod
    def init_data(self, quads, force):
        # quads_init_data
        """ TODO add documentation
        """
    
    @abstractmethod
    def sync_state(self, quads):
        # quads_sync_data
        """ TODO add documentation
        """
    
    @abstractmethod
    def write_data(self, quads, doexit = True):
        # quads_write_data
        """ TODO add documentation
        """

_inventory_service = None

def set_inventory_service(inventory_service):
    global _inventory_service
    if _inventory_service is not None:
        sys.exit("Error: _inventory_service already set")
    _inventory_service = inventory_service

def get_inventory_service():
    return _inventory_service
