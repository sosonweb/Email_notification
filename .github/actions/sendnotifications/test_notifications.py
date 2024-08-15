import pytest
import smtplib
from unittest.mock import patch, MagicMock
from main import send_email_notification  # Replace with your actual module name

# Test case for send_email_notification
@patch('main.smtplib.SMTP')  # Mock smtplib.SMTP
def test_send_email_notification(mock_smtp):
    # Mock data
    message = "<p>This is a test message</p>"
    recipients = ["test@example.com"]
    email_subject = "Test Subject"
    
    # Create a mock SMTP instance
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    # Call the function
    send_email_notification(message, recipients, email_subject)

    # Assert that SMTP was called correctly
    mock_smtp.assert_called_once_with('mta.kp.org', 25)
    
    # Check that sendmail was called with the correct parameters
    mock_smtp_instance.sendmail.assert_called_once_with(
        from_addr='githubactions@kp.org',
        to_addrs='test@example.com',
        msg=mock_smtp_instance.sendmail.call_args[1]['msg']
    )
    
    # Assert that quit was called
    mock_smtp_instance.quit.assert_called_once()

def test_send_email_notification_no_recipients(caplog):
    message = "<p>This is a test message</p>"
    recipients = []
    email_subject = "Test Subject"

    # Call the function
    with caplog.at_level(logging.INFO):
        send_email_notification(message, recipients, email_subject)

    # Assert that the appropriate log message was generated
    assert 'No emails addresses configured.' in caplog.text
  
