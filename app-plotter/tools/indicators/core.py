# Global Imports
# (No global imports yet.)

# Local Imports
from os import sys
from os import path

scope = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(scope)

from coreglobals import get_global_property
from coreglobals import set_global_property


# from, import * guard.
__all__ = ['my_public_method']


# Public Methods
def my_public_method():
    # Test if we have access to the global properties.
    NAMESPACE = get_global_property('APP_NAME') + "." + __name__
    print('{}: Module accessed.'.format(NAMESPACE))


# vim: ts=4 ft=python nowrap fdm=marker
