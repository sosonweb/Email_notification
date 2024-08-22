import os
import pytest
import smtplib
import requests
import logging
import json
import yaml
from main import send_email_notification, notification_message, send_environment_notification

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
    sent_emails = []

    def mock_smtp(*args, **kwargs):
        class MockSMTP:
            def sendmail(self, from_addr, to_addrs, msg):
                sent_emails.append((from_addr, to_addrs, msg))

            def quit(self):
                pass

        return MockSMTP()

    monkeypatch.setattr(smtplib, 'SMTP', mock_smtp)

    # Call the function under test
    send_email_notification(message, recipients, email_subject)

    # Assertions
    assert len(sent_emails) == 1
    from_addr, to_addrs, msg = sent_emails[0]
    assert from_addr == 'githubactions@kp.org'
    assert to_addrs == "test@example.com"
    assert email_subject in msg
    assert message in msg


def test_send_email_notification_no_recipients(monkeypatch, caplog):
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
    sent_emails = []

    def mock_smtp(*args, **kwargs):
        class MockSMTP:
            def sendmail(self, from_addr, to_addrs, msg):
                sent_emails.append((from_addr, to_addrs, msg))

            def quit(self):
                pass

        return MockSMTP()

    monkeypatch.setattr(smtplib, 'SMTP', mock_smtp)

    # Call the function under test with logging capture
    with caplog.at_level(logging.INFO):
        send_email_notification(message, recipients, email_subject)

    # Assertions
    assert len(sent_emails) == 0  # Ensure no emails were sent
    assert "No emails addresses configured." in caplog.text  # Ensure the correct log message was generated


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


def test_send_environment_notification_exception_handling(monkeypatch, caplog):
    # Setting environment variables using monkeypatch with invalid YAML to trigger an exception
    monkeypatch.setenv('ENV_NOTIFICATION_MAP', 'invalid_yaml')
    monkeypatch.setenv('APP_TYPE', 'app_type')

    notification_map = {
        'environment': 'production',
        'artifact_name': 'v1.2.3',
        'message': 'Deployment successful!'
    }
    job_status = 'Failed'

    # Call the function with logging capture
    with caplog.at_level(logging.INFO):
        send_environment_notification(notification_map, job_status)

    # Asserting that logging.info was called due to the exception
    assert "Error in environment notifications:" in caplog.text


def test_generate_test_reports_html_report_path(monkeypatch):
    # Set up the test data
    build_var_map = {
        'args_test': 'npm test',
        'build_group': {
            'html-reports': {
                'pipeline-coverage-report': {
                    'report-dir': 'coverage-report-dir'
                }
            }
        }
    }

    # Mock the workspace path
    monkeypatch.setattr('main.workspace', '/fake/workspace')
    
    # Mock subprocess.check_output to simulate finding the HTML report directory
    mock_check_output = mock.Mock(return_value='/fake/workspace/coverage-report-dir\n')
    monkeypatch.setattr(subprocess, 'check_output', mock_check_output)
    
    # Mock os.system and logging.info
    mock_os_system = mock.Mock()
    monkeypatch.setattr('main.os.system', mock_os_system)
    
    mock_logging_info = mock.Mock()
    monkeypatch.setattr('main.logging.info', mock_logging_info)
    
    # Call the function under test
    generate_test_reports(build_var_map)
    
    # Assert that subprocess.check_output was called with the correct command
    mock_check_output.assert_called_once_with("find /fake/workspace -depth 1 -type d -name coverage-report-dir", shell=True, text=True)
    
    # Assert that logging.info and os.system were called correctly if the path is found
    mock_logging_info.assert_any_call('HTML report path /fake/workspace/coverage-report-dir')
    mock_os_system.assert_any_call("echo 'html-report-path=/fake/workspace/coverage-report-dir' >> $GITHUB_OUTPUT")

    # Modify the mock to simulate the case where no directory is found
    mock_check_output.return_value = ''
    
    # Call the function again to handle the "no HTML report produced" scenario
    generate_test_reports(build_var_map)
    
    # Assert that the appropriate log message is written
    mock_logging_info.assert_any_call("Test execution did not produce any HTML reports: ")



if __name__ == "__main__":
    pytest.main()
