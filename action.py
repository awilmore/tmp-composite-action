#!/usr/bin/env python3

import github
import json
import os
import signal
import sys


###
# MAIN METHOD
###

def main():
    print()
    print(' * Composite action test')
    print()

    # Get event details
    event_json = read_event()
    pr_number = get_pull_request_number()

    if not pr_number:
        print(' * Not a pull request.')
        sys.exit()

    print(f' * PR NUMBER: {pr_number}')

    # Get github params
    token = get_env_var('GITHUB_TOKEN')
    repo_name = get_env_var('GITHUB_REPOSITORY')

    # Fetch PR details
    gh = github.Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    print(' * PR:')
    print(pr)

    # Finished
    print()
    print(' * Done.')
    print()


# Get PR number from event details
def get_pull_request_number(event_json):
    # Inspect json payload
    if 'pull_request' in event_json:
        pr = event_json['pull_request']

        if 'number' in pr:
            return int(pr['number'])

    # Not a PR
    return 0


# Read github event data
def read_event():
    # Find path
    event_path = get_env_var('GITHUB_EVENT_PATH')

    # Read json contents
    with open(event_path, 'r') as f:
        json_data = json.load(f)

    return json_data


# Look up env var
def get_env_var(env_var_name, strict=True):
    # Check env var
    value = os.getenv(env_var_name)

    # Handle missing value
    if not value:
        if strict:
            if env_var_name == 'GITHUB_TOKEN':
                print(f'error: env var not found: {env_var_name}')
                print('''please ensure your workflow step includes
                env:
                    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}''')
                sys.exit(1)

            else:
                print(f'error: env var not found: {env_var_name}')
                sys.exit(1)

    return value


# Handle interrupt
def signal_handler(_, __):
    print(' ')
    sys.exit(0)


####
# MAIN
####

# Set up Ctrl-C handler
signal.signal(signal.SIGINT, signal_handler)

# Invoke main method
if __name__ == '__main__':
    main()
