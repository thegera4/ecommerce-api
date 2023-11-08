from fastapi import (BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status)
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import dotenv_values
from pydantic import BaseModel, EmailStr
from typing import List
from models import User
import jwt


credentials = dotenv_values(".env")

config = ConnectionConfig(
    MAIL_USERNAME=credentials["EMAIL"],
    MAIL_PASSWORD=credentials["PASSWORD"],
    MAIL_FROM=credentials["EMAIL"],
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True

)


async def send_email(email: List, instance: User):
    token_data = {"id": instance.id, "username": instance.username}
    token = jwt.encode(token_data, credentials["SECRET"], algorithm="HS256")
    template = f"""
                <!DOCTYPE html>                
                <html>
                    <head>
                        
                    </head> 
                    <body> 
                     <div style="display: flex; align-items: center; justify-content: center; flex-direction: column"> 
                      <h3>Account Verification</h3> 
                      </br> 
                      <p>Thanks for choosing our shop. 
                        Please click the link below to verify your account</p> 
                      <a style="margin-top: 1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; 
                      text-decoration: none; background: #0275d8; color: white;"
                      href="http://localhost:8000/verification/?token={token}">
                        Verify your account
                      </a> 
                      <p>Please ignore this email if you did not register in our Shop. Thanks</p>
                     </div> 
                    </body> 
                </html>
                """
    message = MessageSchema(
        subject="Shop Account Verification Email",
        recipients=email,  # List of recipients
        body=template,
        subtype="html"
    )
    fm = FastMail(config)
    await fm.send_message(message=message)
