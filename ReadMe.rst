Project Mu UEFI Variables
=========================

This repository contains a prototype for a new UEFI variable design for modern PCs.

It is extensible, secure, with built-in testing up and down the entire stack. The design and implementation are all
taking place here in this repo.

Project Mu Top-Level information
________________________________

This repository is part of Project Mu. Please see Project Mu for details: https://microsoft.github.io/mu.

Current Project Status
______________________

This project is not actively being developed. There are plans to implement the design currently shown in this
repo in the future and those will be shared on the repo when finalized.

Contributing
============

We welcome everyone to file feature requests, bugs, participate in code reviews, submit code, update documentation,
and help us build the best variable driver possible.

At this time, we are very early in the work so we're particularly interested in ideas around the future of UEFI
variables (including breaking UEFI specification compatibility) and suggestions to help shape the overall design.

Please open GitHub issues directly in this repo.

Background
==========

The UEFI Specification describes an interface between the operating system (OS) and platform firmware. A UEFI
Specification compliant system must implement two high-level sets of services - Boot Services which consist of
functions available prior to a successful call to ``EFI_BOOT_SERVICES.ExitBootServices()`` and Runtime Services which
consist of functions that are available before and after any call to ``EFI_BOOT_SERVICES.ExitBootServices()``.

A fundamental Runtime Service is called the UEFI variable services. These services are comprised of an API that the
platform firmware must implement to satisfy the relevant API requirements defined in the UEFI Specification. While the
underlying implementation is platform-specific, the callers will include both the operating system and firmware
components.

Motivation
==========

The de facto open-source implementation of UEFI, `TianoCore`_, provides a commonly used set of `UEFI variable drivers`_
in the `edk2`_ project that has served as the industry standard implementation for UEFI variable services for over a
decade. Over time, the UEFI variable driver has substantially grown in complexity to support an increasing number of
features.

The TianoCore driver is now over 15 years old. It's design is rigid and not accommodating to change. Over the span of
its lifetime, many advancements have occurred in the PC industry that require better scale to support:

1. New storage technologies have come to market
2. Device trends have shifted to low-power ultra mobile devices and cloud server systems
3. New offload engines like BMC and special security processors have become more common to process non-volatile data
4. New expectations around device security have come into focus

   - For example, resistance against physical attack has led to variable data confidentiality via encryption, data
     integrity checks for tamper-proof storage guarantees, data replay protection, etc.
5. Additional computer architectures have gained popularity such as AArch64 and RISC-V
6. Operating systems have evolved and so have their security expectations

The TianoCore driver was written for a PI-centric boot flow assuming it was writing to SPI flash with no structured
design to support extending the driver to support these advancements. In addition, while some industry standard tests
such as the UEFI Self-Certification Tests exist, much of the stack is error prone to modify and difficult to assess
because of its accumulated technical debt.

Due to the importance of the driver, we concluded that a new design that takes into account these requirements with
testing built in could better support today's needs.

Code of Conduct
===============

This project has adopted the Microsoft Open Source Code of Conduct https://opensource.microsoft.com/codeofconduct/

For more information see the Code of Conduct FAQ https://opensource.microsoft.com/codeofconduct/faq/
or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`_. with any additional questions or comments.

Builds
======

Please follow the steps in the Project Mu docs to build for CI and local testing.
`More Details <https://microsoft.github.io/mu/CodeDevelopment/compile/>`_

Copyright & License
===================

Some files in this repository have their own copyright. Otherwise, the following copyright applies.

| Copyright (C) Microsoft Corporation
| SPDX-License-Identifier: BSD-2-Clause-Patent

.. _edk2: https://github.com/tianocore/edk2
.. _TianoCore: https://www.tianocore.org/
.. _UEFI variable drivers: https://github.com/tianocore/edk2/tree/master/MdeModulePkg/Universal/Variable
