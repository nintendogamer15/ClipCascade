#!/usr/bin/env python3
# ClipCascade - A seamless clipboard syncing utility
# Repository: https://github.com/Sathvik-Rao/ClipCascade
#
# Author: Sathvik Rao Poladi
# License: GPL-3.0
#
# This script serves as the entry point for the ClipCascade application
# initializing and running the core application logic.

import os
import sys

# Add Flatpak-specific module path
if os.path.exists('/app/lib/python3.11/site-packages'):
    sys.path.insert(0, '/app/lib/python3.11/site-packages')

from core.application import Application


class Main:
    def __init__(self):
        Application().run()


if __name__ == "__main__":
    Main()
