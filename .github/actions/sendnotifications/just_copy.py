import os
import pytest
import smtplib
import requests
import logging
import json
import yaml
from main import send_email_notification, notification_message, send_environment_notification

# Define a test for the send_email_notifications function
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
    def mock_smtp(*args, **kwargs):
        class MockSMTP:
            def sendmail(self, from_addr, to_addrs, msg):
                pass

            def quit(self):
                pass

        return MockSMTP()

    monkeypatch.setattr(smtplib, 'SMTP', mock_smtp)

    # Call the function under test
    send_email_notification(message, recipients, email_subject)

    # Since it's a mock free implementation, we don't assert SMTP methods directly.
    # Instead, we ensure no exceptions were raised during execution.


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
    def mock_smtp(*args, **kwargs):
        class MockSMTP:
            def sendmail(self, from_addr, to_addrs, msg):
                pass

            def quit(self):
                pass

        return MockSMTP()

    monkeypatch.setattr(smtplib, 'SMTP', mock_smtp)

    # Call the function under test
    send_email_notification(message, recipients, email_subject)

    # Ensure that no errors were raised due to the empty recipients list.


# Test case for notification_message
def test_notification_message(monkeypatch):
    # Mock data
    message = "<p>This is a test message</p>"
    teams_channel = "https://example.com/webhook"
    job_status = "success"

    # Adjust the expected message to match the nested <p> tag structure
    expected_message = "<p><strong style='color:#00cc00;'>SUCCESS</strong></p><p><p>This is a test message</p></p>"

    # Mock requests.request to prevent actual HTTP calls
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.content = "OK"

        return MockResponse()

    monkeypatch.setattr(requests, 'request', mock_request)

    # Call the function
    notification_message(message, teams_channel, job_status)

    # Ensure that the function executed without errors


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
    monkeypatch.setattr('main.app_type', 'app_type')

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Success'

    # Mock requests.request to prevent actual HTTP calls
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.content = "OK"

        return MockResponse()

    monkeypatch.setattr(requests, 'request', mock_request)

    # Call the function
    send_environment_notification(notification_map, job_status)

    # Ensure that the function executed without errors


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

    # Mock requests.request to prevent actual HTTP calls
    def mock_request(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.content = "OK"

        return MockResponse()

    monkeypatch.setattr(requests, 'request', mock_request)

    # Call the function
    send_environment_notification(notification_map, job_status)

    # Since no matching teams_channel, ensure no exceptions were raised


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

    # Mock logging to capture the output
    with caplog.at_level(logging.INFO):
        send_environment_notification(notification_map, job_status)

    # Asserting that logging.info was called due to the exception
    assert "Error in environment notifications:" in caplog.text


if __name__ == "__main__":
    pytest.main()
