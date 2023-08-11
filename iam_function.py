from urllib import response
from datetime import date
import requests
import boto3
import json
import sys
import random
import os

min_age = 70
max_age = 90
user_list = []
maxage_users = []
slackchannel = os.environ['slackchannel']
hook_url = os.environ['hook_url']
account_id = boto3.client("sts").get_caller_identity()["Account"]
vault_user = (f'vaultuser-{account_id}')
days_remain_all = []

def lambda_handler(event, context):
    client = boto3.client('iam')
    response = client.list_users()
    for x in response['Users']:
        if x['UserName'] !=  vault_user:
            user_list.append(x['UserName'])

    for username in user_list:
        res = client.list_access_keys(UserName=username)
        accesskeydate = res['AccessKeyMetadata'][0]['CreateDate'].date()
        currentdate = date.today()
        active_days = currentdate - accesskeydate
        days_remain = max_age - (active_days.days)
        if active_days.days > min_age:
            maxage_users.append(username)
            days_remain_all.append(days_remain)
            
    
    slack_notif()


def slack_notif():
    url = hook_url
    message = (f'Found users "{maxage_users}" in account "{account_id}" User keys expires in: "{days_remain_all}" days')
    title = (f"IAM Key Rotation:zap:")
    slack_data = {
        "username": "IAM_Key_Rotation",
        "icon_emoji": ":satellite:",
        "channel" : slackchannel,
        "attachments": [
            {
                "color": "#9733EE",
                "fields": [
                    {
                        "title": title,
                        "value": message,
                        "short": "false",
                    }
                ]
            }
        ]
    }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    if maxage_users:
        response = requests.post(url, data=json.dumps(slack_data), headers=headers)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
