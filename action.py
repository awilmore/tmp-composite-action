#!/usr/bin/env python3

import github
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

    # Get github params
    token = get_env_var('GITHUB_TOKEN')
    repo_name = get_env_var('GITHUB_REPOSITORY')
    #pr_number = get_env_var('', strict=False)

    # Create client
    gh = github.Github(token)
    print(' * Github client created:')
    print(gh)

    ## Display env vars
    #print(' * Displaying all env vars:')
    #show_all_env_vars()

    # Get event details
    event_json = read_event()
    print(' * event_json:')
    print(event_json)
    print()

    # List PR comments
#    if pr_number:
#        repo = gh.get_repo(repo_name)
#        pr = repo.get_pull(pr_number)
#
#    else:
#        print(' * No Pull Request number detected.')

    # Finished
    print()
    print(' * Done.')
    print()


# Read github event data
def read_event():
    # Find path
    event_path = gen_env_var('GITHUB_EVENT_PATH')

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


# TODO - remove:
# Display env vars
def show_all_env_vars():
    # Loop through env vars
    for env_name in sorted(os.environ):
        env_value = os.environ[env_name]
        print('%-25s = %s' % (env_name, env_value))


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
