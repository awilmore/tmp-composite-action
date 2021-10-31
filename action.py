#!/usr/bin/env python3

from configparser import RawConfigParser
from sonarqube import SonarQubeClient

import github
import json
import os
import re
import signal
import sonarqube
import subprocess
import sys


###
# GLOBALS
###

SONAR_LOGO          = '![image](https://github.com/awilmore/tmp-composite-action/raw/master/images/sonar-logo-s.png) '
SONAR_PROPERTIES    = 'sonar-project.properties'
DEFAULT_METRIC_KEYS = ['coverage', 'code_smells', 'bugs']


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

    # Check for custom sonar metric keys
    sonar_metric_keys = check_sonar_metric_keys()

    # Fetch sonar details
    results = fetch_sonar_results(sonar_metric_keys)

    # Generate PR comment
    comment_body = generate_comment_body(results, sonar_metric_keys)

    # Get github params
    token = get_env_var('GITHUB_TOKEN')
    repo_name = get_env_var('GITHUB_REPOSITORY')

    # Fetch PR details
    gh = github.Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Update PR with comment
    update_pr_comment(pr, comment_body)


# Check if project uses custom metric keys via SONAR_METRIC_KEYS
def check_sonar_metric_keys():
    custom_keys = get_env_var('SONAR_METRIC_KEYS', strict=False)

    # Return defaults if no env var found
    if not custom_keys:
        return DEFAULT_METRIC_KEYS

    # Convert env var to list of metric keys
    key_list = custom_keys.split(',')
    return key_list


# Update PR with sonar scan comment
def update_pr_comment(pr, comment_body):
    # Retrieve most recent sonar scan comment to avoid duplicates
    recent_comment = ''
    for c in pr.get_issue_comments().reversed:
        if SONAR_LOGO in c.body:
            recent_comment = c.body
            break

    # Check if results in recent comment match
    if recent_comment == comment_body:
        # Do not recreate duplicate comment
        print(' * Sonar scan results comment already exists. No update.')
        return

    # Note: new comments will be added each time scan results change
    print(' * Creating PR comment with latest sonar scan results')

    # Create sonar scan comment
    pr.create_issue_comment(comment_body)


# Create PR comment body
def generate_comment_body(results, sonar_metric_keys):
    # Begin comment
    comment = f'{SONAR_LOGO}  **Scan Results**:\n'

    # Scan through in order of METRIC_KEYS
    for key in sonar_metric_keys:
        value = results[key]

        # Special treatment for 'coverage' metric key
        if key == 'coverage':
            value = f'{value}%'  # include percentage character

        comment += f' * **{key}**: {value}\n'

    return comment.rstrip()


# Fetch sonar results
def fetch_sonar_results(sonar_metric_keys):
    # Get sonar project key
    sonar_project = read_sonar_project_key()

    # Get sonar details
    sonar_url = get_env_var('SONAR_HOST_URL')
    sonar_token = get_env_var('SONAR_TOKEN')

    # Create sonar client
    sonar = SonarQubeClient(sonarqube_url=sonar_url, token=sonar_token)

    # Find project details
    metric_keys = ','.join(sonar_metric_keys)

    try:
        component = sonar.measures.get_component_with_specified_measures(component=sonar_project, version="dev-another-pr-1", fields="metrics,periods", metricKeys=metric_keys)
        measures = component['component']['measures']

    except sonarqube.utils.exceptions.NotFoundError as e:
        # Determine problematic field
        m = re.search('The following metric keys are not found: (.*)$', str(e))
        match = m.group(1)

        # Log error
        print(f'error: unknown sonar metric key set in SONAR_METRIC_KEYS: key={match}')
        print('reference: https://docs.sonarqube.org/latest/user-guide/metric-definitions/')
        sys.exit()

    # Parse results
    results = {}
    for metric in measures:
        field = metric['metric']
        value = metric['value']
        results[field] = value

    # Ensure value exists for each metric key to avoid KeyError exceptions
    for metric in sonar_metric_keys:
        if metric not in results:
            results[metric] = 0

    # Log results for action output
    print(f' * Sonar scan results: {results}')

    # Return results
    return results


# Read sonar-project.properties file
def read_sonar_project_key():
    # Get path to sonar properties
    workspace_path = get_env_var('GITHUB_WORKSPACE')
    sonar_properties = f'{workspace_path}/{SONAR_PROPERTIES}'

    # Read sonar properties
    with(open(sonar_properties, 'r')) as f:
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
