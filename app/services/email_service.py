"""Email service for sending notifications."""
from flask import current_app, render_template_string
from flask_mail import Message

from app.extensions import mail


def send_email(to: str, subject: str, html_body: str, text_body: str = None):
    """
    Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: HTML content
        text_body: Plain text content (optional)
    """
    # Skip email sending if mail server is not configured (local development)
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.info(f"Email not sent (no mail server configured): {subject} -> {to}")
        return True  # Return True so app continues working

    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_body,
            body=text_body or html_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email send error: {e}")
        return False


def send_verification_email(user):
    """Send email verification link."""
    if not user.email:
        return False

    verify_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/verify/{user.email_verification_token}"

    subject = "Verify your email - Solio"

    html_body = render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; background: #0D0D0D; color: #FFFFFF; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #9945FF, #14F195); color: white; text-decoration: none; border-radius: 8px; }
            .footer { margin-top: 30px; color: #A0A0A0; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Solio!</h1>
            <p>Thank you for registering. Please verify your email by clicking the button below:</p>
            <p><a href="{{ verify_url }}" class="button">Verify Email</a></p>
            <p>If the button doesn't work, copy this link to your browser:</p>
            <p>{{ verify_url }}</p>
            <div class="footer">
                <p>This email was sent from the Solio platform. If you did not register, you can ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    ''', verify_url=verify_url)

    text_body = f'''
    Welcome to Solio!

    Thank you for registering. Please verify your email at:
    {verify_url}

    If you did not register, you can ignore this email.
    '''

    return send_email(user.email, subject, html_body, text_body)


def send_password_reset_email(user):
    """Send password reset link."""
    if not user.email:
        return False

    reset_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/reset-password/{user.password_reset_token}"

    subject = "Reset your password - Solio"

    html_body = render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; background: #0D0D0D; color: #FFFFFF; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #9945FF, #14F195); color: white; text-decoration: none; border-radius: 8px; }
            .warning { background: #1A1A1A; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 3px solid #FF6B6B; }
            .footer { margin-top: 30px; color: #A0A0A0; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Password Reset</h1>
            <p>We received a request to reset your password. Click the button below to set a new password:</p>
            <p><a href="{{ reset_url }}" class="button">Reset Password</a></p>
            <p>If the button doesn't work, copy this link to your browser:</p>
            <p>{{ reset_url }}</p>
            <div class="warning">
                <strong>This link expires in 30 minutes.</strong>
                <p>If you didn't request this, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>This email was sent from the Solio platform.</p>
            </div>
        </div>
    </body>
    </html>
    ''', reset_url=reset_url)

    text_body = f'''
    Password Reset

    We received a request to reset your password. Visit this link to set a new password:
    {reset_url}

    This link expires in 30 minutes.
    If you didn't request this, you can safely ignore this email.
    '''

    return send_email(user.email, subject, html_body, text_body)


def send_payout_notification(project, payout):
    """Send payout notification to project creator."""
    user = project.creator
    if not user.email:
        return False

    from app.utils.helpers import format_sol

    explorer_url = payout.explorer_url

    subject = f"Payout from project {project.title} - Solio"

    html_body = render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; background: #0D0D0D; color: #FFFFFF; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .highlight { color: #14F195; font-weight: bold; }
            .stats { background: #1A1A1A; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .button { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #9945FF, #14F195); color: white; text-decoration: none; border-radius: 8px; }
            .footer { margin-top: 30px; color: #A0A0A0; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Congratulations! 🎉</h1>
            <p>Your project <strong>{{ project.title }}</strong> has been successfully completed and funds have been paid out.</p>

            <div class="stats">
                <p>Total raised: <span class="highlight">{{ format_sol(payout.total_raised) }} SOL</span></p>
                <p>Platform fee (2.5%): {{ format_sol(payout.platform_fee) }} SOL</p>
                <p>Paid to you: <span class="highlight">{{ format_sol(payout.net_amount) }} SOL</span></p>
            </div>

            <p><a href="{{ explorer_url }}" class="button">View Transaction</a></p>

            <p>Thank you for using Solio!</p>

            <div class="footer">
                <p>This email was sent from the Solio platform.</p>
            </div>
        </div>
    </body>
    </html>
    ''', project=project, payout=payout, format_sol=format_sol, explorer_url=explorer_url)

    text_body = f'''
    Congratulations!

    Your project "{project.title}" has been successfully completed and funds have been paid out.

    Total raised: {format_sol(payout.total_raised)} SOL
    Platform fee (2.5%): {format_sol(payout.platform_fee)} SOL
    Paid to you: {format_sol(payout.net_amount)} SOL

    Transaction: {explorer_url}

    Thank you for using Solio!
    '''

    return send_email(user.email, subject, html_body, text_body)


def send_donation_notification(donation):
    """Send notification about new donation to project creator."""
    project = donation.project
    user = project.creator

    if not user.email:
        return False

    from app.utils.helpers import format_sol

    subject = f"New donation for {project.title} - Solio"

    html_body = render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; background: #0D0D0D; color: #FFFFFF; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .highlight { color: #14F195; font-weight: bold; }
            .message-box { background: #1A1A1A; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 3px solid #9945FF; }
            .footer { margin-top: 30px; color: #A0A0A0; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>New Donation! 💜</h1>
            <p>Your project <strong>{{ project.title }}</strong> received a new donation.</p>

            <p><span class="highlight">{{ format_sol(donation.amount_sol) }} SOL</span> from {{ donation.donor_display_name }}</p>

            {% if donation.message %}
            <div class="message-box">
                <strong>Message:</strong>
                <p>{{ donation.message }}</p>
            </div>
            {% endif %}

            <p>Currently raised: {{ format_sol(project.raised_sol) }} / {{ format_sol(project.goal_sol) }} SOL</p>

            <div class="footer">
                <p>This email was sent from the Solio platform.</p>
            </div>
        </div>
    </body>
    </html>
    ''', project=project, donation=donation, format_sol=format_sol)

    return send_email(user.email, subject, html_body)
