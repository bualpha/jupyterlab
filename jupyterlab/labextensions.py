# coding: utf-8
"""Jupyter LabExtension Entry Points."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import print_function

import json
import os
import sys

from jupyter_core.application import JupyterApp, base_flags, base_aliases

from traitlets import Bool, Unicode

from .commands import (
    install_extension, uninstall_extension, list_extensions,
    enable_extension, disable_extension,
    link_package, unlink_package, build
)


flags = dict(base_flags)
flags['no-build'] = (
    {'BaseExtensionApp': {'should_build': False}},
    "Defer building the app after the action."
)
flags['clean'] = (
    {'BaseExtensionApp': {'should_clean': True}},
    "Cleanup intermediate files after the action."
)

aliases = dict(base_aliases)
aliases['app-dir'] = 'BaseExtensionApp.app_dir'


here = os.path.dirname(__file__)
with open(os.path.join(here, 'package.app.json')) as fid:
    data = json.load(fid)
VERSION = data['jupyterlab']['version']


class BaseExtensionApp(JupyterApp):
    version = VERSION
    flags = flags
    aliases = aliases

    app_dir = Unicode('', config=True,
        help="The app directory to target")

    should_build = Bool(False, config=True,
        help="Whether to build the app after the action")

    should_clean = Bool(False, config=True,
        help="Whether temporary files should be cleaned up after building jupyterlab")

    def _log_format_default(self):
        """A default format for messages"""
        return "%(message)s"


class InstallLabExtensionApp(BaseExtensionApp):
    description = "Install labextension(s)"
    should_build = Bool(True, config=True,
        help="Whether to build the app after the action")

    def start(self):
        self.extra_args = self.extra_args or [os.getcwd()]
        [install_extension(arg, self.app_dir, logger=self.log)
         for arg in self.extra_args]
        if self.should_build:
            try:
                build(self.app_dir, clean_staging=self.should_clean, logger=self.log)
            except Exception as e:
                for arg in self.extra_args:
                    uninstall_extension(arg, self.app_dir, logger=self.log)
                raise e


class LinkLabExtensionApp(BaseExtensionApp):
    description = """
    Link local npm packages that are not lab extensions.

    Links a package to the JupyterLab build process. A linked
    package is manually re-installed from its source location when
    `jupyter lab build` is run.
    """
    should_build = Bool(True, config=True,
        help="Whether to build the app after the action")

    def start(self):
        self.extra_args = self.extra_args or [os.getcwd()]
        [link_package(arg, self.app_dir, logger=self.log)
         for arg in self.extra_args]
        if self.should_build:
            try:
                build(self.app_dir, clean_staging=self.should_clean, logger=self.log)
            except Exception as e:
                for arg in self.extra_args:
                    unlink_package(arg, self.app_dir, logger=self.log)
                raise e


class UnlinkLabExtensionApp(BaseExtensionApp):
    description = "Unlink packages by name or path"
    should_build = Bool(True, config=True,
        help="Whether to build the app after the action")

    def start(self):
        self.extra_args = self.extra_args or [os.getcwd()]
        ans = any([unlink_package(arg, self.app_dir, logger=self.log)
                   for arg in self.extra_args])
        if ans and self.should_build:
            build(self.app_dir, clean_staging=self.should_clean, logger=self.log)


class UninstallLabExtensionApp(BaseExtensionApp):
    description = "Uninstall labextension(s) by name"
    should_build = Bool(True, config=True,
        help="Whether to build the app after the action")

    def start(self):
        self.extra_args = self.extra_args or [os.getcwd()]
        ans = any([uninstall_extension(arg, self.app_dir, logger=self.log)
                   for arg in self.extra_args])
        if ans and self.should_build:
            build(self.app_dir, clean_staging=self.should_clean, logger=self.log)


class ListLabExtensionsApp(BaseExtensionApp):
    description = "List the installed labextensions"

    def start(self):
        list_extensions(self.app_dir, logger=self.log)


class EnableLabExtensionsApp(BaseExtensionApp):
    description = "Enable labextension(s) by name"

    def start(self):
        [enable_extension(arg, self.app_dir, logger=self.log)
         for arg in self.extra_args]


class DisableLabExtensionsApp(BaseExtensionApp):
    description = "Disable labextension(s) by name"

    def start(self):
        [disable_extension(arg, self.app_dir, logger=self.log)
         for arg in self.extra_args]


_examples = """
jupyter labextension list                        # list all configured labextensions
jupyter labextension install <extension name>    # install a labextension
jupyter labextension uninstall <extension name>  # uninstall a labextension
"""


class LabExtensionApp(JupyterApp):
    """Base jupyter labextension command entry point"""
    name = "jupyter labextension"
    version = VERSION
    description = "Work with JupyterLab extensions"
    examples = _examples

    subcommands = dict(
        install=(InstallLabExtensionApp, "Install labextension(s)"),
        uninstall=(UninstallLabExtensionApp, "Uninstall labextension(s)"),
        list=(ListLabExtensionsApp, "List labextensions"),
        link=(LinkLabExtensionApp, "Link labextension(s)"),
        unlink=(UnlinkLabExtensionApp, "Unlink labextension(s)"),
        enable=(EnableLabExtensionsApp, "Enable labextension(s)"),
        disable=(DisableLabExtensionsApp, "Disable labextension(s)"),
    )

    def start(self):
        """Perform the App's functions as configured"""
        super(LabExtensionApp, self).start()

        # The above should have called a subcommand and raised NoStart; if we
        # get here, it didn't, so we should self.log.info a message.
        subcmds = ", ".join(sorted(self.subcommands))
        sys.exit("Please supply at least one subcommand: %s" % subcmds)


main = LabExtensionApp.launch_instance
