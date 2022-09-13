# Project Mu UEFI Variable Design

## Introduction

This document describes the Project Mu UEFI variable design. This design is meant to be extensible and easy to test.

As a result, the design involves a stronger use of interfaces and other software constructs than typically defined
in EDK II style drivers. Such separation supports:

- Better portability to C interoperable programming languages such as Rust
  - Cooperation of separate design parts across language boundaries
- Increased extensibility to introduce new design elements and extend instances of presently defined elements
- Isolated testing of individual parts of the design

To establish a lexicon used to identify individual entities that compose the overall variable design, a set of primary
design pieces are defined below and referenced throughout the remainder of the document and source repository.

## Zones

Zones are regions of the overall design in which residing elements share a common high-level responsibility and are
completely decoupled from other design areas. Control only transfers between zones across well-defined APIs. All data
transferred across zones is considered external and untrusted.

- `External` - Code outside the front-end and back-end.
  - All interaction with variable services occurs through externally defined interfaces.
- `Front-end` - Performs data validation and business logic. When data leaves the front-end, it has been validated
  and transformed to its final state for transfer to the back-end.
- `Back-end` - Handles moving data between the front-end and data destinations.

## Flows

The variable software stack moves data from an external caller to a store and from a store back to an external caller.

The direction of data movement from caller to store is called `input flow` and the movement back to the caller is
called `output flow`.

Some elements may perform the same actions regardless of flow. In other cases, flow will completely change how the
component behaves.

## Stages

As data progress within a zone, it is passed between `stages`. A stage is a container of `elements`. The duration of
execution for each element within the stage is called the element's `time`.

For example, in the `API stage`, three `validator` element instances might be present. During the stage, the three
validators are sequentially run against the variable data. The duration of time those three validators are running is
called the `API stage validation time`.

## Elements

As variable data moves in flows between zones, it is passes through stages which contain `elements`. The different
types of allowed elements are defined in this section.

### API

An `API` is a well-defined and stable interface.

### Cache

A `cache` is a special type of `store` with a pre-configured store policy to always serve as a volatile memory store
with _cache-like_ properties.

Each store may optionally have an associated cache.

### Gasket

A `gasket` is a data bridge between zones. A gasket does not modify the actual variable data (that is what a
`transformer` does). Instead, it modifies the _presentation_ of the data for compatibility between elements.

### Hook

A `hook` is simply a notification to subscribers that a `hook event` has occurred.

The following hook events are defined:

1. `Mutation Event` - An event issued before and after transformers operate on data.
2. `Status Event` - An event issued when external status data is produced.
3. `Validation Event` - An event issued at validation time in an input flow.

### Logger

A `logger` is a data sink for _types_ of operational messages and status.

Examples of loggers include:

- Debug output
- Tracing output
- Telemetry output

### Policy

`Policy` is an instantiation of data configuration for an element and the central method of defining data properties of
elements.

- `Policy Data` describes how an element should be configured
- `Policy Schema` describes how `Policy Data` should be organized

Many elements have policy to describe how they should operate. For example:

- `Hook Policy`
  - Configures hook parameters
- `Logger Policy`
  - Configures logging parameters
- `Router Policy`
  - Maps variables to stores
- `Store Policy`
  - Configures store properties
- `Transformer Policy`
  - Configures transformation parameters
- `Validator Policy`
  - Configures validator parameters

### Router

The `router` transfers data between the `front-end` and `back-end` of the variable design. This means the router maps
individual variable transactions that have finished being processed by the front-end to a store on the back-end.

### Store

A `store` is an instance of a variable data destination. _N_ instances of stores may exist.

Two general types of stores exist:

- `Concrete` - Directly manages the storage of the variable data on an underlying hardware storage device.
- `Proxy` - Proxies the data to another entity that ultimately stores the data in its final location.

Examples of concrete stores include:

- `Firmware Volume Block Storage`
  - A Firmware Volume Block device is often used as an abstraction within Platform Initialization (PI) firmware to
    a memory-mapped device such as SPI NOR flash. This is the primary storage path for most PCs today.
- `eMMC`
  - An Embedded Multi-Media Card (eMMC) NAND flash device.
  - Data is often stored on the Replay Protected Memory Block (RPMB) partition.
- `UFS`
  - A Universal Flash Storage (UFS) NAND flash device.
  - Data is often stored on the Replay Protected Memory Block (RPMB) LUN.

Examples of proxy stores include:

- `File System`
  - The store manages the data through a store chosen file system API.
  - The file system abstracts the underlying media type.
- `Network`
  - The store manages the data through a store chosen network interface.
- `Offload Engine`
  - The store moves data back and forth between a separate micro-controller such as a Baseboard Management Controller
    (BMC).

### Transformer

A `transformer` modifies variable data in transit in an `input flow` or `output flow` throughout the variable process.

Examples of transformers include:

- `Compressors` - Compress and decompress variable data.
- `Encryptors` - Encrypt and decrypt variable data.

### Trusted Execution Environments

A `Trusted Execution Environment (TEE)`, within the context of this design, is a secure processing area that can be
used to perform security-sensitive operations.

Example of TEEs include:

- ARM TrustZone
- x86 System Management Mode (SMM)

### Validator

A `validator` is responsible for verifying data against a well-defined set of requirements. Validators accept data as
input and return a boolean value as output indicating whether the data met the validator's requirements.

Examples of validators include:

- `API Validator` - Verifies API requirements are met.
- `Gasket Validator` - Verifies gasket requirements are met.
- `Security Validator` - Verifies variable security requirements are met.
- `Store Validator` - Verifies store requirements are met.
- `Transformer Validator` - Verifies transformation requirements are met.

## Variable Driver Theory of Operation

The variable driver accepts `variable data` as input and returns variable data as output. Variable data travels through
the driver stack in input and output `flows` between `zones`. Within zones, variable data is passed between `stages`
that contain `elements`. Elements are configured with `policy`. All active instances of an element are executed during
that element's `time` in the stage. Variable policy is platform-instantiated data that is validated against a
well-defined layout in a policy `schema`.

Throughout any flow, there are common behaviors to be aware of:

- `Loggers` output contextual information such as debug output, detailed tracing messages, telemetry data, and so on
  constantly as flows progress.
- `Stages` are composed of _N_ instances of elements for the stage type.
  - For example, a `validation stage` has _N_ validators invoked that are registered for that stage type.
- `Trusted Execution Environments (TEEs)` may be called to perform an operation within any stage. Invocation is
  specific to an element instance within a given stage and is not called out in this generic section.
  - For example, a `validator` may call into a TEE to perform authentication of an external caller.
  - A `hook` may call into a TEE to broadcast an event that has occurred during variable processing.
- `Validation Stages` only succeed if all validators within the stage return success.
  - If any validator returns failure, the variable transaction is aborted.
  - Each validation stage triggers a `validation hook event` that allows external validators to participate in that
    stage.

### Initialization Operation

Because this driver is initially targeting PI firmware, it will be loaded (via entry touch points) by the PI phase
dispatcher. Like all variable driver code, the initialization code should be written to minimize PI phase binding and
ease porting to other firmware frameworks or programming languages in the future.

During initialization, the driver configures elements by:

1. Running `policy validators` against `policies`
2. Binding policies against `elements`
3. Initializing elements for `stages`
4. Initializing any remaining elements
   - Examples:
     1. Publishing registration interfaces for subscribers to `hooks`
     2. Setting up `loggers` to their endpoints
5. Instructing the `router` to enumerate and account for `stores`
   - Stores perform self-initialization
6. Setting up `Trusted Execution Environments` per TEE-specific initialization requirements

### Write Operations

In a write flow, the `input flow` begins when variable data is introduced to the variable driver `front-end` through a
`user-facing API`. This starts the `API stage`. At `validation time` within the stage, stage associated validators
verify the API requirements are satisfied. If successful, the data may pass through a `gasket` in route to the
`security stage`. The validators in this stage verify all security properties required to make this transaction are
met.

The validated data is passed on to the `transformation stage` where transformers mutate the data according to their
transformation `policy`. As the data is modified, `mutation events` are produced. This allows external parties to
receive before and after views of the data as it is transformed.

Finally, the data reaches the `router stage`, the last stage of the front-end. The router sends the data to the
appropriate store(s) based on router policy.

Because the router sends the variable data in a single, well-defined format, after a `store` in the `back-end` gets
the data, it may be routed through a store gasket and then moved through validators before it goes to the
`storage stage` which contains the store-specific logic for storing the data.

Return from the storage stage begins the `output flow` of a write operation. The store returns the storage status back
to router. The router then checks if the store has an associated `cache`. If so, the router send the data to the cache.

The cache determines if the cache needs to be updated and returns the status to the router. The router returns the
overall status to the API stage which returns the status to the external caller.

### Read Operations

A read operation `input flow` begins when an external caller requests variable data via an external API. During
`validation time` in the `API stage`, validators check the read request. If it passes, the request may move through
a `gasket` to the `security stage`. If the security requirements for the variable read request are verified, the
request is passed to the `router stage`.

The `router` checks if the `store(s)` registered for the variable have a `cache` enabled. A cache is a special type of
variable store so some of the store logic described later applies at this point. If the variable is present in the
cache, the `output flow` begins and the cached data is returned to the caller.

If all of the store(s) associated with the variable are registered for caching and there were no cache hits, the output
flow begins and the router returns the variable was not found.

If any store(s) associated with the variable did not register for caching (and the variable was not found yet), the
router sends the request to the those store(s).

The store in the `back-end` may move the request through a gasket before it is subject to `store validators`. If the
store has the variable, the `output flow` begins and the variable data travels back to the router. The router double
checks that the store is not registered for caching (if it is, the data is sent to cache) and ultimately returns the
data to the external caller.

## Implementation Principles

Uniformity across recurring decision points throughout the implementation will lead to consistency that will improve
maintainability. This section provides generic guidance to help drive the overall development process.

### True Dependencies vs Implementation Dependencies

A common development error is misidentifying dependencies. Once the wrong dependency is baked in, it can cause
significant technical debt to accumulate over time working around the mistake.

For example, one incorrect dependency in the TianoCore UEFI variable driver was claiming that variable storage was
dependent on MMIO backed storage. The UEFI Specification does not mandate that UEFI variable storage must be MMIO
accessible, only that non-volatile storage is available. By directly placing a dependency on MMIO-backed storage,
instead of non-volatile storage, the driver became extremely cumbersome to adapt to new storage technologies.

#### Boot Phase Dependencies

Within the Platform Initialization (PI) architecture, some code is truly dependent on a boot phase. However, the vast
majority of code is not. Consider every interaction with a phase-dependent interface a "touch point". Every touch point
to a phase-specific interface anchors all code in the touch point to that phase.

Therefore, the touch point should be as small as possible. Within this implementation, touch points should only serve
as data connectors to the external API needed. Most of the variable implementation should be phase-agnostic up to a
minimal touch point that serves as an abstraction to the PI phase interface.

Library classes were invented to readily provide such abstractions. For example, `MemoryAllocationLib` abstracts common
memory allocation procedures from the implementation in the phase-specific core module. `DebugLib` abstracts debug
callers from underlying phase-specific code. There are many other examples. The underlying behavior of many modules
can be instantly swapped out without modifying their source code using library classes.

This Project Mu feature groups all UEFI variable related functionality into a single package. We should not hesitate
to use code grouping techniques like library classes to our advantage.

In any case, for maximum portability, phase-specific APIs should only be invoked from touch points.

### Static vs Dynamic Interfaces

UEFI and the PI Specs grant a lot of flexibility in combining source and binary components. When designing a new
interface, a common decision that needs to be made is whether to make the interface `static` or `dynamic`.

Sometimes the choice is obvious. Even so, there are some basic points to keep in mind to facilitate organizing code
behind these types of interfaces.

#### Static Linking

Modules are the static integration point. Modules combine functionality contained within source files local to the
module with that from libraries linked against the module.

As a general point, but especially within this implementation, local files are primarily used for orchestrating the
main control flow of the module. These files define _what_ the module must do and _when_ it must be done. An important
decision that must be made is choosing _how_ the work is done.

Whether the work is implemented in a module source file or library, it will be statically linked to the module. The
key separation a library provides is:

1. A separate INF file
2. Cohesive grouping of related functionality
3. Ability to add/remove functionality easily at build time by consuming packages

These are complementary. (2) allows related functionality to be kept and maintained together. Think about whether the
functionality is (or could be) decoupled enough from the main module that it could be used by other modules.

When designing a library, cohesion is critical. Consider whether the functionality were moved to another package. How
difficult would that be? For (3), determine whether a set of functionality would need to be swapped out based on a
platform decision. If the answer is yes, that is achievable with no modification to the original driver source code
with a library class.

(1) should be used to keep INFs focused on cohesive sets of dependencies needed for similar functionality. A bloated
INF with dependencies on completely unrelated features is an indicator of poor cohesion and higher maintenance cost.

### Dynamic Linking

Within dynamic linking, modules serve as producers and consumers of interfaces. PI dynamic linking (at least, at this
time), is essentially just locatable structures of function pointers stored in a firmware-wide global list.

Dynamic linking is particularly useful when:

- Producers and consumers are across binary deliverable boundaries
- N instances of an interface may exist
- An interface may optionally exist at runtime
- An interface may need to be modified at runtime (installed/uninstalled)
