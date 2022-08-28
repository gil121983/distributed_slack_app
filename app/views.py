"""
Distributed Slack Application Example
(with external event listener to your app notifications)
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_bolt.oauth.callback_options import CallbackOptions
from slack_bolt.authorization.authorize import InstallationStoreAuthorize
from slack_bolt.context.context import BoltContext

from slack_sdk import WebClient
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from flask import request, jsonify, session, make_response
from app import flask_app
from app.custom_callback_options import success,failure
from app.helper import authenticate_bot, get_bot_from_installation_store

logging.basicConfig(level=logging.DEBUG)

env_path = Path('./..') / '.env'
load_dotenv(dotenv_path=env_path)

client_id=os.environ["SLACK_CLIENT_ID"]

oauth_settings = OAuthSettings(
    client_id=client_id,
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    installation_store=FileInstallationStore(
        base_dir="./app/data/installations", client_id=client_id),
    state_store=FileOAuthStateStore(
        expiration_seconds=600, base_dir="./app/data/states", client_id=client_id),
    callback_options=CallbackOptions(
        success=success, failure=failure),
    scopes=[
        "channels:read", "chat:write", "chat:write.public", "app_mentions:read", "incoming-webhook"],
    token_rotation_expiration_minutes=60*6, # Rotate tokens x minutes before expiration time
    )

bolt_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    oauth_settings=oauth_settings
    )
bolt_app.enable_token_revocation_listeners()
handler = SlackRequestHandler(bolt_app)

@bolt_app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()

## INSTALLATION OAUTH ENDPOINTS ##
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/slack/install", methods=["GET"])
def install():
    # customer_id should be sent from "Add to Slack" button
    session["customer"] = int(request.args.get("customer"))
    # Replace jwt_token with your application JWT cookie name 
    session["jwt"] = request.cookies.get("jwt_token")
    return handler.handle(request)

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)


## EXTERNAL EVENTS LISTENER ##
# This endpoint access should be restricted to your app api. 
# Should receives payloads - {enterprise_id:"",team_id:"",channel_id:"", bot_id:"", text:""}
@flask_app.route("/slack/notifications", methods=["POST"])
def wasp_events():
    request_data = request.get_json()
    text = request_data.get('text')
    channel_id = request_data.get('channel_id')

    bot = get_bot_from_installation_store(
        enterprise_id=request_data.get('enterprise_id'), 
        team_id=request_data.get('team_id')
        )
    
    authenticated_bot = authenticate_bot(
        bot=bot,
        request_data=request_data, 
        logger=bolt_app.logger, 
        installation_store=bolt_app.installation_store,
        )

    client=WebClient(bot['bot_token'])
    slack_response = client.chat_postMessage(
        token=authenticated_bot.bot_token, channel=channel_id, text=text)

    bolt_app.logger.debug(f"\033[96m{slack_response}\033[0m")
    response = make_response(
        jsonify({"ok": slack_response['ok'], }),slack_response.status_code,
        )
    response.headers["Content-Type"] = "application/json"
    return response
    

## RESPONSE TESTER ##
@bolt_app.event("app_mention")
def event_test(body, say, logger):
    logger.info(body)
    say("MyTestBot is Alive!")
