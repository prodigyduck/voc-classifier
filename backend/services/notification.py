import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import yaml
from pathlib import Path
from typing import Optional, List
from datetime import datetime


def load_config():
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
notification_config = config.get("notification", {})


class NotificationService:
    def __init__(self):
        self.enabled = notification_config.get("enabled", False)
        self.email_config = notification_config.get("email", {})
        self.slack_config = notification_config.get("slack", {})
        self.notify_on = notification_config.get("notify_on", [])

    def is_enabled_for_event(self, event: str) -> bool:
        return self.enabled and event in self.notify_on

    def send_notification(self, event: str, title: str, message: str, data: dict = None):
        if not self.is_enabled_for_event(event):
            return

        if self.email_config.get("enabled", False):
            self._send_email(title, message, data)

        if self.slack_config.get("enabled", False):
            self._send_slack(title, message, data)

    def _send_email(self, subject: str, message: str, data: dict = None):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])
            msg["Subject"] = f"[VOC Classifier] {subject}"

            body = message
            if data:
                body += "\n\nDetails:\n"
                for key, value in data.items():
                    body += f"- {key}: {value}\n"

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(
                self.email_config["smtp_host"],
                self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["smtp_username"],
                    self.email_config["smtp_password"]
                )
                server.send_message(msg)
        except Exception as e:
            print(f"Email send failed: {str(e)}")

    def _send_slack(self, title: str, message: str, data: dict = None):
        try:
            webhook_url = self.slack_config.get("webhook_url")
            if not webhook_url:
                return

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 VOC Classifier: {title}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]

            if data:
                fields = []
                for key, value in data.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                blocks.append({
                    "type": "section",
                    "fields": fields
                })

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            })

            payload = {
                "channel": self.slack_config.get("channel", "#voc-alerts"),
                "blocks": blocks
            }

            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Slack send failed: {str(e)}")

    def notify_new_voc(self, voc_id: int, title: str, priority: str):
        if not self.is_enabled_for_event("new_voc"):
            return

        notification_title = f"새 VOC 등록됨 (ID: {voc_id})"
        notification_message = f"*제목:* {title}\n*우선순위:* {priority}"

        self.send_notification(
            "new_voc",
            notification_title,
            notification_message,
            {"VOC ID": voc_id, "Title": title, "Priority": priority}
        )

    def notify_voc_resolved(self, voc_id: int, title: str):
        if not self.is_enabled_for_event("voc_resolved"):
            return

        notification_title = f"VOC 해결됨 (ID: {voc_id})"
        notification_message = f"*제목:* {title}"

        self.send_notification(
            "voc_resolved",
            notification_title,
            notification_message,
            {"VOC ID": voc_id, "Title": title}
        )

    def notify_ui_improvement_completed(self, improvement_id: int, name: str, reduction_rate: float):
        if not self.is_enabled_for_event("ui_improvement_completed"):
            return

        notification_title = f"UI 개선 활동 완료 (ID: {improvement_id})"
        notification_message = f"*개선 활동:* {name}\n*감소율:* {reduction_rate * 100:.1f}%"

        self.send_notification(
            "ui_improvement_completed",
            notification_title,
            notification_message,
            {"Improvement ID": improvement_id, "Name": name, "Reduction Rate": f"{reduction_rate * 100:.1f}%"}
        )

    def notify_high_priority_voc(self, voc_id: int, title: str, priority: str):
        if not self.is_enabled_for_event("high_priority_voc"):
            return

        if priority not in ["HIGH", "CRITICAL"]:
            return

        notification_title = f"⚠️ 높은 우선순위 VOC 등록됨 (ID: {voc_id})"
        notification_message = f"*제목:* {title}\n*우선순위:* {priority}"

        self.send_notification(
            "high_priority_voc",
            notification_title,
            notification_message,
            {"VOC ID": voc_id, "Title": title, "Priority": priority}
        )
