'''
Created on 06.11.2019

@author: thopiekar
'''

import os
import platform
import site
import sys

from UM.Logger import Logger

def registerThirdPartyModules(third_party_dir):
    third_party_dir = os.path.realpath(third_party_dir)
    Logger.log("i", "Adding 3rd-party modules from: {}".format(third_party_dir))

    # Collecting platform info
    platform_info = [platform.python_implementation().lower(),
                     "{0}.{1}".format(*platform.python_version_tuple()),
                     platform.system().lower(),
                     platform.machine().lower(),
                     ]
    Logger.log("i", "Platform is: {}".format(platform_info))

    # Generating directory names
    platform_dirs = ["-".join(platform_info[:x] + ["common",]) for x in range(len(platform_info))] + ["-".join(platform_info),]
    platform_dirs.reverse()
    Logger.log("d", "platform_dirs: {}".format(platform_dirs))

    # Looking for directories
    found_platform_dirs = []
    for subdir in platform_dirs:
        subdir = os.path.join(third_party_dir, subdir)
        if os.path.isdir(subdir):
            found_platform_dirs.append(subdir)

    # Looking for modules in these directories
    for found_platform_dir in found_platform_dirs:
        while found_platform_dir in sys.path:
            sys.path.remove(found_platform_dir)
        site.addsitedir(found_platform_dir)
        Logger.log("i", "Adding search path: {}".format(found_platform_dir))
