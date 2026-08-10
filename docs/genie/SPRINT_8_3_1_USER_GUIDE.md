# Sprint 8.3.1: Authentication Lifecycle
## User Guide

**Version**: 1.0.0  
**Audience**: End Users  
**Last Updated**: 2026-05-21

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Your Sessions](#managing-your-sessions)
3. [Account Security](#account-security)
4. [Password Management](#password-management)
5. [Trusted Devices](#trusted-devices)
6. [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)
7. [Account Lifecycle](#account-lifecycle)
8. [Privacy & Data Export](#privacy--data-export)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### What's New in Sprint 8.3.1

We've enhanced EAIMOS with powerful new security and account management features:

* **Session Management** - View and control all your active sessions
* **Trusted Devices** - Mark devices you use regularly for faster login
* **MFA Recovery Codes** - Backup codes for when you can't access your authenticator
* **Account Lifecycle** - Self-service account deactivation and deletion
* **Comprehensive Audit Logs** - Track all security events on your account
* **Enhanced Privacy** - Export all your data with one click (GDPR compliant)

---

## Managing Your Sessions

### What Are Sessions?

A session represents an active login on a device or browser. Each time you log in, a new session is created.

### Viewing Your Active Sessions

1. Click your **profile icon** in the top right
2. Select **Security Settings**
3. Navigate to the **Sessions** tab

You'll see:
* Device type and name
* Browser information
* IP address and location
* Last activity time
* Current session indicator

### Revoking a Session

**When to revoke:**
* You logged in from a public computer and forgot to log out
* You see an unfamiliar session
* You lost or sold a device

**How to revoke:**

1. Go to **Security Settings > Sessions**
2. Find the session you want to end
3. Click **Revoke** next to that session
4. Confirm the action

✅ The session is immediately terminated, and that device must log in again.

### Revoking All Sessions

**Use this when:**
* You suspect unauthorized access
* You want to force re-authentication everywhere
* You're changing your password

**How to revoke all:**

1. Go to **Security Settings > Sessions**
2. Click **Revoke All Sessions**
3. Check **Keep my current session** if you want to stay logged in
4. Confirm the action

⚠️ **Note**: All other devices will be immediately logged out.

---

## Account Security

### Account Lockout Protection

Your account is automatically protected against brute-force attacks:

* After **5 failed login attempts**, your account is locked for **15 minutes**
* You'll receive an email notification
* Admin users can unlock your account immediately if needed

**If you're locked out:**
1. Wait 15 minutes, or
2. Contact your administrator, or
3. Use the **"Account Locked?"** link on the login page

### Email Verification

**Why verify your email?**
* Required for password resets
* Enables important security notifications
* Full access to all features

**How to verify:**

1. Check your email inbox for the verification message
2. Click the **Verify Email** button
3. You'll be redirected back to EAIMOS

**Didn't receive the email?**

1. Go to **Settings > Account**
2. Click **Resend Verification Email**
3. Check your spam/junk folder

---

## Password Management

### Password Requirements

Passwords must:
* Be at least **12 characters** long
* Include at least one **uppercase letter**
* Include at least one **lowercase letter**
* Include at least one **number**
* Include at least one **special character** (!@#$%^&*)

### Changing Your Password

**While logged in:**

1. Go to **Settings > Security**
2. Click **Change Password**
3. Enter your **current password**
4. Enter your **new password** (twice)
5. Click **Update Password**

✅ All other sessions will be logged out for security.

### Forgot Your Password?

1. On the login page, click **Forgot Password?**
2. Enter your **email address**
3. Click **Send Reset Link**
4. Check your email (within 5 minutes)
5. Click the **Reset Password** link
6. Enter your **new password** (twice)
7. Click **Reset Password**

**Reset link expires in:** 1 hour

⚠️ **Security Tip**: Never share password reset links. They're single-use and expire quickly.

---

## Trusted Devices

### What Are Trusted Devices?

Trusted devices are computers, phones, or tablets you use regularly. Marking a device as trusted:

* Speeds up login (no MFA on trusted devices)
* Remembers your preferences
* Reduces security friction

### Marking a Device as Trusted

**During login:**

1. Log in with your email and password
2. Complete MFA verification
3. Check the box **"Trust this device for 30 days"**
4. Click **Continue**

**From settings:**

1. Go to **Security Settings > Trusted Devices**
2. Click **Trust This Device**
3. Give it a name (e.g., "My Work Laptop")
4. Choose trust duration (7, 30, or 90 days)
5. Click **Save**

### Managing Trusted Devices

**View all trusted devices:**

1. Go to **Security Settings > Trusted Devices**
2. See all devices with:
   * Device name
   * Device type
   * Last used date
   * Trust expiration date

**Revoke trust for a device:**

1. Find the device in the list
2. Click **Revoke Trust**
3. Confirm the action

**Revoke all trusted devices:**

1. Click **Revoke All Trusted Devices**
2. Confirm the action

⚠️ **Best practice**: Revoke trust for:
* Lost or stolen devices
* Devices you no longer use
* Shared or public computers
* Before traveling

---

## Multi-Factor Authentication (MFA)

### Setting Up MFA

1. Go to **Security Settings > MFA**
2. Click **Enable MFA**
3. Choose your method:
   * **Authenticator App** (recommended)
   * **SMS** (backup)
4. Follow the setup wizard
5. **Save your recovery codes** (see below)

### MFA Recovery Codes

**What are recovery codes?**

Backup codes you can use if you:
* Lose your phone
* Can't access your authenticator app
* Don't receive SMS codes

**Generating recovery codes:**

1. Go to **Security Settings > MFA > Recovery Codes**
2. Click **Generate Recovery Codes**
3. **Save these codes** securely:
   * Print them
   * Store in a password manager
   * Keep in a safe place
4. Click **I've Saved These Codes**

**Using a recovery code:**

1. On the MFA verification screen, click **Use Recovery Code**
2. Enter one of your codes
3. Click **Verify**

⚠️ **Important**: 
* Each code can only be used **once**
* You have **10 codes** by default
* Generate new codes when you're down to 2-3 remaining

**Regenerating codes:**

If you lose your codes:

1. Go to **Security Settings > MFA > Recovery Codes**
2. Click **Regenerate Codes**
3. ⚠️ **Warning**: This invalidates all old codes
4. Save the new codes securely

---

## Account Lifecycle

### Deactivating Your Account

**What happens when you deactivate:**
* You're immediately logged out
* You cannot log in
* Your data is preserved
* You can reactivate anytime

**How to deactivate:**

1. Go to **Settings > Account > Lifecycle**
2. Click **Deactivate Account**
3. Enter a reason (optional)
4. Click **Confirm Deactivation**

**Reactivating:**

1. Go to the login page
2. Enter your email and password
3. Click **Reactivate My Account**
4. Your account is restored immediately

---

### Deleting Your Account

**What happens when you delete:**
* **7-day grace period** before permanent deletion
* All your data will be permanently removed
* This action is **irreversible** after the grace period
* You'll receive a confirmation email

**How to request deletion:**

1. Go to **Settings > Account > Lifecycle**
2. Click **Delete Account**
3. Read the warnings carefully
4. Enter your password
5. Type **"DELETE MY ACCOUNT"** to confirm
6. Click **Request Deletion**

**During the grace period (7 days):**

* You can still log in
* A banner shows days remaining
* You can **Cancel Deletion** anytime

**Canceling deletion:**

1. Log in to your account
2. Click the **Cancel Deletion** button in the banner
3. Confirm cancellation
4. Your account is fully restored

**Immediate deletion (skip grace period):**

1. Follow the deletion steps above
2. Check **"Delete immediately"**
3. Your account is deleted within 24 hours

⚠️ **Final Warning**: After the grace period or immediate deletion, your data **cannot be recovered**.

---

## Privacy & Data Export

### Exporting Your Data (GDPR)

You have the right to export all your data at any time.

**What's included:**
* Profile information
* Account settings
* Session history
* Audit logs
* Activity history

**How to export:**

1. Go to **Settings > Privacy > Data Export**
2. Choose format:
   * **JSON** (machine-readable)
   * **CSV** (spreadsheet-friendly)
3. Click **Export My Data**
4. Download starts immediately

**Export frequency:**
* You can export once every **24 hours**
* Files are generated in real-time

---

### Viewing Audit Logs

**What are audit logs?**

A detailed record of all security events on your account:
* Login attempts (successful and failed)
* Password changes
* Session activity
* Settings changes
* MFA events

**How to view:**

1. Go to **Security Settings > Audit Logs**
2. See all events with:
   * Event type
   * Timestamp
   * IP address
   * Device info
   * Result (success/failure)

**Filtering logs:**

* **By date**: Select date range
* **By event type**: Choose from dropdown
* **By result**: Success or failure

**Exporting logs:**

1. Set your filters
2. Click **Export Logs**
3. Choose JSON or CSV
4. Download starts immediately

---

## Troubleshooting

### I can't log in

**Check:**
1. Is your email address correct?
2. Is Caps Lock on?
3. Are you using the correct password?
4. Is your account locked? (Wait 15 minutes or contact admin)
5. Is your account deactivated or deleted?

**Try:**
* Use **Forgot Password** to reset
* Check your email for account status notifications
* Contact your administrator

---

### I don't see a verification email

**Check:**
1. Spam/junk folder
2. Email address is correct in settings
3. Email wasn't blocked by firewall

**Try:**
* Click **Resend Verification Email**
* Add `noreply@markai.com` to your contacts
* Wait 5 minutes (emails may be delayed)

---

### I lost my MFA device

**Options:**

1. **Use a recovery code**:
   * Click **Use Recovery Code** on MFA screen
   * Enter one of your backup codes

2. **Contact your administrator**:
   * They can temporarily disable MFA
   * You'll need to set up MFA again

3. **Use SMS backup** (if configured):
   * Click **Use SMS Instead**
   * Enter the code sent to your phone

---

### My account was locked

**Why?**
* Too many failed login attempts (5 within 15 minutes)

**What to do:**
1. **Wait 15 minutes** - the lock expires automatically
2. **Contact your administrator** - they can unlock immediately
3. **Check your email** - you'll receive lockout notification

**Prevent lockouts:**
* Use **Forgot Password** after 2-3 failed attempts
* Enable **trusted devices** on your regular devices

---

### I see an unfamiliar session

**Immediate action:**

1. Go to **Security Settings > Sessions**
2. Click **Revoke** on the unfamiliar session
3. Click **Revoke All Sessions** to log out everywhere
4. **Change your password** immediately
5. Review your **audit logs** for suspicious activity
6. Contact your administrator or security team

---

### Need More Help?

* **Documentation**: [https://docs.markai.com](https://docs.markai.com)
* **Support**: support@markai.com
* **Security Issues**: security@markai.com
* **Administrator**: Contact your organization's EAIMOS admin

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-05-21  
**Feedback**: docs@markai.com
