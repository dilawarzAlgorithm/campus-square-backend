import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config.config import settings

def _send_otp_blocking(email_to: str, otp: str, user_name: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"{otp} is your Campus Square verification code"
        message["From"] = f"Campus Square <{settings.smtp_from_email}>"
        message["To"] = email_to

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Campus Square Account</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f5f6;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 500px;
                    margin: 40px auto;
                    background: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    border: 1px solid #eef0f2;
                }}
                .header {{
                    background-color: #1a1a1a;
                    padding: 32px 24px;
                    text-align: center;
                    color: #ffffff;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .content {{
                    padding: 40px 32px;
                    text-align: center;
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    line-height: 1.5;
                    margin-top: 0;
                    margin-bottom: 24px;
                    color: #555555;
                }}
                .otp-box {{
                    display: inline-block;
                    background: #f1f3f5;
                    color: #000000;
                    font-size: 36px;
                    font-weight: 800;
                    letter-spacing: 6px;
                    padding: 16px 32px;
                    border-radius: 12px;
                    margin: 16px 0 24px 0;
                    border: 1px dashed #ced4da;
                }}
                .footer {{
                    padding: 24px;
                    text-align: center;
                    font-size: 13px;
                    color: #868e96;
                    border-top: 1px solid #eef0f2;
                    background-color: #fcfdfe;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Campus Square</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Welcome to Campus Square! Use the secure verification code below to activate your account.</p>
                    <div class="otp-box">{otp}</div>
                    <p style="font-size: 14px; color: #868e96;">This code is strictly valid for 15 minutes. Please do not share this code with anyone.</p>
                </div>
                <div class="footer">
                    This is an automated security system notification. Please do not reply directly to this email.
                </div>
            </div>
        </body>
        </html>
        """
        
        part_html = MIMEText(html_content, "html")
        message.attach(part_html)

        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

        try:
            if settings.smtp_port == 587:
                server.starttls()
                
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        finally:
            server.quit()

    except Exception as error:
        return


async def send_otp_email(email_to: str, otp: str, user_name: str):
    if not settings.smtp_username or not settings.smtp_password:
        return

    await asyncio.to_thread(_send_otp_blocking, email_to, otp, user_name)