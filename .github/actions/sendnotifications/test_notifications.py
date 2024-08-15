import os
import pytest
from unittest.mock import patch, MagicMock
from your_module_name import send_email_notification  # Replace with your actual module name

# Define a test for the send_email_notification function
@patch.dict(os.environ, {
    'PROJECT_GIT_REPO': 'test-repo',
    'NOTIFICATION_MAP': '{"email_recipients": ["test@example.com"], "subject": "Test Subject", "message": "Test Message"}',
    'APP_TYPE': 'web',
    'BUILD_URL': 'http://build-url.com',
    'NOTIFY_FLAGS': '{"send-teams-notification": true}'
    'LOG_LEVEL': '20'
})
@patch('your_module_name.smtplib.SMTP')
def test_send_email_notification_with_all_vars(mock_smtp):
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

@patch.dict(os.environ, {
    'PROJECT_GIT_REPO': 'test-repo',
    'NOTIFICATION_MAP': '{}',
    'APP_TYPE': 'web',
    'BUILD_URL': 'http://build-url.com',
    'NOTIFY_FLAGS': '{"send-teams-notification": true}',
    'LOG_LEVEL': '20'
})
@patch('your_module_name.smtplib.SMTP')
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

@patch.dict(os.environ, {
    'PROJECT_GIT_REPO': 'test-repo',
    'NOTIFICATION_MAP': '{"email_recipients": ["test@example.com"], "subject": "Test Subject", "message": "Test Message"}',
    'APP_TYPE': 'web',
    'BUILD_URL': 'http://build-url.com',
    'NOTIFY_FLAGS': '{"send-teams-notification": true}',  # Empty notify flags
    'LOG_LEVEL': '20'
})
@patch('your_module_name.smtplib.SMTP')
def test_send_email_notification_with_empty_notify_flags(mock_smtp):
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

if __name__ == "__main__":
    pytest.main()
