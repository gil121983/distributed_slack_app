# distributed_slack_app

## Distributed Slack application example with custom event listener for any app - using Bolt for python and Flask

## Installation

- Clone or download the repo.

- Inside the repo folder run:

        $pip3 install requirements.txt -r
        $python3 run.py

- Create an app at https://api.slack.com/apps using manifest.yml (don't forget to add your domain where needed).

- Integrate the "Add to Slack" button (from Manage Distribution page in your app settings) into your application UI.

- Change the button's href to pass customer id (or user id) on request's params

        `&{SLACK_APP_BASE_PATH}/slack/install?customer=${current_customer_id}`.

- Install the app to your workspace or test workspace.

- You can mention the app name on the installed channel to check connection is alive.
