"""
Version information for Smart File Organizer Pro
Update this file for each release
"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Application information
APP_NAME = "Smart File Organizer Pro"
APP_VERSION = __version__
APP_AUTHOR = "BITTU KUMAR AZAD"
APP_COPYRIGHT = "Copyright © 2025 Bittu Kumar Azad"
APP_DESCRIPTION = "Intelligent automated file management system"
APP_WEBSITE = "https://github.com/Bittukrazad/smart-file-organizer"

# Update configuration
GITHUB_REPO = "Bittukrazad/smart-file-organizer"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
ENABLE_AUTO_UPDATE_CHECK = True
UPDATE_CHECK_INTERVAL_DAYS = 7  # days

# Build information (managed by build system)
BUILD_DATE = None
BUILD_NUMBER = None


def get_version_string():
    return f"v{APP_VERSION}"


def get_full_version_string():
    if BUILD_NUMBER:
        return f"{APP_NAME} v{APP_VERSION} (Build {BUILD_NUMBER})"
    return f"{APP_NAME} v{APP_VERSION}"


def compare_versions(version1: str, version2: str) -> int:
    v1_parts = [int(x) for x in version1.split('.')]
    v2_parts = [int(x) for x in version2.split('.')]

    for i in range(max(len(v1_parts), len(v2_parts))):
        v1 = v1_parts[i] if i < len(v1_parts) else 0
        v2 = v2_parts[i] if i < len(v2_parts) else 0

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1

    return 0
