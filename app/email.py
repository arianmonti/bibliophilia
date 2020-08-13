from threading import Thread
from flask_mail import Message
from app import mail
from flask import current_app

def send_async_email(app, message):
    with app.app_context():
        mail.send(message)

def send_email(subject, sender, recipients, text_body, html_body):
    message = Message(subject, sender=sender, recipients=recipients)
    message.body = text_body
    message.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), message)).start()
