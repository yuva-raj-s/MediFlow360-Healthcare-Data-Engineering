# Branching Strategy
- `main`: Production code. Locked. PR required.
- `develop`: Integration branch.
- `feature/<jira-id>`: Developer branches. Merged into `develop`.
- `hotfix/<jira-id>`: Emergency fixes branched directly from `main`.