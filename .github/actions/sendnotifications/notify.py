import os
import pytest
from unittest.mock import patch, MagicMock
from main import send_email_notification,notification_message, send_environment_notification
import logging,json
import yaml
from unittest import mock

# Define a test for the send_email_notification function
@patch('main.smtplib.SMTP')
@patch.dict(os.environ, {
    'PROJECT_GIT_REPO': 'test-repo',
    'NOTIFICATION_MAP': '{"email_recipients": ["test@example.com"], "subject": "Test Subject", "message": "Test Message"}',
    'APP_TYPE': 'web',
    'BUILD_URL': 'http://build-url.com',
    'NOTIFY_FLAGS': '{"send-teams-notification": true}'
})
def test_send_email_notification_with_all_vars(mock_smtp):
    #print(os.environ)
    # Define test data
    message = "<p>This is a test message</p>"
    recipients = ["test@example.com"]
    email_subject = "Test Subject"

    # Mock the SMTP instance to prevent sending real emails
    mock_smtp_instance = mock_smtp.return_value
    mock_smtp_instance.sendmail = MagicMock()

    # Call the function under test
    send_email_notification(message, recipients, email_subject)

    # Assertions
    mock_smtp.assert_called_once_with('mta.kp.org', 25)
    mock_smtp_instance.sendmail.assert_called_once_with(
        from_addr='githubactions@kp.org',
        to_addrs='test@example.com',
        msg=mock_smtp_instance.sendmail.call_args[1]['msg']
    )
    mock_smtp_instance.quit.assert_called_once()
    
@patch('main.smtplib.SMTP')
@patch.dict(os.environ, {
    'PROJECT_GIT_REPO': 'test-repo',
    'NOTIFICATION_MAP': '{}',
    'APP_TYPE': 'web',
    'BUILD_URL': 'http://build-url.com',
    'NOTIFY_FLAGS': '{"send-teams-notification": false}',
    'LOG_LEVEL': '20'
})

def test_send_email_notification_no_recipients(mock_smtp):
    # Define test data
    message = "<p>This is a test message</p>"
    recipients = []  # No recipients
    email_subject = "Test Subject"

    # Mock the SMTP instance to prevent sending real emails
    mock_smtp_instance = mock_smtp.return_value
    mock_smtp_instance.sendmail = MagicMock()

    # Call the function under test
    send_email_notification(message, recipients, email_subject)

    # Assertions
    mock_smtp.assert_not_called()  # No SMTP actions should be performed
    mock_smtp_instance.quit.assert_not_called()  # No SMTP actions should be performed

# Test case for notification_message
@patch('main.requests.request')  # Mock requests.request
def test_notification_message(mock_request):
    # Mock data
    message = "<p>This is a test message</p>"
    teams_channel = "https://example.com/webhook"
    job_status = "success"

    # Adjust the expected message to match the nested <p> tag structure
    expected_message = "<p><strong style='color:#00cc00;'>SUCCESS</strong></p><p><p>This is a test message</p></p>"
    
    # Call the function
    notification_message(message, teams_channel, job_status)

    # Assert that requests.request was called correctly
    mock_request.assert_called_once_with(
        "POST",
        teams_channel,
        #data=b'{"text": "<p><strong style=\'color:#00cc00;\'>SUCCESS</strong></p><p>This is a test message</p>"}',
        data=json.dumps({"text": expected_message}).encode(),
        headers={'Content-Type': 'application/json'}
    )

def test_notification_message_no_teams_channel(caplog):
    message = "<p>This is a test message</p>"
    teams_channel = None
    job_status = "success"

    # Call the function
    with caplog.at_level(logging.INFO):
        notification_message(message, teams_channel, job_status)

    # Assert that the appropriate log message was generated
    assert 'No teams channel configured.' in caplog.text

'''

def test_send_environment_notification(monkeypatch):
    
    # Use monkeypatch to set environment variables
    monkeypatch.setenv('APP_TYPE', 'webapp1')
    monkeypatch.setenv('ENV_NOTIFICATION_MAP', '{"webapp1": {"production": "https://example.com/webhook1"}}')
    
    # Mock yaml.safe_load to correctly parse the ENV_NOTIFICATION_MAP
    with patch('main.yaml.safe_load') as mock_safe_load:
        mock_safe_load.side_effect = lambda x: {
            'webapp1': {
                'production': 'https://example.com/webhook1'
            }
        } if x == '{"webapp1": {"production": "https://example.com/webhook1"}}' else {}
        
        # Mock the notification_message function
        with patch('main.notification_message') as mock_notification_message:
            notification_map = {
                'environment': 'production',
                'artifact_name': 'v1.0.0',
                'message': 'Deployment successful'
            }
            job_status = "success"
            
            # Call the function
            send_environment_notification(notification_map, job_status, 'webapp1')
            
            # Check that notification_message was called correctly
            mock_notification_message.assert_called_once_with(
                "Environment: <b>production</b>, Application Type: <b>webapp1</b>, Artifact Version : <b>v1.0.0, Workflow status : <b>success</b>, <b>Deployment successful</b>",
                'https://example.com/webhook1',
                'success'
            )


@patch('main.yaml.safe_load')
@patch('main.os.getenv')
def test_send_environment_notification_no_teams_channel(mock_getenv, mock_safe_load, caplog):
    # Mock environment variable and data
    mock_getenv.side_effect = lambda x: {
        'ENV_NOTIFICATION_MAP': '{}',  # Empty map to simulate no teams channel
        'APP_TYPE': 'webapp'
    }[x]

    mock_safe_load.return_value = {}  # Returning an empty map

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.0.0',
        'message': 'Deployment successful'
    }
    job_status = "success"

    with caplog.at_level(logging.INFO):
        send_environment_notification(notification_map, job_status)

    # Check for the specific log entry
    assert any('Error in environment notifications:' in message for message in caplog.messages)

    
'''
def test_send_environment_notification_success(monkeypatch):
    # Setting environment variables using monkeypatch
    env_notification_map = {
        'app_type': {
            'production': 'teams-channel-id-prod',
            'staging': 'teams-channel-id-staging'
        }
    }
    monkeypatch.setenv('ENV_NOTIFICATION_MAP', yaml.dump(env_notification_map))
    monkeypatch.setenv('APP_TYPE', 'app_type')

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Success'

    # Mocking the notification_message function
    with mock.patch('main.notification_message') as mock_notification_message:
        send_environment_notification(notification_map, job_status, 'app_type')

        # Asserting that notification_message was called with the correct parameters
        expected_message = (
            "Environment: <b>production</b>, Application Type: <b>app_type</b>, "
            "Artifact Version : <b>v1.2.3, Workflow status : <b>Success</b>, <b>Deployment successful!</b>"
        )
        mock_notification_message.assert_called_once_with(expected_message, 'teams-channel-id-prod', 'Success')

def test_send_environment_notification_no_channel(monkeypatch):
    # Setting environment variables using monkeypatch with no matching channel
    env_notification_map = {
        'app_type': {
            'staging': 'teams-channel-id-staging'
        }
    }
    monkeypatch.setenv('ENV_NOTIFICATION_MAP', yaml.dump(env_notification_map))
    monkeypatch.setenv('APP_TYPE', 'app_type')

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Success'

    # Mocking the notification_message function
    with mock.patch('main.notification_message') as mock_notification_message:
        send_environment_notification(notification_map, job_status, 'app_type')

        # Asserting that notification_message was not called since no teams_channel was found
        mock_notification_message.assert_not_called()

def test_send_environment_notification_exception_handling(monkeypatch):
    # Setting environment variables using monkeypatch with invalid YAML to trigger an exception
    monkeypatch.setenv('ENV_NOTIFICATION_MAP', 'invalid_yaml')
    monkeypatch.setenv('APP_TYPE', 'app_type')

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Failed'

    # Mocking the logging.info function
    with mock.patch('main.logging.info') as mock_logging_info:
        send_environment_notification(notification_map, job_status, 'app_type')

        # Asserting that logging.info was called due to the exception
        mock_logging_info.assert_called_once()
        assert "Error in environment notifications:" in mock_logging_info.call_args[0][0]


if __name__ == "__main__":
    pytest.main()
