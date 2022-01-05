# git-lp-revert-mp

A CLI tool for reverting changes made in a Launchpad merge proposal. Does roughly the following:

1. Given a link to a merge proposal (`--mp-to-revert`), figure out into which branch it was merged
2. Check that branch out and pull
3. Create a new branch (with the name being branch name + `--new-branch-suffix`)
4. Revert the merge commit
5. Push the new branch with the revert to upstream specified by `--upstream`
6. Create a new merge proposal against the same branch the original MP was merged into

## Installation

1. Clone the repo
2. `pip install --user .`

## Usage

```
git-lp-revert-mp \
  --upstream ivan \
  --new-branch-suffix revert-cool-feature \
  --mp-to-revert https://code.launchpad.net/~user_mcuserface/vapourware/+git/cool_repo/+merge/40000
```
