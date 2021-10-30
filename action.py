#!/usr/bin/env python3

from configparser import RawConfigParser
from sonarqube import SonarQubeClient

import github
import json
import os
import signal
import sys


###
# GLOBALS
###

SONAR_LOGO       = '![image](https://github.com/awilmore/tmp-composite-action/raw/master/images/sonar-logo-s.png'
SONAR_PROPERTIES = 'sonar-project.properties'
METRIC_KEYS      = 'coverage,code_smells,bugs'


###
# MAIN METHOD
###

def main():
    # Get event details
    event_json = read_event()
    pr_number = get_pull_request_number(event_json)

    if not pr_number:
        print(' * Not a pull request.')
        sys.exit()

    # Fetch sonar details
    results = fetch_sonar_results()

    # Generate PR comment
    comment_body = generate_comment_body(results)

    # Get github params
    token = get_env_var('GITHUB_TOKEN')
    repo_name = get_env_var('GITHUB_REPOSITORY')

    # Fetch PR details
    gh = github.Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Update PR with comment
    update_pr_comment(pr, comment_body)

    # Finished
    print()
    print(' * Done.')
    print()


# Update PR with sonar scan comment
def update_pr_comment(pr, comment_body):
    # Retrieve comments to avoid duplicates
    for c in pr.get_issue_comments():
        if c.body == comment_body:
            # Do not recreate duplicate comment
            print(' * Sonar scan results comment already exists')
            return

    # Note: new comments will be added each time scan results change
    print(' * Creating PR comment with sonar scan results')

    # Create sonar scan comment
    pr.create_issue_comment(comment_body)


# Create PR comment body
def generate_comment_body(results):
    # Begin comment
    comment = f'{SONAR_LOGO}  **Scan Results**:\n'

    for key in sorted(results):
        value = results[key]
        if key == 'coverage':
            value = f'{value}%'

        comment += f' * **{key}**: {value}\n'

    return comment.rstrip()


# Fetch sonar results
def fetch_sonar_results():
    # Get sonar project key
    sonar_project = read_sonar_project_key()

    # Get sonar details
    sonar_url = get_env_var('SONAR_HOST_URL')
    sonar_token = get_env_var('SONAR_TOKEN')

    # Create sonar client
    sonar = SonarQubeClient(sonarqube_url=sonar_url, token=sonar_token)

    # Find project details
    component = sonar.measures.get_component_with_specified_measures(component=sonar_project, version="dev-another-pr-1", fields="metrics,periods", metricKeys=METRIC_KEYS)
    measures = component['component']['measures']

    # Parse results
    results = {}
    for metric in measures:
        field = metric['metric']
        value = metric['value']
        results[field] = value

    # Check for coverage
    if 'coverage' not in results:
        results['coverage'] = 0

    # Return results
    return results


# Read sonar-project.properties file
def read_sonar_project_key():
    # Read sonar properties
    with(open(SONAR_PROPERTIES, 'r')) as f:
        for prop in [line.rstrip() for line in f]:
            name, value = prop.split('=')

            # Check property
            if name == 'sonar.projectKey':
                return value

    # Something went wrong
    print(f'error: sonar.projectKey value not found in sonar properties file: {SONAR_PROPERTIES}')
    sys.exit(1)


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
