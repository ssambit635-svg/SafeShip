"""Deployed version information.

This is read from an environment variable in production so the deployed
Git commit can be surfaced via GET /version without rebuilding the image.
"""

import os

VERSION = os.environ.get("SAFESHIP_VERSION", "dev-local")
