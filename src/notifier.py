"""
Notification module.
Sends the diagram URL via email, webhook, or iOS-compatible methods.
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import httpx


async def notify_email(subject: str, html_url: str, summary: str) -> bool:
    """Send an email notification with the diagram link."""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("NOTIFY_EMAIL")

    if not all([user, password, to_addr]):
        print("[notifier] Email not configured. Skipping.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Multi-AI Diagram] {subject}"
    msg["From"] = user
    msg["To"] = to_addr

    text_body = f"""Multi-AI Diagram Report
===========================
{summary}

View diagram: {html_url}
"""

    html_body = f"""\
<html>
<body style="font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px;">
  <h2 style="color: #22c55e;">Multi-AI Diagram Report</h2>
  <p>{summary}</p>
  <p style="margin-top: 20px;">
    <a href="{html_url}"
       style="background: #3b82f6; color: white; padding: 12px 24px;
              border-radius: 8px; text-decoration: none; font-weight: 600;">
      View Diagram
    </a>
  </p>
</body>
</html>
"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        import asyncio
        await asyncio.to_thread(_send_smtp, host, port, user, password, to_addr, msg)
        print(f"[notifier] Email sent to {to_addr}")
        return True
    except Exception as e:
        print(f"[notifier] Email failed: {e}")
        return False


def _send_smtp(host, port, user, password, to_addr, msg):
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, to_addr, msg.as_string())


async def notify_webhook(url: str, subject: str, html_url: str, summary: str) -> bool:
    """Send notification to a generic webhook (Slack, Discord, IFTTT, etc.)."""
    if not url:
        return False

    payload = {
        "text": f"*{subject}*\n{summary}\n{html_url}",
        "subject": subject,
        "url": html_url,
        "summary": summary,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        print(f"[notifier] Webhook sent to {url[:40]}...")
        return True
    except Exception as e:
        print(f"[notifier] Webhook failed: {e}")
        return False


def generate_ios_shortcut_url(html_url: str, title: str) -> str:
    """
    Generate a URL scheme to create an iOS Reminder via Shortcuts.
    Users can import the companion Shortcut that accepts these parameters.
    """
    import urllib.parse
    params = urllib.parse.urlencode({
        "title": f"[AI Diagram] {title}",
        "url": html_url,
    })
    return f"shortcuts://run-shortcut?name=AddDiagramReminder&input={params}"


def generate_apple_reminder_url(title: str, html_url: str) -> str:
    """Generate x-apple-reminderkit URL (works on iOS/macOS)."""
    import urllib.parse
    body = urllib.parse.quote(f"View diagram: {html_url}")
    title_enc = urllib.parse.quote(f"[AI Diagram] {title}")
    return f"x-apple-reminderkit://REMCDReminder/{title_enc}?body={body}"


async def notify_all(subject: str, html_url: str, summary: str) -> dict:
    """Run all configured notification channels."""
    results = {}

    # Email
    results["email"] = await notify_email(subject, html_url, summary)

    # Webhook
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        results["webhook"] = await notify_webhook(webhook_url, subject, html_url, summary)

    # iOS URL schemes (printed for user to open)
    shortcut_url = generate_ios_shortcut_url(html_url, subject)
    reminder_url = generate_apple_reminder_url(subject, html_url)
    results["ios_shortcut_url"] = shortcut_url
    results["ios_reminder_url"] = reminder_url

    print(f"\n[iOS Shortcut URL] {shortcut_url}")
    print(f"[iOS Reminder URL] {reminder_url}")

    return results
