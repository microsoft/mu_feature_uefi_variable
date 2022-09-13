# @file
#
# Defines the CI settings for the Project Mu UEFI variable repository.
#
# Copyright (c) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import logging
import yaml
from edk2toolext.environment import shell_environment
from edk2toolext.invocables.edk2_ci_build import CiBuildSettingsManager
from edk2toolext.invocables.edk2_ci_setup import CiSetupSettingsManager
from edk2toolext.invocables.edk2_update import UpdateSettingsManager
from edk2toolext.invocables.edk2_pr_eval import PrEvalSettingsManager
from edk2toollib.utility_functions import GetHostInfo


class Settings(
        CiSetupSettingsManager,
        CiBuildSettingsManager,
        UpdateSettingsManager,
        PrEvalSettingsManager):

    def __init__(self):
        self.actual_packages = []
        self.actual_targets = []
        self.actual_architectures = []
        self.actual_tool_chain_tag = ""
        self.use_built_in_base_tools = None
        self.actual_scopes = None

    # ###################################################################### #
    #                             Extra CmdLine configuration                #
    # ###################################################################### #

    def AddCommandLineOptions(self, parserObj):
        pass

    def RetrieveCommandLineOptions(self, args):
        pass

    # ###################################################################### #
    #                        Default Support for this Ci Build               #
    # ###################################################################### #

    def GetPackagesSupported(self):
        """return iterable of edk2 packages supported by this build.
        These should be edk2 workspace relative paths."""

        return ("VariablePkg",)

    def GetArchitecturesSupported(self):
        """return iterable of edk2 architectures supported by this build."""

        return ("IA32", "X64", "ARM", "AARCH64")

    def GetTargetsSupported(self):
        """return iterable of edk2 target tags supported by this build."""

        return ("DEBUG", "RELEASE", "NO-TARGET", "NOOPT")

    # ###################################################################### #
    #                     Verify and Save requested Ci Build Config          #
    # ###################################################################### #

    def SetPackages(self, list_of_requested_packages):
        """
        Confirm the requested package list is valid and configure
        SettingsManager to build the requested packages.

        Raises an exception if a requested package is not supported.
        """

        unsupported = (set(list_of_requested_packages) -
                       set(self.GetPackagesSupported()))

        if len(unsupported) > 0:
            logging.critical("Unsupported Package Requested: "
                             " ".join(unsupported))
            raise Exception("Unsupported Package Requested: "
                            " ".join(unsupported))

        self.actual_packages = list_of_requested_packages

    def SetArchitectures(self, list_of_requested_architectures):
        """Confirm the requests architecture list is valid and configure
        SettingsManager to run only the requested architectures.

        Raises an exception if a requested architeecture is not supported.
        """

        unsupported = (set(list_of_requested_architectures) -
                       set(self.GetArchitecturesSupported()))

        if len(unsupported) > 0:
            logging.critical(
                "Unsupported Architecture Requested: " + " ".join(unsupported))
            raise Exception(
                "Unsupported Architecture Requested: " + " ".join(unsupported))
        self.actual_architectures = list_of_requested_architectures

    def SetTargets(self, list_of_requested_target):
        """Confirm the request target list is valid and configure
        SettingsManager to run only the requested targets.

        Raise an exception if a requested target is not supported.
        """

        unsupported = (set(list_of_requested_target) -
                       set(self.GetTargetsSupported()))

        if len(unsupported) > 0:
            logging.critical("Unsupported Targets Requested: "
                             " ".join(unsupported))
            raise Exception("Unsupported Targets Requested: "
                            " ".join(unsupported))
        self.actual_targets = list_of_requested_target

    # ###################################################################### #
    #                         Actual Configuration for Ci Build              #
    # ###################################################################### #

    def GetActiveScopes(self):
        """
        Return a tuple containing scopes that should be active for this
        process.
        """

        scopes = ("feature-variable-ci",
                  "cibuild",
                  "edk2-build",
                  "host-based-test")

        self.ActualToolChainTag = \
            shell_environment.GetBuildVars().GetValue("TOOL_CHAIN_TAG", "")

        if GetHostInfo().os.upper() == "LINUX" and \
           self.ActualToolChainTag.upper().startswith("GCC"):
            if "AARCH64" in self.actual_architectures:
                scopes += ("gcc_aarch64_linux",)
            if "ARM" in self.actual_architectures:
                scopes += ("gcc_arm_linux",)
            if "RISCV64" in self.actual_architectures:
                scopes += ("gcc_riscv64_unknown",)

        return scopes

    def GetRequiredSubmodules(self):
        """
        Return an iterable containing RequiredSubmodule objects. If there are
        no RequiredSubmodules, then return an empty iterable.
        """

        return []

    def GetName(self):
        """Returns the CI name."""

        return "MuUefiVariables"

    def GetDependencies(self):
        """
        Return git repository dependencies.

        Returns an iterable of dictionary objects with the following fields:
        {
            Path: <required> Workspace relative path
            Url: <required> Url of git repo
            Commit: <optional> Commit to checkout of repo
            Branch: <optional> Branch to checkout (will checkout most recent
                    commit in branch)
            Full: <optional> Boolean to do shallow or Full checkout.
                  (default is False)
            ReferencePath: <optional> Workspace relative path to git repo to
                           use as "reference"
        }
        """

        with open(os.path.join(
                  self.GetWorkspaceRoot(), 'Dependencies.yaml')) as d:
            repo_data = yaml.safe_load(d)

        return repo_data['base_deps']

    def GetPackagesPath(self):
        """
        Return a list of workspace relative paths that should be mapped as
        an edk2 packages path.
        """

        # Return the dependency paths
        # Modify this in the future if other paths are needed
        result = []
        for d in self.GetDependencies():
            result.append(d["Path"])
        return result

    def GetWorkspaceRoot(self):
        """Returns the workspace root directory path."""

        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
