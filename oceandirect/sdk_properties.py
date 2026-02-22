# -*- coding: utf-8 -*-
"""
Created on Wed Jan  9 16:25:46 2019

@author: Ocean Insight Inc.
"""

import os
import platform
import os.path

# Simplified for local project use
os_platform = platform.system()

## Library name based on OS
if os_platform == 'Darwin':
    oceandirect_libname = "liboceandirect.dylib"
elif os.name == 'nt':
    oceandirect_libname = "OceanDirect.dll"
else:
    oceandirect_libname = "liboceandirect.so"

module_path = os.path.dirname(__file__)
oceandirect_dll = os.path.join(module_path, "lib", oceandirect_libname)
