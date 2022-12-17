import smtplib

try:
    server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
except:
    print('Something went wrong...')