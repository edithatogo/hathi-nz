# Specification: Shared Code-Scanning Gate Rollout

## Overview

This track coordinates the rollout of the shared org-level code-scanning gate action across all affected repositories. The goal is to remove repo-local alert-checking scripts, standardize on the pinned shared action in `edithatogo/.github`, and keep every consumer repo tied to a Conductor-visible GitHub issue.

The rollout applies to repositories that run CodeQL or Scorecard workflows and should fail on open high/critical alerts. The enforcement mechanism is the shared action pinned to:

- `edithatogo/.github/.github/actions/code-scanning-gate@90b399a731a17b792352d0c049834a22dbd32523`

## Goals

- Create one Conductor track that owns the rollout plan and completion evidence.
- Create one GitHub issue per affected repository so each repo has an explicit local action item.
- Ensure every affected workflow references the shared org action, not a repo-local Python script.
- Keep the gate behavior consistent across CodeQL and Scorecard workflows.
- Preserve fail-closed behavior for high and critical code-scanning alerts.
- Record the repository list, issue numbers, and verification status in Conductor metadata.

## Repository Set

Affected repositories identified for the rollout:

- `edithatogo/anz-legislation`
- `edithatogo/apfs-rs`
- `edithatogo/authentext`
- `edithatogo/corpus-cases-medilegal-nz`
- `edithatogo/corpus-legislation-nz`
- `edithatogo/corpus-nz-hansard`
- `edithatogo/dnz`
- `edithatogo/fyi-archive`
- `edithatogo/fyi-cli`
- `edithatogo/gtpcnz`
- `edithatogo/kairos`
- `edithatogo/mars`
- `edithatogo/mchs`
- `edithatogo/microsim_oa`
- `edithatogo/nz-legislation`
- `edithatogo/osf-cli-go`
- `edithatogo/pacx`
- `edithatogo/postiz`
- `edithatogo/reimbursement-atlas`
- `edithatogo/sourceright`
- `edithatogo/vcpkg`
- `edithatogo/voiage`

## Functional Requirements

- Each repository must have a GitHub issue that captures the local workflow follow-up.
- Each issue should ask for workflow verification against the shared action and removal of any repo-local gate scripts.
- Repositories with multiple workflows should verify every relevant workflow file.
- If a repo keeps any local gate helper, that helper must be justified and documented.
- The shared action should remain pinned to a commit SHA.

## Acceptance Criteria

- Every affected repository has an associated GitHub issue.
- Every affected workflow uses the pinned shared gate action.
- No remaining workflow depends on a repo-local `check_code_scanning_alerts.py` script for gate enforcement.
- The Conductor track records the final repo-to-issue mapping.
- If GitHub search lags behind, direct file verification is still recorded as the source of truth.

## Out Of Scope

- Changing the underlying CodeQL or Scorecard scanners.
- Reworking unrelated CI jobs.
- Creating additional repo-local alert-checking scripts.

