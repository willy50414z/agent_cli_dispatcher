## ADDED Requirements

### Requirement: Explicit project installer
The package SHALL provide an explicit CLI command named `install_delegant` that installs OpenSpec delegation guidance for the current project.

#### Scenario: Installer is invoked
- **WHEN** the user runs the OpenSpec delegation installer command from a project repository
- **THEN** the command installs delegation guidance into a project-local Codex instruction or rule surface
- **AND** the command reports the target file and selected delegation level

#### Scenario: Python package installation
- **WHEN** the user installs the Python package with `pip install`
- **THEN** the package installation does not modify Codex skills, project rules, or user-level Codex configuration
- **AND** delegation guidance is installed only after the user invokes the explicit installer command

#### Scenario: Existing project install
- **WHEN** the installer finds an existing managed OpenSpec delegation block in the project guidance file
- **THEN** the installer updates that managed block in place
- **AND** the installer does not duplicate the guidance

### Requirement: Delegation level selection
The installer SHALL support two delegation levels that control how aggressively OpenSpec apply delegates work to submodels.

#### Scenario: Level 1 selective delegation
- **WHEN** the user selects Level 1
- **THEN** Codex decides task-by-task whether delegation is cost-effective
- **AND** Codex may delegate selected low-risk draft, test, review, or diagnosis work to submodels
- **AND** Codex remains the primary implementer for tasks that are ambiguous, high-risk, or expensive to delegate

#### Scenario: Level 2 submodel-first implementation
- **WHEN** the user selects Level 2
- **THEN** the apply workflow prefers submodel implementation drafts for all eligible non-`codex-only` tasks
- **AND** Codex remains responsible for integration, final verification, and marking tasks complete
- **AND** Codex may override Level 2 when the task requires broad context, contains high-risk decisions, or produces unusable delegated output

#### Scenario: No explicit level supplied
- **WHEN** the installer is invoked without a selected level
- **THEN** the command prompts the user to choose Level 1 or Level 2 when interaction is available
- **AND** the command defaults to Level 1 only when running in a non-interactive mode that explicitly allows defaults

### Requirement: Task delegation tags
OpenSpec apply planning artifacts SHALL support lightweight task tags that describe delegation suitability without transferring completion authority away from Codex.

#### Scenario: Tagged DeepSeek draft task
- **WHEN** `tasks.md` contains a pending task tagged `[delegate:deepseek]`
- **THEN** the apply workflow treats the task as eligible for lower-cost implementation draft delegation
- **AND** Codex remains responsible for reviewing and integrating any returned output

#### Scenario: Tagged Codex-only task
- **WHEN** `tasks.md` contains a pending task tagged `[codex-only]`
- **THEN** the apply workflow keeps the task in the main Codex thread
- **AND** the task is not delegated to a submodel for implementation

#### Scenario: Untagged task
- **WHEN** `tasks.md` contains a pending task without a delegation tag
- **THEN** the apply workflow MAY classify it using the cost-first delegation policy
- **AND** the workflow MUST NOT assume that untagged tasks are automatically safe to delegate

### Requirement: Cost-first routing policy
The apply workflow SHALL prefer lower-cost delegation only for bounded, low-risk, verifiable work.

#### Scenario: Delegation is cost-effective
- **WHEN** a pending task is low-risk, has clear expected output, and can be described with a focused prompt packet
- **THEN** the apply workflow MAY delegate draft implementation, test drafting, review, or diagnosis to a lower-cost target
- **AND** the prompt packet includes only the task-specific context required to complete the delegated work

#### Scenario: Delegation would require broad context
- **WHEN** a pending task would require sending broad repository context comparable to the main Codex thread doing the work directly
- **THEN** the apply workflow keeps the task in Codex
- **AND** the workflow does not delegate merely because a delegation tag is present

#### Scenario: High-risk task
- **WHEN** a pending task involves architecture decisions, security boundaries, data migration, destructive operations, credentials, or OpenSpec state changes
- **THEN** the apply workflow keeps final implementation and decision authority in Codex
- **AND** any submodel use is limited to advisory analysis unless the user explicitly authorizes a broader workflow

### Requirement: Delegation authority boundaries
Submodels SHALL NOT decide final task completion, change OpenSpec scope, or mark OpenSpec tasks complete.

#### Scenario: Submodel returns implementation draft
- **WHEN** a delegated submodel returns a patch, edit plan, test draft, review finding, or diagnosis
- **THEN** Codex reviews the output before applying or relying on it
- **AND** Codex runs appropriate verification before marking the task complete

#### Scenario: Submodel attempts to mark task complete
- **WHEN** a delegated output includes changes to `tasks.md` task checkboxes
- **THEN** Codex treats those changes as unauthorized
- **AND** Codex does not accept the checkbox update without independent verification

### Requirement: Delegation fallback and escalation
The apply workflow SHALL continue safely when delegated execution is unavailable or unsuitable.

#### Scenario: Delegation target unavailable
- **WHEN** the selected submodel target or `agent-dispatch` backend is unavailable
- **THEN** the apply workflow falls back to Codex for the affected task
- **AND** records that delegation was skipped due to target unavailability

#### Scenario: Delegated output unusable
- **WHEN** a delegated attempt returns malformed, overly broad, stale, unverifiable, or repo-inconsistent output
- **THEN** Codex rejects the output and takes over the task
- **AND** the workflow avoids repeated delegated retries unless the failure is mechanical and clearly recoverable

### Requirement: Delegation audit trail
The apply workflow SHALL report delegation decisions clearly enough for the user to understand cost and quality trade-offs.

#### Scenario: Delegated task completes
- **WHEN** Codex completes a task using delegated draft work
- **THEN** Codex appends a delegation note to `tasks.md` recording the delegation target or mode, verification performed, and whether the output was integrated

#### Scenario: Delegation overridden
- **WHEN** Codex chooses not to delegate a tagged task or delegates an untagged task
- **THEN** Codex appends the override reason as a note to the relevant entry in `tasks.md`
