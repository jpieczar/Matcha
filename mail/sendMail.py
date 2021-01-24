import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com" #"smtp-relay.sendinblue.com"
PORT = 587
LOGIN = "thedragonknight777@gmail.com" #"pdpreez412@gmail.com"
PASSWORD = "waviurfrajacjdtj" #"m5Cd6BRTvYPSg0WX"
SENDER = "no_reply@matcha.com"

def sendVerificationMail(recipient, uid):
    subject = "Please verify your account"
    content = """
    <html>
    <p>Click the link below to verify your account.</p>
    <a href='http://localhost:5000/verify?email={}&uuid={}'>Matcha</a>
    </html>
    """.format(recipient, uid)
    sendMail(recipient, content, subject)

def sendPasswordMail(recipient, password):
    subject = "New Matcha password"
    content = """
    <html>
    <p>Your Matcha password has been reset. You will be able to log in with the following password: {}</p>
    </html>
    """.format(password)
    sendMail(recipient, content, subject)

def sendMail(recipient, content, subject):
    print("recipient", recipient)
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER
    message["To"] = recipient
    text = content
    part = MIMEText(text, "html")
    message.attach(part)
    with smtplib.SMTP(SMTP_SERVER, PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(LOGIN, PASSWORD)
        server.sendmail(SENDER, recipient, message.as_string())

