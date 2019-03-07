import os
import logging
import logging.config

from pisces import pisces_root
from pisces.utils import load_config


class PiscesBase():
    """Base class for all classes in the Pisces package.

    The purpose of this class is to load the config and configure logging.
    """ 
    def __init__(self, **kwargs):
        config_path = kwargs.get('config_path', 'config.yaml')
        self.config = load_config(config_path=config_path,
                                  path_root=pisces_root)

        # Configure logging.
        logging_config = self.config.get('logging')
        if logging_config is not None:
            logging.config.dictConfig(logging_config)    
        self.logger = logging.getLogger('system')
