# Login Troubleshooting Guide

## Common Login Issues and Solutions

This guide covers the most frequent login problems reported by users and step-by-step solutions for each.

---

## Issue 1: "Invalid Username or Password" Error

**Symptoms:** Error message appears after entering credentials.

**Step-by-Step Resolution:**

1. **Verify your email address** — Ensure you are using the email address registered with your account (check for typos, extra spaces).
2. **Check Caps Lock** — Passwords are case-sensitive. Ensure Caps Lock is off.
3. **Use Password Reset** — If unsure of your password, click "Forgot Password" on the login page and follow the reset instructions.
4. **Clear browser cache** — Cached credentials can interfere:
   - Chrome: `Ctrl+Shift+Delete` → Clear cookies and cached images
   - Firefox: `Ctrl+Shift+Delete` → Clear Cache
5. **Try a different browser** — Sometimes browser extensions block authentication cookies.
6. **Disable VPN** — VPNs can occasionally conflict with authentication servers.

---

## Issue 2: Login Page Not Loading / Stuck on Loading Screen

**Symptoms:** Browser spins indefinitely or shows a blank white page.

**Resolution:**

1. Check the service status page at `status.example.com` for ongoing incidents.
2. Clear all cookies for `example.com`:
   - Chrome: `Settings → Privacy → Cookies → See all site data → example.com → Remove`
3. Disable browser extensions one by one (especially ad blockers and privacy tools).
4. Try an Incognito/Private browsing window.
5. If on a corporate network, contact your IT team — firewall rules may block authentication endpoints.

---

## Issue 3: Two-Factor Authentication (2FA) Problems

**Symptoms:** 2FA code is rejected or not received.

**Time-Based OTP (Authenticator App) Issues:**
1. Ensure your device clock is synchronized:
   - Android: `Settings → General Management → Date and Time → Automatic`
   - iPhone: `Settings → General → Date & Time → Set Automatically`
2. Time drift of more than 30 seconds will cause TOTP codes to fail.
3. Re-sync the authenticator app by removing and re-adding the account (requires backup codes).

**SMS 2FA Issues:**
1. Confirm your phone number is correct in `Settings → Security → Phone Number`.
2. Check if you have signal — SMS may take 2–3 minutes during peak times.
3. Request a new code only after waiting 60 seconds (to avoid rate limiting).
4. If in a region with poor SMS delivery, switch to an authenticator app.

**Backup Codes:**
If you have lost access to your 2FA device, use one of the 10 backup codes provided during 2FA setup. Each backup code can only be used once. Find them in your original 2FA setup email.

---

## Issue 4: Account Locked After Failed Attempts

**Symptoms:** Message says "Your account has been temporarily locked."

**Resolution:**
1. Wait 15 minutes — accounts auto-unlock after 15 minutes of inactivity following a lockout.
2. For immediate unlock, use the "Unlock My Account" link sent to your registered email after lock.
3. For permanent locks or security-related locks, contact support — see `account_lock_policy.txt` for details.

---

## Issue 5: SSO / Single Sign-On Login Failures

**Symptoms:** Redirected back to login page after SSO, or error "SAML assertion failed."

**Resolution for Administrators:**
1. Verify the SAML metadata is up to date in `Settings → Organization → SSO Configuration`.
2. Confirm the ACS (Assertion Consumer Service) URL matches: `https://app.example.com/auth/saml/callback`
3. Ensure the identity provider's signing certificate has not expired.
4. Check attribute mapping: the `email` attribute must be mapped to the user's email.

**Resolution for End Users:**
1. Contact your IT administrator — SSO issues are typically server-side.
2. As a temporary workaround, ask your admin to issue a local password for your account.

---

## Issue 6: Session Expires Too Quickly

**Symptoms:** Logged out automatically after a few minutes.

**Resolution:**
1. Check your session timeout setting: `Settings → Security → Session Timeout`.
2. Default timeout is 8 hours for standard accounts, 30 minutes for high-security accounts.
3. Staying on an active page and interacting every 5 minutes keeps the session alive.
4. Admins can adjust organization-wide session timeout in `Admin Panel → Security Policy`.

---

## Browser Compatibility

Supported browsers and minimum versions:

| Browser | Minimum Version |
|---------|----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |
| Opera | 76+ |

Internet Explorer is not supported.

---

## Still Can't Login?

If none of the above steps resolve your issue:
1. Collect the following information: browser version, operating system, error message text, screenshot if possible
2. Contact support at support@example.com
3. Include your account email and the time the issue occurred
