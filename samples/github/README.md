### GitHub integration sample

This example shows how to use the GitHub plugin to exercise **all** GitHub skills:
listing issues/PRs, reading a file, creating/commenting/closing an issue,
and creating/merging a PR (write actions are opt-in).

### Dependencies

The default kernel does not contain the dependencies required for plugins, as it is lightweight.
For plugins to work, you need to install dependencies in your project yourself.

```requirements
PyGithub==2.3.0
```

Please use this commandline for install dependencies:

```commandline
pip install PyGithub
```

### Environments

To set up and run the example, use the following environment variables. They are necessary for proper
connection to GitHub.

```properties
GITHUB_TOKEN=ghp_xxx                      # required
GITHUB_REPO=owner/repo                    # optional override, e.g. octocat/Hello-World
GITHUB_FILE_PATH=README.md                # optional, path to read
GITHUB_FILE_REF=main                      # optional, branch/sha for file read

# Optional: enable write operations (creates issue & PR)
GITHUB_WRITE_ENABLED=1
GITHUB_ISSUE_TITLE=SidusAI sample issue
GITHUB_ISSUE_BODY=Created by the SidusAI GitHub sample.

# Required when write enabled and creating PR
GITHUB_PR_HEAD=feature-branch
GITHUB_PR_BASE=main
GITHUB_PR_TITLE=SidusAI sample PR
GITHUB_PR_BODY=Created by the SidusAI GitHub sample.
```

### Run

Execute the sample from the repository root:

```commandline
python samples/github/list_github_items.py
```

- Read-only actions (always run): list issues, list PRs, read a file.
- Write actions (when `GITHUB_WRITE_ENABLED=1`): create issue → comment → close, create PR → merge.
