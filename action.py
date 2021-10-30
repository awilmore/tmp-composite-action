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

#    # Get github token
#    token = get_env_var('INPUT_TOKEN')
#    repo_name = get_env_var('GITHUB_REPOSITORY')
#
#    # Create client
#    gh = github.Github(token)
#    print(' * Github client created:')
#    print(gh)

    # Display env vars
    print(' * Displaying all env vars:')
    show_all_env_vars()

    # Finished
    print()
    print(' * Done.')
    print()


# Look up env var
def get_env_var(env_var_name, strict=True):
    # Check env var
    value = os.getenv(env_var_name)

    # Handle missing value
    if not value:
        if strict:
            print(f'error: env var not found: {env_var_name}')
            sys.exit(1)
        else:
            value = ''

    return value


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
