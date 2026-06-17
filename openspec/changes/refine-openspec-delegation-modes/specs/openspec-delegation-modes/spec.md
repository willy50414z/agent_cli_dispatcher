## ADDED Requirements

### Requirement: Interactive delegation modes
The installer SHALL expose named OpenSpec delegation modes as the primary configuration interface.

#### Scenario: Interactive mode selection
- **WHEN** the user runs `agent-dispatch install_delegant` in an interactive terminal without specifying a mode
- **THEN** the command prompts the user to choose A, B, or C
- **AND** option A installs `main` mode
- **AND** option B installs `hybrid` mode
- **AND** option C installs `delegated-apply` mode

#### Scenario: Explicit main mode
- **WHEN** the user runs `agent-dispatch install_delegant --mode main`
- **THEN** the installed project guidance states that all OpenSpec apply work remains with the main model
- **AND** the guidance disables automatic submodel delegation unless the user explicitly asks for it later

#### Scenario: Explicit hybrid mode
- **WHEN** the user runs `agent-dispatch install_delegant --mode hybrid`
- **THEN** the installed project guidance states that the main model plans, integrates, validates, and updates OpenSpec task state
- **AND** the guidance requires propose-time assignment of delegate-friendly implementation, test, review, documentation extraction, repetitive edit, and diagnosis work to standalone delegate task packets
- **AND** the guidance requires apply-time delegation attempts for tagged delegate tasks before direct main-model implementation

#### Scenario: Explicit delegated apply mode
- **WHEN** the user runs `agent-dispatch install_delegant --mode delegated-apply`
- **THEN** the installed project guidance states that the main model may delegate the apply implementation to a submodel
- **AND** the guidance requires the main model to verify task completion, tests, and spec alignment before marking tasks complete

### Requirement: Compatibility level mapping
The installer SHALL preserve backward-compatible `--level` handling while promoting named modes.

#### Scenario: Level one compatibility
- **WHEN** the user runs `agent-dispatch install_delegant --level 1`
- **THEN** the command installs `hybrid` mode guidance
- **AND** the command reports the selected mode

#### Scenario: Level two compatibility
- **WHEN** the user runs `agent-dispatch install_delegant --level 2`
- **THEN** the command installs `delegated-apply` mode guidance
- **AND** the command reports the selected mode

#### Scenario: Conflicting mode and level
- **WHEN** the user supplies both `--mode` and `--level` with incompatible values
- **THEN** the command exits with an argument error
- **AND** the command does not modify the project guidance file

### Requirement: Propose-time delegate task packets
OpenSpec propose guidance SHALL split delegate-friendly work into standalone tasks with enough local context for a submodel to avoid reading all OpenSpec artifacts.

#### Scenario: Hybrid mode assigns delegate-friendly work
- **WHEN** `hybrid` mode is installed and a proposed implementation plan contains delegate-friendly implementation, test, review, documentation extraction, repetitive edit, or diagnosis work
- **THEN** the generated `tasks.md` assigns that work to standalone delegate task packets
- **AND** those task packets include an appropriate delegation tag
- **AND** those task packets include enough local context for a delegated model to start without reading every OpenSpec artifact

#### Scenario: Delegate-friendly work is split
- **WHEN** a proposed implementation plan contains bounded, low-risk, independently verifiable work suitable for a submodel
- **THEN** the generated `tasks.md` includes a standalone checkbox task for that work
- **AND** the task line includes an appropriate delegation tag

#### Scenario: Delegate task packet includes local context
- **WHEN** a generated task is intended for submodel delegation and local context can reduce token usage
- **THEN** the task MAY include indented `context`, `output`, and `verify` notes under the checkbox
- **AND** the checkbox line remains in the standard `- [ ]` format so OpenSpec task parsing remains intact

#### Scenario: Broad task remains with main model
- **WHEN** a task requires architecture decisions, scope decisions, security judgment, destructive operations, credentials, or broad repository context
- **THEN** the generated task is tagged `[codex-only]` or left for main-model classification
- **AND** the task is not split into a submodel packet merely to force delegation

### Requirement: Apply-time delegation-first hybrid behavior
Hybrid mode SHALL attempt delegation for tagged delegate tasks before the main model implements those tasks directly.

#### Scenario: Tagged delegate task is applied
- **WHEN** `hybrid` mode is installed and apply reaches a task tagged `[delegate:deepseek]`, `[delegate:test]`, or `[delegate:review]`
- **THEN** the main model attempts delegated execution before implementing the task directly
- **AND** the default shell delegation path uses `agent-dispatch run --target deepseek --prompt-file <packet>` unless the task packet names another target

#### Scenario: Main model wants to skip because task is small
- **WHEN** `hybrid` mode is installed and a tagged delegate task is small, trivial, or faster for the main model to do directly
- **THEN** that reason alone does not allow the main model to skip the delegated attempt

#### Scenario: Tagged delegate task cannot be delegated safely
- **WHEN** `hybrid` mode is installed and a tagged delegate task is high-risk, needs broad repository context, has no available delegation backend, or produces unusable delegated output after one attempt
- **THEN** the main model may take over
- **AND** the main model records the concrete skip or takeover reason near the relevant task in `tasks.md`

### Requirement: README hybrid responsibilities
The README SHALL document hybrid mode responsibilities clearly enough for users to understand which work remains with the main model and which work may be delegated.

#### Scenario: User reads hybrid mode docs
- **WHEN** the user reads the OpenSpec delegation installer documentation
- **THEN** the README lists main-model responsibilities for `hybrid` mode
- **AND** the README lists delegate-assigned work for `hybrid` mode
- **AND** the README identifies `hybrid` as the recommended delegation-first cost-control default
- **AND** the README states that tagged delegate tasks require a delegated attempt before direct main-model implementation
