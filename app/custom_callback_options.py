import os
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt.oauth.callback_options import  SuccessArgs, FailureArgs
from slack_bolt.response import BoltResponse
from app.helper import insert_bot_instance_credentials_to_db

env_path = Path('./..') / '.env'
load_dotenv(dotenv_path=env_path)

def success(args: SuccessArgs)->BoltResponse :
    """
    After Installation success, will insert the installation data 
    needed for sending messages to clients workspace.
    On query success redirects back to your app.
    """
    assert args.request is not None

    ## Insert current cred's into Customer object in your app DB
    wasp_res = insert_bot_instance_credentials_to_db(args.installation)

    if wasp_res.status_code == 200:
        base_url = os.environ["YOUR_APP_BASE_URL"]
        return BoltResponse(
            status=302,
            headers={"Location":f"{base_url}/settings/notifications?slack_installation=confirm"},
            body="TestBot is successfully installed!"
        )
    return BoltResponse(
        status=500,
        body="Error: Failed to save credentials to DB"
    )

def failure(args: FailureArgs) -> BoltResponse:
    assert args.request is not None
    assert args.reason is not None
    return BoltResponse(
        status=args.suggested_status_code,
        body=f"Error: {args.reason}"
    )
