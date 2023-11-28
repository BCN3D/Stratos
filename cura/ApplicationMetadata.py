#  Copyright (c) 2022 UltiMaker
#  Cura is released under the terms of the LGPLv3 or higher.

# ---------
# General constants used in Cura
# ---------
DEFAULT_CURA_APP_NAME = "BCN3D Stratos"
DEFAULT_CURA_DISPLAY_NAME = "BCN3D Stratos"
DEFAULT_CURA_VERSION = "dev"
DEFAULT_CURA_BUILD_TYPE = ""
DEFAULT_CURA_DEBUG_MODE = False
DEFAULT_CURA_LATEST_URL = "https://software.ultimaker.com/latest.json"

# Each release has a fixed SDK version coupled with it. It doesn't make sense to make it configurable because, for
# example Cura 3.2 with SDK version 6.1 will not work. So the SDK version is hard-coded here and left out of the
# CuraVersion.py.in template.
CuraSDKVersion = "8.4.0"

try:
    from cura.CuraVersion import CuraLatestURL
    if CuraLatestURL == "":
        CuraLatestURL = DEFAULT_CURA_LATEST_URL
except ImportError:
    CuraLatestURL = DEFAULT_CURA_LATEST_URL

try:
    from cura.CuraVersion import CuraAppName  # type: ignore
    if CuraAppName == "":
        CuraAppName = DEFAULT_CURA_APP_NAME
except ImportError:
    CuraAppName = DEFAULT_CURA_APP_NAME

try:
    from cura.CuraVersion import CuraVersion  # type: ignore
    if CuraVersion == "":
        CuraVersion = DEFAULT_CURA_VERSION
except ImportError:
    CuraVersion = DEFAULT_CURA_VERSION  # [CodeStyle: Reflecting imported value]

# CURA-6569
# This string indicates what type of version it is. For example, "enterprise". By default it's empty which indicates
# a default/normal Cura build.
try:
    from cura.CuraVersion import CuraBuildType  # type: ignore
except ImportError:
    CuraBuildType = DEFAULT_CURA_BUILD_TYPE

try:
    from cura.CuraVersion import CuraDebugMode  # type: ignore
except ImportError:
    CuraDebugMode = DEFAULT_CURA_DEBUG_MODE

# CURA-6569
# Various convenience flags indicating what kind of Cura build it is.
__ENTERPRISE_VERSION_TYPE = "enterprise"
IsEnterpriseVersion = CuraBuildType.lower() == __ENTERPRISE_VERSION_TYPE
IsAlternateVersion = CuraBuildType.lower() not in [DEFAULT_CURA_BUILD_TYPE, __ENTERPRISE_VERSION_TYPE]
# NOTE: IsAlternateVersion is to make it possibile to have 'non-numbered' versions, at least as presented to the user.
#       (Internally, it'll still have some sort of version-number, but the user is never meant to see it in the GUI).
#       Warning: This will also change (some of) the icons/splash-screen to the 'work in progress' alternatives!

try:
    from cura.CuraVersion import CuraAppDisplayName  # type: ignore
    if CuraAppDisplayName == "":
        CuraAppDisplayName = DEFAULT_CURA_DISPLAY_NAME
    if IsEnterpriseVersion:
        CuraAppDisplayName = CuraAppDisplayName

except ImportError:
    CuraAppDisplayName = DEFAULT_CURA_DISPLAY_NAME

DEPENDENCY_INFO = {}
try:
    from pathlib import Path
    conan_install_info = Path(__file__).parent.parent.joinpath("conan_install_info.json")
    if conan_install_info.exists():
        import json
        with open(conan_install_info, "r") as f:
            DEPENDENCY_INFO = json.loads(f.read())
except:
    pass
