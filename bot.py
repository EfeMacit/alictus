import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import main

#Below are the initialization of the slackapi
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

#Task4
#Notifying slack channel of general in order to post message which procedure is done
def notify_slack_channel(text: str):
    client.chat_postMessage(channel='#general', text=text)


@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id, text=text)

#Task5
#slack command of calculate_budget takes text parameter and passes it through calculate_budget_campaign method
@app.route('/calculate_budget', methods=['POST'])
def calculate_budget():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text')
    val = main.calculate_budget_campaign(text)
    client.chat_postMessage(channel=channel_id, text=val)#posting total budget of the campaign
    if text != None:
        print(text)
    return Response(), 200

#Bonus Task unfortunately i couldnt done that lack of time
@app.route('/CompareCampaigns', methods=['POST'])
def comparecampaigns():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text')
    client.chat_postMessage(channel=channel_id, text="compare camps")
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True)
