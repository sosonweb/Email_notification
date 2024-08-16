Test_notifications.py has test cases for send_email_notification method in main.py file.
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

Test cases :
    1. if recipients parameter list is not empty , email should be sent to the recipients email.
       - we verify if email_sender is 'githubactions@kp.org' and also if mta.kp.org is right and port number is 25
       - we make sure we sent the emails to recipients list :
           -  mock_smtp.assert_called_once_with('mta.kp.org', 25) 
       - method which verifies it, is in test_notifications.py file :
           def test_send_email_notification_with_all_vars(mock_smtp):
               mock_smtp_instance = mock_smtp.return_value
                mock_smtp_instance.sendmail = MagicMock()  // these 2 lines are to just mock smpt object so that real mails will not be sent.
       - how to test this :
           - change the email_sender from 'githubactions@kp.org' to anything else in main.py file , you will see assertion error.
           - Also change to_addrs=email_recipient to to_addrs='somthing' , assertion fails.
           - change mta.kp.org to org1 or something or change 25 to anything , it fails. 
           
    2 . if recipients parameter list is empty , we do not want to send emails to empty list. 
        if list is empty ,  we make sure smtp object is not initiated at all through this line :
            mock_smtp.assert_not_called()  # No SMTP actions should be performed
        - how to test this :
          - comment the return in send_email_notification method in main file :
               - else:
                  logging.info('No emails addresses configured.')
                  #return // commenting this in code will lead to execute next steos and send the emails
          - It will fail saying emails should not be sent in this case.
          
Possible Improvements:
       - we should provide proper values for env variables.
       - possibly check the message content also.
    
  
