"""BotEmail tool — gives agents free, disposable email inboxes via botemail.ai."""

from __future__ import annotations

from typing import Literal, Optional, Union

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field


class BotEmailCreateInbox(BaseTool):
    """Tool that creates a new disposable email inbox via botemail.ai.

    botemail.ai provides free, temporary email inboxes for AI agents with no
    sign-up required. This tool creates a new inbox and returns the email
    address and API key needed to read messages.

    Example:
        .. code-block:: python

            from langchain_community.tools.botemail import BotEmailCreateInbox

            tool = BotEmailCreateInbox()
            result = tool.invoke("")
            # Returns: "Email: abc@botemail.ai | API Key: xxxx-xxxx"
    """

    name: str = "botemail_create_inbox"
    description: str = (
        "Creates a free, disposable email inbox for an AI agent via botemail.ai. "
        "No input needed. Returns the email address and API key to use with "
        "botemail_get_emails and botemail_delete_email tools."
    )
    base_url: str = Field(default="https://api.botemail.ai")

    def _run(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Create a new email inbox."""
        try:
            response = requests.post(f"{self.base_url}/api/create-account", timeout=15)
            response.raise_for_status()
            data = response.json()
            email = data.get("email", "")
            api_key = data.get("apiKey", "")
            return (
                f"Inbox created successfully.\n"
                f"Email: {email}\n"
                f"API Key: {api_key}\n"
                f"Use these with botemail_get_emails to check for incoming messages."
            )
        except requests.RequestException as e:
            return f"Error creating inbox: {str(e)}"


class BotEmailGetEmails(BaseTool):
    """Tool that reads emails from a botemail.ai inbox.

    Example:
        .. code-block:: python

            from langchain_community.tools.botemail import BotEmailGetEmails

            tool = BotEmailGetEmails(
                email="abc@botemail.ai",
                api_key="your-api-key",
            )
            result = tool.invoke("")
            # Returns a list of emails in the inbox
    """

    name: str = "botemail_get_emails"
    description: str = (
        "Retrieves emails from a botemail.ai inbox. "
        "The inbox email address and API key must be configured on the tool instance. "
        "Returns a formatted list of emails with sender, subject, date, and body preview."
    )
    email: str = Field(..., description="The email address of the inbox.")
    api_key: str = Field(..., description="The API key for the inbox.")
    base_url: str = Field(default="https://api.botemail.ai")

    def _run(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Retrieve emails from the inbox."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/api/emails/{self.email}",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            emails = response.json()

            if not emails:
                return f"No emails found in inbox: {self.email}"

            result_lines = [f"Found {len(emails)} email(s) in {self.email}:\n"]
            for i, msg in enumerate(emails, 1):
                result_lines.append(f"--- Email {i} ---")
                result_lines.append(f"ID:      {msg.get('id', 'N/A')}")
                result_lines.append(f"From:    {msg.get('from', 'N/A')}")
                result_lines.append(f"Subject: {msg.get('subject', '(no subject)')}")
                result_lines.append(f"Date:    {msg.get('date', 'N/A')}")
                body = msg.get("body") or msg.get("text") or msg.get("html") or ""
                if body:
                    preview = body[:500] + ("..." if len(body) > 500 else "")
                    result_lines.append(f"Body:\n{preview}")
                result_lines.append("")
            return "\n".join(result_lines)
        except requests.RequestException as e:
            return f"Error retrieving emails: {str(e)}"


class BotEmailDeleteEmail(BaseTool):
    """Tool that deletes a specific email from a botemail.ai inbox.

    Example:
        .. code-block:: python

            from langchain_community.tools.botemail import BotEmailDeleteEmail

            tool = BotEmailDeleteEmail(
                email="abc@botemail.ai",
                api_key="your-api-key",
            )
            result = tool.invoke("email-id-to-delete")
    """

    name: str = "botemail_delete_email"
    description: str = (
        "Deletes a specific email from a botemail.ai inbox. "
        "Input should be the email ID to delete. "
        "The inbox email address and API key must be configured on the tool instance."
    )
    email: str = Field(..., description="The email address of the inbox.")
    api_key: str = Field(..., description="The API key for the inbox.")
    base_url: str = Field(default="https://api.botemail.ai")

    def _run(
        self,
        email_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Delete a specific email."""
        if not email_id or not email_id.strip():
            return "Error: Please provide the email ID to delete."
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.delete(
                f"{self.base_url}/api/emails/{self.email}/{email_id.strip()}",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            return f"Email '{email_id}' deleted successfully from inbox: {self.email}"
        except requests.RequestException as e:
            return f"Error deleting email: {str(e)}"
