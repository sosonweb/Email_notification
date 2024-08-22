import os
import pytest
from unittest.mock import patch, MagicMock
from main import send_email_notification, notification_message, send_environment_notification
import logging
import json
import yaml

# Define a test for the send_email_notification function
def test_send_email_notification_with_all_vars(monkeypatch):
    # Use monkeypatch to set environment variables
    monkeypatch.setenv('PROJECT_GIT_REPO', 'test-repo')
    monkeypatch.setenv('NOTIFICATION_MAP', '{"email_recipients": ["test@example.com"], "subject": "Test Subject", "message": "Test Message"}')
    monkeypatch.setenv('APP_TYPE', 'web')
    monkeypatch.setenv('BUILD_URL', 'http://build-url.com')
    monkeypatch.setenv('NOTIFY_FLAGS', '{"send-teams-notification": true}')

    # Define test data
    message = "<p>This is a test message</p>"
    recipients = ["test@example.com"]
    email_subject = "Test Subject"

    # Mock the SMTP instance to prevent sending real emails
    with patch('main.smtplib.SMTP') as mock_smtp:
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

def test_send_email_notification_no_recipients(monkeypatch):
    # Use monkeypatch to set environment variables
    monkeypatch.setenv('PROJECT_GIT_REPO', 'test-repo')
    monkeypatch.setenv('NOTIFICATION_MAP', '{}')
    monkeypatch.setenv('APP_TYPE', 'web')
    monkeypatch.setenv('BUILD_URL', 'http://build-url.com')
    monkeypatch.setenv('NOTIFY_FLAGS', '{"send-teams-notification": false}')
    monkeypatch.setenv('LOG_LEVEL', '20')

    # Define test data
    message = "<p>This is a test message</p>"
    recipients = []  # No recipients
    email_subject = "Test Subject"

    # Mock the SMTP instance to prevent sending real emails
    with patch('main.smtplib.SMTP') as mock_smtp:
        mock_smtp_instance = mock_smtp.return_value
        mock_smtp_instance.sendmail = MagicMock()

        # Call the function under test
        send_email_notification(message, recipients, email_subject)

        # Assertions
        mock_smtp.assert_not_called()  # No SMTP actions should be performed
        mock_smtp_instance.quit.assert_not_called()  # No SMTP actions should be performed

# Test case for notification_message
def test_notification_message(monkeypatch):
    # Mock data
    message = "<p>This is a test message</p>"
    teams_channel = "https://example.com/webhook"
    job_status = "success"

    # Adjust the expected message to match the nested <p> tag structure
    expected_message = "<p><strong style='color:#00cc00;'>SUCCESS</strong></p><p><p>This is a test message</p></p>"

    # Mock requests.request to prevent actual HTTP calls
    with patch('main.requests.request') as mock_request:
        # Call the function
        notification_message(message, teams_channel, job_status)

        # Assert that requests.request was called correctly
        mock_request.assert_called_once_with(
            "POST",
            teams_channel,
            data=json.dumps({"text": expected_message}).encode(),
            headers={'Content-Type': 'application/json'}
        )

def test_notification_message_no_teams_channel(monkeypatch, caplog):
    message = "<p>This is a test message</p>"
    teams_channel = None
    job_status = "success"

    # Call the function with logging capture
    with caplog.at_level(logging.INFO):
        notification_message(message, teams_channel, job_status)

    # Assert that the appropriate log message was generated
    assert 'No teams channel configured.' in caplog.text

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
    monkeypatch.setattr('main.app_type','app_type')
    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Success'

    # Mocking the notification_message function
    with patch('main.notification_message') as mock_notification_message:
        send_environment_notification(notification_map, job_status)

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
    with patch('main.notification_message') as mock_notification_message:
        send_environment_notification(notification_map, job_status)

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
    with patch('main.logging.info') as mock_logging_info:
        send_environment_notification(notification_map, job_status)

        # Asserting that logging.info was called due to the exception
        mock_logging_info.assert_called_once()
        assert "Error in environment notifications:" in mock_logging_info.call_args[0][0]

if __name__ == "__main__":
    pytest.main()
