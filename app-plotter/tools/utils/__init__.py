# ;------------------------------------------------------------------------------------------
# ; Initialisation File for the "Utils" Module
# ;------------------------------------------------------------------------------------------

"""
__init__ file for 'app/tools/utils'

This file should provide the necessary import short-cuts for the module.
For example, a ``tools.utils.io.Foo()`` class can be imported as ``tools.utils.Foo()`` by
the main application once defined inside this module header file.
"""

from .core import *
from .io import InputOutput as IO

__version__ = 'dev-v0.0.1'
__name__ = 'tools.utils'
__author__ = 'Muhittin Bilginer'
__email__ = 'muhittin.bilginer@gmail.com'
__url__ = ''

# vim: ts=4 ft=python nowrap fdm=marker
