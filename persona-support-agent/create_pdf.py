"""
Generate the password_reset_guide.pdf knowledge base document.
Run this once to create the PDF in the data/ directory.
"""
from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(30, 80, 162)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "Password Reset Guide", new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} | Example Platform Support | support@example.com", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(230, 240, 255)
        self.set_text_color(20, 60, 140)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_x(self.l_margin + 5)
        self.multi_cell(0, 6, f"  -  {text}")

    def numbered_step(self, num, text):
        self.set_font("Helvetica", "B", 10)
        self.set_x(self.l_margin + 5)
        x = self.get_x()
        self.cell(8, 6, f"{num}.")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(1)


def create_pdf(output_path: str):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Subtitle
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Example Platform  |  Customer Support Knowledge Base  |  Version 2.4", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Overview
    pdf.section_title("1. Overview")
    pdf.body_text(
        "This guide walks you through every available method to reset your Example Platform password. "
        "Whether you forgot your password, suspect unauthorized access, or simply need to rotate "
        "credentials for security compliance, this document covers all scenarios step-by-step."
    )

    # Self-Service Reset
    pdf.section_title("2. Standard Self-Service Password Reset")
    pdf.body_text("This is the fastest method if you have access to your registered email address.")
    pdf.numbered_step(1, "Go to the login page: https://platform.example.com/login")
    pdf.numbered_step(2, 'Click the "Forgot Password?" link below the login form.')
    pdf.numbered_step(3, "Enter the email address associated with your account and click Submit.")
    pdf.numbered_step(4, "Check your inbox for an email with subject: \"Reset Your Example Platform Password\" (may take up to 2 minutes).")
    pdf.numbered_step(5, 'Click the "Reset Password" button inside the email. The link is valid for 30 minutes.')
    pdf.numbered_step(6, "Enter your new password. Requirements:")
    pdf.bullet("Minimum 10 characters")
    pdf.bullet("At least one uppercase letter (A-Z)")
    pdf.bullet("At least one lowercase letter (a-z)")
    pdf.bullet("At least one number (0-9)")
    pdf.bullet("At least one special character (!@#$%^&*)")
    pdf.bullet("Cannot be the same as any of your last 5 passwords")
    pdf.numbered_step(7, 'Confirm the new password and click "Set New Password".')
    pdf.numbered_step(8, "You will be redirected to the login page. Sign in with your new password.")
    pdf.ln(4)
    pdf.body_text("Note: After a successful reset, all existing sessions on other devices are automatically terminated for security.")

    pdf.add_page()

    # SSO Reset
    pdf.section_title("3. SSO (Single Sign-On) Account Password Reset")
    pdf.body_text(
        "If your organization uses SSO (Google Workspace, Microsoft Azure AD, Okta, etc.), your password "
        "is managed by your identity provider, NOT by Example Platform."
    )
    pdf.numbered_step(1, "Contact your IT administrator or help desk.")
    pdf.numbered_step(2, "Request a password reset through your organization's identity provider.")
    pdf.numbered_step(3, "Once reset at the identity provider level, return to https://platform.example.com and log in via SSO.")
    pdf.ln(2)
    pdf.body_text("Example Platform support cannot reset SSO-managed passwords. Your IT team controls those credentials.")

    # 2FA Locked Out
    pdf.section_title("4. Reset When Locked Out Due to 2FA")
    pdf.body_text("If you have lost access to your 2FA device (phone, authenticator app):")
    pdf.numbered_step(1, 'On the 2FA prompt page, click "Use a Backup Code".')
    pdf.numbered_step(2, "Enter one of the 10 backup codes you saved during initial 2FA setup.")
    pdf.numbered_step(3, "Each backup code can be used only once.")
    pdf.ln(2)
    pdf.body_text("If you do not have backup codes:")
    pdf.bullet("Email security@example.com with subject: 2FA RECOVERY REQUEST")
    pdf.bullet("Provide: account email, last 4 digits of billing card, approximate account creation date")
    pdf.bullet("Identity verification will be required")
    pdf.bullet("Processing time: 1-2 business days")

    # Admin Reset
    pdf.section_title("5. Admin-Initiated Password Reset")
    pdf.body_text("Account administrators can reset passwords for team members:")
    pdf.numbered_step(1, "Log into your admin account at https://platform.example.com")
    pdf.numbered_step(2, 'Navigate to Admin Panel > Team > Users.')
    pdf.numbered_step(3, "Find the user by name or email.")
    pdf.numbered_step(4, 'Click the user row and select "Reset Password".')
    pdf.numbered_step(5, "Choose: Send Reset Email (user receives reset link) or Set Temporary Password (admin sets a temp password).")
    pdf.numbered_step(6, "If setting a temporary password, the user will be forced to change it on next login.")

    # Troubleshooting
    pdf.section_title("6. Troubleshooting Reset Issues")
    pdf.body_text("Reset email not received:")
    pdf.bullet("Check your spam/junk folder")
    pdf.bullet("Ensure you used the exact email registered with the account")
    pdf.bullet("Wait 5 minutes before requesting another reset (to avoid spam filters)")
    pdf.bullet("Add noreply@example.com to your contacts/allowlist")
    pdf.bullet("Check with your IT team if corporate email filtering may be blocking the message")
    pdf.ln(2)
    pdf.body_text("Reset link expired:")
    pdf.bullet("Reset links are valid for 30 minutes only")
    pdf.bullet("Return to the login page and request a new reset link")
    pdf.ln(2)
    pdf.body_text('"New password not accepted" error:')
    pdf.bullet("Ensure all password requirements are met (see Section 2, Step 6)")
    pdf.bullet("Clear your browser cache and try again in a private/incognito window")
    pdf.bullet("Try a different browser")

    pdf.add_page()

    # Security Best Practices
    pdf.section_title("7. Password Security Best Practices")
    pdf.body_text("After resetting your password, follow these best practices to keep your account secure:")
    pdf.bullet("Use a password manager (1Password, Bitwarden, LastPass) to generate and store strong unique passwords")
    pdf.bullet("Never reuse passwords across multiple services")
    pdf.bullet("Enable Two-Factor Authentication (2FA) at Settings > Security > Two-Factor Authentication")
    pdf.bullet("Rotate your password every 90 days if handling sensitive data")
    pdf.bullet("Never share your password with support agents (we will never ask for it)")
    pdf.bullet("Sign out of shared or public computers after each session")
    pdf.ln(4)
    pdf.body_text("If you suspect your account has been compromised, reset your password immediately and contact security@example.com.")

    # Contact
    pdf.section_title("8. Contact Support")
    pdf.body_text(
        "If you are unable to reset your password using the methods above, contact our support team:"
    )
    pdf.bullet("Email: support@example.com")
    pdf.bullet("Chat: Available in the platform dashboard (Professional/Enterprise plans)")
    pdf.bullet("Phone: 1-800-EXAMPLE (Enterprise only, Mon-Fri 9AM-6PM EST)")
    pdf.ln(2)
    pdf.body_text("When contacting support, have ready: your account email, approximate date of last successful login, and any error messages received.")

    pdf.output(output_path)
    print(f"PDF created successfully: {output_path}")


if __name__ == "__main__":
    create_pdf("data/password_reset_guide.pdf")
