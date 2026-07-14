# Specification - Multi-Git Mirroring Follow-up

## Goal

Close the residual gap in Track 5 by making GitLab and Codeberg first-class,
independently configured mirrors and by distinguishing a skipped workflow from
a verified push.

## Requirements

1. Support `GITLAB_MIRROR_URL` and `CODEBERG_MIRROR_URL` independently while
   retaining the existing `GIT_MIRROR_URL` compatibility path.
2. Fail closed when a configured target has no private key or pinned SSH host
   key, and reject non-SSH mirror URLs.
3. Mirror all branches and tags, not only the triggering branch.
4. Emit a machine-readable target count in the workflow log and document the
   external GitLab repository/key setup gate.

## Acceptance

- The workflow has a safe no-target dry run.
- A configured target cannot silently skip because credentials are incomplete.
- Codeberg remains compatible with the current legacy secret configuration.
- GitLab is reported as pending until its repository and GitHub secrets exist.
- Focused workflow tests pass.
