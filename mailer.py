import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple


class Mailer:
    def __init__(self, smtp_url: str, smtp_port: int, sender_email: str, sender_password: str, timeout=10):
        self.smtp_url = smtp_url
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.context = ssl.create_default_context()
        self.timeout = timeout

    def test_connection(self):
        try:
            with smtplib.SMTP(self.smtp_url, self.smtp_port, timeout=self.timeout) as server:
                server.starttls(context=self.context)
                server.login(self.sender_email, self.sender_password)
        except (socket.error, smtplib.SMTPException):
            return False
        return True

    def __create_email(self, to: str, subject: str, body: Tuple[str, str]):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to

        text_body, html_body = body
        mail_message = MIMEText(text_body, "plain")
        mail_html = MIMEText(html_body, "html")

        message.attach(mail_message)
        message.attach(mail_html)

        return message

    def send_email(self, to: str, subject: str, body: Tuple[str, str]):
        try:
            email = self.__create_email(to, subject, body)
            with smtplib.SMTP(self.smtp_url, self.smtp_port, timeout=self.timeout) as server:
                server.starttls(context=self.context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email, to, email.as_string()
                )
        except (socket.error, smtplib.SMTPException):
            return False
        return True

    def send_emails(self, recipients: [str], subject: str, body: Tuple[str, str]):
        if len(recipients) == 0:
            return
        try:
            with smtplib.SMTP(self.smtp_url, self.smtp_port, timeout=self.timeout) as server:
                server.starttls(context=self.context)
                server.login(self.sender_email, self.sender_password)
                for recipient in recipients:
                    email = self.__create_email(recipient, subject, body)
                    server.sendmail(
                        self.sender_email, recipient, email.as_string()
                    )
        except (socket.error, smtplib.SMTPException):
            return False
        return True
