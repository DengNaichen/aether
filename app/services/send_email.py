"""
Email service for sending transactional emails via Resend.

Supports both development (console logging) and production (actual emails).
"""

import logging

# from app.core.config import settings

logger = logging.getLogger(__name__)


# async def send_password_reset_email(email: str, reset_token: str) -> None:
#     """
#     Send a password reset email to the user via Resend.
#
#     In development (ENVIRONMENT=local): Logs to console
#     In production: Sends actual email via Resend API
#
#     Args:
#         email (str): The recipient's email address
#         reset_token (str): The plain password reset token (not hashed)
#
#     Raises:
#         Exception: If email sending fails in production
#
#     Example:
#         >>> await send_password_reset_email("user@example.com", "abc123xyz...")
#     """
#     # Build the reset link
#     # For iOS app deep link: aether://reset-password?token={reset_token}
#     # For web app: https://app.com/reset-password?token={reset_token}
#     reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
#
#     # Production mode: send via Resend
#     try:
#         import resend
#
#         resend.api_key = settings.RESEND_API_KEY
#
#         params = {
#             "from": f"{settings.EMAIL_FROM}",  # Update with your verified domain
#             "to": email,
#             "subject": "Reset your Aether password",
#             "html": _get_reset_email_html(reset_link),
#         }
#
#         email_response = resend.Emails.send(params)
#         logger.info(
#             f"Password reset email sent to {email} (ID: {email_response['id']})"
#         )
#
#     except Exception as e:
#         logger.error(f"Failed to send password reset email to {email}: {e}")
#         raise
#
#
# def _get_reset_email_html(reset_link: str) -> str:
#     """
#     Generate HTML template for password reset email.
#
#     Args:
#         reset_link (str): The password reset link with token
#
#     Returns:
#         str: HTML email content
#     """
#     return f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <meta charset="utf-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <style>
#             body {{
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#                 line-height: 1.6;
#                 color: #333;
#                 max-width: 600px;
#                 margin: 0 auto;
#                 padding: 20px;
#             }}
#             .container {{
#                 background-color: #ffffff;
#                 border-radius: 8px;
#                 padding: 40px;
#                 box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#             }}
#             h1 {{
#                 color: #2563eb;
#                 font-size: 24px;
#                 margin-bottom: 20px;
#             }}
#             .button {{
#                 display: inline-block;
#                 padding: 12px 24px;
#                 background-color: #2563eb;
#                 color: #ffffff;
#                 text-decoration: none;
#                 border-radius: 6px;
#                 margin: 20px 0;
#                 font-weight: 600;
#             }}
#             .footer {{
#                 margin-top: 30px;
#                 padding-top: 20px;
#                 border-top: 1px solid #e5e7eb;
#                 font-size: 14px;
#                 color: #6b7280;
#             }}
#             .warning {{
#                 background-color: #fef3c7;
#                 border-left: 4px solid #f59e0b;
#                 padding: 12px;
#                 margin: 20px 0;
#                 border-radius: 4px;
#             }}
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>Reset Your Password</h1>
#
#             <p>Hello,</p>
#
#             <p>We received a request to reset the password for your Aether Learning Platform account.</p>
#
#             <p>Click the button below to reset your password:</p>
#
#             <a href="{reset_link}" class="button">Reset Password</a>
#
#             <p>Or copy and paste this link into your browser:</p>
#             <p style="word-break: break-all; color: #6b7280; font-size: 14px;">{reset_link}</p>
#
#             <div class="warning">
#                 <strong>⏰ This link will expire in 1 hour.</strong>
#             </div>
#
#             <div class="footer">
#                 <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
#                 <p>For security reasons, never share this link with anyone.</p>
#                 <p>&copy; 2025 Aether Learning Platform. All rights reserved.</p>
#             </div>
#         </div>
#     </body>
#     </html>
#     """
