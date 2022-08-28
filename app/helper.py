import os
import json
import requests
from pathlib import Path
from typing import Optional
from flask import session
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_bolt.context.context import BoltContext
from slack_bolt.authorization.authorize import InstallationStoreAuthorize
from slack_bolt.authorization.authorize_result import AuthorizeResult

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def insert_bot_instance_credentials_to_db(installation=None)->requests.Response:
    """
    Save installation data and default settings to current client in your db 
    by the client_id saved on session 
    (received from the "Add to Slack" button inside your application)
    """
    if installation == None:
        response = requests.Response()
        response.status_code = 400
        response.text = "Missing installation data"
        return response
    
    base_url = os.environ["YOUR_APP_BASE_URL"]
    api_endpoint = os.environ["YOUR_API_UPDATE_USER_ENDPOINT"]
    url=f"{base_url}{api_endpoint}{session['customer']}"
    enterprise = installation.enterprise_id if installation.is_enterprise_install else "none"
    
    data = {
        "integration_source":"slack",
        "customer_id":session["customer"],
        "is_slack_installed":True,
        "slack_details": {
            "enterprise_id": enterprise,
            "team_id": installation.team_id,
            "channel_id": installation.incoming_webhook_channel_id,
            "bot_id": installation.bot_id,
        },
        "slack_settings": {
            "on_new_finding" : True,
            "finding_severity" : 2,
            "on_new_auto_finding" : True,
            "auto_finding_severity" : 3, 
            "on_new_comment" : True,
            "on_status_change" : True,
            "on_new_asset" : True
        }        
    }

    headers = {
        "Content-Type":"application/json; charset=utf-8",
        "Accept":"*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":"keep-alive",
        "Authorization":f"Bearer {session['jwt']}",
        }

    return requests.put(url=url, json=data, headers=headers)


def get_bot_from_installation_store(enterprise_id:str=None,team_id:str=None)->dict:
    """
    Gets bot credentials from your file installation store
    """
    if enterprise_id is None:
        enterprise_id = "none"

    customer_bot_dir_name = f"{enterprise_id}-{team_id}"
    if "test" not in os.environ["YOUR_APP_BASE_URL"]:
        customer_bot_dir_name = f'{os.environ["SLACK_CLIENT_ID"]}/{customer_bot_dir_name}'
        
    work_dir = os.path.realpath(os.path.join(os.path.dirname(__file__)))
    json_file_path = f"{work_dir}/data/installations/{customer_bot_dir_name}/bot-latest"
    customer_bot_details = json.load(open(json_file_path,"r",encoding="utf-8"))
    return customer_bot_details


def authenticate_bot(bot=None, request_data=None, logger=None, installation_store=None)->Optional[AuthorizeResult]:
    """
    Call Slack API to authenticate request coming from your
    """
    client=WebClient(bot['bot_token'])
    
    bot_context = BoltContext({    
        "team_id":bot['team_id'],
        "enterprise_id":bot['enterprise_id'],
        "user_id": bot['bot_user_id'],
        "channel_id": request_data.get('channel_id'),
        })
    
    authorization = InstallationStoreAuthorize(
        logger=logger,
        installation_store=installation_store,
        client=client,
        client_id=os.environ.get("SLACK_CLIENT_ID"),
        client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
        bot_only=True,
        )

    auth_bot = authorization(
        context=bot_context, 
        team_id=bot['team_id'],
        enterprise_id=bot['enterprise_id'],
        user_id=bot['bot_user_id']
        )
    
    logger.debug(f"\033[96m{auth_bot}\033[0m")
    return auth_bot