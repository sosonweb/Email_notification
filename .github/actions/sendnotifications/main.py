import os
import yaml
import smtplib
import requests
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


repo_name = os.getenv('PROJECT_GIT_REPO')
notification_map_str = os.getenv('NOTIFICATION_MAP')
app_type = os.getenv('APP_TYPE')
build_url = os.getenv('BUILD_URL')
notification_flag = yaml.safe_load(os.getenv('NOTIFY_FLAGS'))
log_level = os.getenv('LOG_LEVEL') if os.getenv('LOG_LEVEL') else '20'
logging.basicConfig(level=int(log_level), format='%(asctime)s :: %(levelname)s :: %(message)s')

# hello
def main():
    notification_map_str = os.getenv('NOTIFICATION_MAP')
    notification_flag = yaml.safe_load(os.getenv('NOTIFY_FLAGS'))
    if not notification_map_str:
        logging.info('No notifications configured.')
        return
    else:
        notification_map = yaml.safe_load(notification_map_str)
        job_status = notification_map.get('build_status') or os.getenv('JOB_STATUS')
        if notification_map.get('app_props') and notification_map.get('app_props').get('notification_map'): 
            email_recipients = notification_map['app_props'].get('notification_map').get('email_recipients')
            teams_channel = notification_map['app_props'].get('notification_map').get('teams_channel')
        else:
            email_recipients = notification_map.get('email_recipients')
            teams_channel = notification_map.get('teams_channel')
        message_body = notification_map.get('message') if notification_map.get('message') else 'Github Actions Build Information'
        message_body += f"<p>Repository Name: {repo_name}<br>Build Status: {job_status}</p><p><a href='{build_url}'>Build link</a></p>"
        message_subject = notification_map.get('subject') if notification_map.get('subject') else 'Github Actions Notification'
        try:
            # teams webhooks and environment notifications
            if notification_flag['send-teams-notification'] == True:
                logging.info(f"Notify flag set to true.")
                if notification_map.get('environment_notifications') == True:
                    send_environment_notification(notification_map, job_status)
                else:
                    notification_message(message_body, teams_channel, job_status)
                    
            # email notifications            
            send_email_notification(message_body, email_recipients, message_subject)
        except Exception as e:
            logging.error(f'Error in send notification: {e}')
            

def send_email_notification(message, recipients, email_subject):
    if recipients and len(recipients) > 0:
        # logging.info(type(recipients))
        logging.info(f'[INFO] Sending emails notification to {recipients}.')
    else:
        logging.info('No emails addresses configured.')
        return
    msg = MIMEMultipart()
    email_sender = 'githubactions@kp.org'
    msg['Subject'] = email_subject
    msg['From'] = email_sender
    msg.attach(MIMEText(message, 'html'))
    s = smtplib.SMTP('mta.kp.org',25)
    for email_recipient in recipients:
        msg['To'] = email_recipient
        s.sendmail(from_addr=email_sender, to_addrs=email_recipient, msg=msg.as_string())
    s.quit()
    
    
def notification_message(message, teams_channel, job_status):
    if teams_channel and teams_channel != 'None':
        logging.info('[INFO] Sending MS Teams channel notification')
    else:
        logging.info('No teams channel configured.')
        return
    if job_status == 'success': job_color = '#00cc00'
    elif job_status == 'failure': job_color = '#ff0000'
    else: 
        job_color = '#00ff00'
        job_status = 'notify'
    headers = { 'Content-Type': 'application/json' }
    text = f"<p><strong style='color:{job_color};'>{job_status.upper()}</strong></p><p>{message}</p>"
    message_body = json.dumps({"text": text}).encode()
    post_webhook = requests.request("POST", teams_channel, data=message_body, headers=headers)
    logging.debug(f"{post_webhook.content}") 


def send_environment_notification(notification_map, job_status):
    try:
        app_type = os.getenv('APP_TYPE')
        deploy_env = notification_map.get('environment')
        env_notification_map = yaml.safe_load(os.getenv('ENV_NOTIFICATION_MAP'))
        print("env_notification_map ")
        print(env_notification_map)
        teams_channel = env_notification_map.get(app_type).get(deploy_env) if env_notification_map.get(app_type) else None
        print("teams channel ...")
        print(teams_channel)
        print(app_type)
        print(os.getenv('APP_TYPE'))
        if teams_channel:
            print("here I am ...")
            artifact_version = notification_map.get('artifact_name')
            custom_message = notification_map.get('message') if notification_map.get('message') else ""
            message = f"Environment: <b>{deploy_env}</b>, Application Type: <b>{app_type}</b>, Artifact Version : <b>{artifact_version}, Workflow status : <b>{job_status}</b>, <b>{custom_message}</b>"
            notification_message(message, teams_channel, job_status)
    except Exception as e:
        logging.info(f'Error in environment notifications: {e}')


if __name__ == '__main__':
    main()
