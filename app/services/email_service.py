import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings


def send_reset_email(to_email: str, reset_code: str):
    """Отправка письма для восстановления пароля"""
    subject = "Восстановление пароля - DocShare"

    html = f"""
    <html>
    <body>
        <h2>Восстановление пароля</h2>
        <p>Вы запросили восстановление пароля.</p>
        <p>Ваш код для сброса пароля:</p>
        <h3 style="background: #f0f0f0; padding: 10px; display: inline-block;">
            {reset_code}
        </h3>
        <p>Этот код действителен в течение 15 минут.</p>
        <p>Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.</p>
    </body>
    </html>
    """

    send_email(to_email, subject, html)


def send_email(to_email: str, subject: str, html_content: str):
    """Общая функция отправки email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        print(f"Error sending email: {e}")
        # Не выбрасываем ошибку, чтобы не ломать API