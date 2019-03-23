import smtplib
import ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_mail(to, html):

    sender_email = "my@gmail.com"
    password = "password"

    receiver_email = to

    message = MIMEMultipart("alternative")
    message["Subject"] = "WebTracker Update"
    message["From"] = sender_email
    message["To"] = receiver_email

    mail_message = MIMEText("Website updated", "plain")
    mail_html = MIMEText(html, "html")

    message.attach(mail_message)
    message.attach(mail_html)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def send_mails(recipients, data):
    for recipient in recipients:
        send_mail(recipient, data)
