#!/usr/bin/env python

import os
import click
import sys
import git
import json
import gitlptools
import subprocess

from lazr.restfulclient.errors import BadRequest
from launchpadlib.launchpad import Launchpad
from urllib.parse import urlparse
from tempfile import NamedTemporaryFile


def make_lp_api_url(url):
    parsed_url = urlparse(url)
    # noinspection PyProtectedMember
    new_url = parsed_url._replace(netloc="api.launchpad.net", path="/devel" + parsed_url.path)
    return new_url.geturl()


# mostly copypasta from git-lp-tools, but with some stuff thrown out
def git_lp_propose(lp, merge_target):
    # noinspection PyProtectedMember
    repo = gitlptools._get_this_repo()
    if repo.is_dirty():
        sys.exit(
            "ERROR: Uncommitted changes detected, please commit or stash.")

    merge_target = gitlptools.get_merge_target(repo, merge_target)

    lp_git_ref = gitlptools.LPGitRef.from_repo(repo)
    if lp_git_ref is None:
        sys.exit(
            "ERROR: Unable to find commit {} for {} on LP. "
            "Did you push it?".format(repo.active_branch.commit,
                                      repo.active_branch))

    lp_target_refs = gitlptools.get_lp_target_refs(lp, lp_git_ref, merge_target)
    print(
        "Proposing merge from {0.lp_path}:{0.lp_branch_name} → "
        "{1.repo}:{1.branch}".format(lp_git_ref, merge_target))

    if not lp_target_refs.target:
        sys.exit("ERROR: Cannot find ref for {}".format(merge_target.branch))

    commit_message = gitlptools.prompt_for_commit_message(repo, merge_target)
    if not commit_message:
        sys.exit("Empty commit message. Aborted!")

    try:
        mp = lp_target_refs.branch.createMergeProposal(
            merge_target=lp_target_refs.target,
            commit_message=commit_message,
            needs_review=True
        )
    except BadRequest as e:
        sys.exit("ERROR: {}".format(e.content.decode('utf-8')))
    else:
        print('Created MP: {}'.format(mp.web_link))
        mp.description = "Made with Ivan's Resplendent MP Reverter 9000"  # :-)
        mp.lp_save()


@click.command()
@click.option('--upstream', required=True,
              help='Name of the git upstream corresponding to your fork of the Launchpad repo.')
@click.option('--new-branch-suffix', required=True, help='Suffix of the branch name with a revert.')
@click.option('--mp-to-revert', required=True, help='URL of the merge proposal to revert.')
def revert_mp(upstream, new_branch_suffix, mp_to_revert):
    repo = git.Repo(os.getcwd())
    assert not repo.is_dirty()

    lp = Launchpad.login_with("ivans-resplendent-mp-reverter", "production", version="devel")
    # noinspection PyProtectedMember
    mp_data = json.loads(lp._browser.get(make_lp_api_url(mp_to_revert)).decode())

    merge_commit = mp_data["merged_revision_id"]  # merge commit ID
    assert merge_commit

    target_git_path = mp_data["target_git_path"]  # e.g., refs/heads/devel
    assert target_git_path

    branch_name = repo.git.rev_parse(target_git_path, abbrev_ref=True)
    print(f"Checking out {branch_name}...")
    repo.git.checkout(branch_name)

    print(f"Pulling...")
    repo.git.pull()

    new_branch_name = "-".join([branch_name, new_branch_suffix])
    print(f"Creating branch {new_branch_name}...")
    repo.git.checkout(b=new_branch_name)

    print(f"Reverting {merge_commit}...")
    repo.git.revert(merge_commit, m=1, no_edit=True)

    # Running the editor to amend the revert commit message.
    with NamedTemporaryFile(mode='w') as fh:
        fh.write(repo.head.commit.message)
        fh.flush()

        p = subprocess.Popen(['editor', fh.name])
        p.wait()

        repo.git.commit(amend=True, F=fh.name)

    print(f"Pushing to upstream {upstream}")
    repo.git.push(upstream, set_upstream=True)

    print("Proposing MP...")
    git_lp_propose(lp, f"origin/{branch_name}")
