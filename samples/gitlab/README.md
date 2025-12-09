# GitLab plugin sample

Demonstrates creating an issue (dry-run by default), listing issues, searching code, and fetching pipeline status using the GitLab plugin.

## Prerequisites

1. Install dependencies from repo root:
   ```bash
   pip install -e . -r requirements.txt
   ```
2. Set required environment variables:
   ```bash
   export GITLAB_TOKEN="<your-pat>"                 # scope: api (for create/comment) or read_api for read-only
   export GITLAB_PROJECT_ID="<namespace/project>"   # or numeric project id
   # Optional
   export GITLAB_BASE_URL="https://gitlab.example.com"
   export GITLAB_PIPELINE_REF="main"                # ref to fetch pipeline status
   export GITLAB_SAMPLE_DRY_RUN="true"              # default; set false to actually create an issue
   ```

## Run

```bash
python samples/gitlab/main.py
# or
# PYTHONPATH=. python samples/gitlab/main.py
```

Expected output outline:
- Issue creation prints dry-run payload (or created issue iid/url if dry-run disabled).
- Issue list prints a few open issues.
- Code search prints matching files/lines for `TODO`.
- Pipeline status prints latest pipeline info for the configured ref (or a no-results message).
