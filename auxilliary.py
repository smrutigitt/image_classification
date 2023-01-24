# this file is for handling command line arguments
import argparse
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import smtplib
import ssl
import requests

config = configparser.ConfigParser()
config.read('config.ini')

def handling_argparse():
    parser = argparse.ArgumentParser(description='Argument to collct info')
    parser.add_argument('--account_id', help='account id for the user')
    parser.add_argument('--project_id', help='account id for the user')
    parser.add_argument('--email_id', help='email id for the user')
    parser.add_argument('--version', help='version to build and test')
    parser.add_argument('--last_version', help='base-model version for retraining')
    parser.add_argument('--action', help='test or train')
    parser.add_argument('--model_name', help='name of the model')
    parser.add_argument('--effnet_model_name', help='name of the model',default=None)
    args = parser.parse_args()
    arg_dir = {
        "account_id" : args.account_id,
        "project_id" : args.project_id,
        "email_id"   : args.email_id,
        "version" : args.version,
        "last_version" : args.last_version,
        "action" : args.action,
        "model_name" : args.model_name,
        "effnet_model_name" : args.effnet_model_name
    }
    return arg_dir

def email_notification(arg_dic, failure_reason=None, user = False):
    email_sender = config['Email config']['email_id']
    email_username = config['Email config']['username']
    email_password = config['Email config']['password']
    host = config['Email config']['host']
    port = int(config['Email config']['port'])
    msg = MIMEMultipart('alternative')
    msg['From'] = email_sender

    model_name = arg_dic['model_name']
    if failure_reason is None:
        email_receiver = arg_dic['email_id']
        
        msg['Subject'] = f"Your model {model_name} is trained successful. "
        
        body = f"""<p>Dear {email_receiver.split("@")[0].capitalize()},</p>

    <p>Your model training is completed successfully. Please click the link below to test the model.</p>

    <p><a href={config['Email config']['test_model_url'].format(arg_dic['account_id'],arg_dic['project_id'])}>Model Testing</a></p>


    <p>If you need further assistance please feel free to contact us at info@saraagh.com.</p>


    Cheers!<br>
    Team Saaragh
    """
    elif failure_reason is not None and not user:
        email_receiver = config['Email config']['failure_receiver']
        
        msg['Subject'] = f"Model training failed"
        build_number = requests.get(config['Jenkins config']['buildno_url'],headers={'Authorization': config['Jenkins config']['Authorization']}).text
        
        body = f"""<p>Dear VA DEVs,</p>

    <p>Model training failed for the account: {arg_dic['account_id']}, project_id: {arg_dic['project_id']}.</p>
    <p>Faliure reason: {failure_reason}.</p>

    <p>For more deails, refer the console log of last build</p>

    <p><a href="http://3.229.179.40:8080/job/live-training-server-GPU/{build_number}/consoleText/">Console log for last build</a></p>


    Cheers!<br>
    Team Saaragh
    """
    elif failure_reason is not None and user:
        email_receiver = arg_dic['email_id']
        
        msg['Subject'] = f"Training failed for your model {model_name}"
        
        if "Datasets has invalid images" in failure_reason: 
            body = f"""<p>Dear {email_receiver.split("@")[0].capitalize()},</p>

    <p>Your model training was not successful. {failure_reason}</p>

    <p><a href={config['Email config']['test_model_url'].format(arg_dic['account_id'],arg_dic['project_id'])}>Model Training</a></p>


    <p>If you need further assistance please feel free to contact us at info@saraagh.com.</p>


    Cheers!<br>
    Team Saaragh
    """
        else:
            body = f"""<p>Dear {email_receiver.split("@")[0].capitalize()},</p>

    <p>Your model training was not successful. Please try again after a few minutes.</p>

    <p><a href={config['Email config']['test_model_url'].format(arg_dic['account_id'],arg_dic['project_id'])}>Model Training</a></p>


    <p>If you need further assistance please feel free to contact us at info@saraagh.com.</p>


    Cheers!<br>
    Team Saaragh
    """
    msg['To'] = email_receiver
    msg_body = MIMEText(body,'html')
    msg.attach(msg_body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context) as smtp:
        smtp.login(email_username, email_password)
        smtp.sendmail(email_sender, email_receiver, msg.as_string())


def update_status(status: str, account_id: str, project_id: str, model_name:str):
    api_url = config['Basic config']['update_status_api'].format(account_id,model_name,project_id)
    payload = json.dumps({"status": status})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=api_url,headers=headers, data=payload)
    return response.status_code
