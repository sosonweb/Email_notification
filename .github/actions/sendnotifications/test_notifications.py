import os
import pytest
from unittest.mock import patch, MagicMock
from main import send_email_notification  # Replace with your actual module name
from main import notification_message
import logging

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
    
    # Call the function
    notification_message(message, teams_channel, job_status)

    # Assert that requests.request was called correctly
    mock_request.assert_called_once_with(
        "POST",
        teams_channel,
        data=b'{"text": "<p><strong style=\'color:#00cc00;\'>SUCCESS</strong></p><p>This is a test message</p>"}',
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


if __name__ == "__main__":
    pytest.main()
