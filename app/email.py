from threading import Thread
from flask_mail import Message
from app import app, mail
from flask import render_template

def send_async_email(app, message):
    with app.app_context():
        mail.send(message)

def send_email(subject, sender, recipients, text_body, html_body):
    message = Message(subject, sender=sender, recipients=recipients)
    message.body = text_body
    message.html = html_body
    Thread(target=send_async_email, args=(app, message)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Bibliophilia] Reset Your Password',
        sender=app.config['ADMINS'][0], 
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )
