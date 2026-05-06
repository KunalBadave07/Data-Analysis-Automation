# Phase 3: Authentication System with OTP Verification

## 1) Architecture Explanation
Phase 3 introduces a production-style authentication layer that works locally without AWS access:

- Flask-Login session management for user auth state.
- Bcrypt password hashing before persistence.
- SQLite-backed user + OTP persistence (`AUTH_DB_PATH`) to replace in-memory storage.
- OTP lifecycle with expiry, resend cooldown, and single-use validation.
- SMTP integration for OTP emails with safe local fallback (OTP printed to logs when SMTP is not configured).

Flow:
`Register -> OTP generated -> Verify OTP -> Mark verified -> Login allowed`

## 2) Folder Structure
```text
app/
  routes/
    auth.py                    # register/login/verify/resend/logout
  services/
    auth_store.py              # persistent user + OTP store (SQLite)
    otp_service.py             # OTP generation, hashing, email sending
  templates/
    auth/
      login.html
      register.html
      verify_otp.html          # new OTP screen
tests/
  test_auth_flow.py            # new auth + OTP flow tests
docs/
  PHASE_03.md
```

## 3) Code Generation
Implemented in this phase:

- New persistent auth data layer:
  - `users` table
  - `otp_codes` table
- App startup DB initialization in app factory.
- New auth endpoints:
  - `/auth/register`
  - `/auth/login`
  - `/auth/verify`
  - `/auth/resend-otp`
  - `/auth/logout`
- OTP controls:
  - six-digit code generation
  - HMAC hash-based OTP verification
  - expiry (`OTP_EXPIRY_MINUTES`)
  - resend throttle (`OTP_RESEND_COOLDOWN_SECONDS`)
- UI updates for login/register/verify screens and nav links.

## 4) Required Commands
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python run.py
```

Test command:
```powershell
python -m pytest -q
```

## 5) AWS Setup Instructions
No AWS dependency is required to run Phase 3 locally.

Optional cloud alignment for email delivery:
1. If you want real OTP emails in cloud, use AWS SES SMTP credentials.
2. Fill `.env` with `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SENDER`.
3. Without SMTP, OTP is printed in local server logs for development use.

## 6) Integration Instructions
1. Keep `auth_store.py` API stable until DynamoDB migration.
2. When AWS access arrives, migrate user/OTP persistence from SQLite to DynamoDB repository methods.
3. Keep route-level behavior unchanged during migration so frontend remains stable.
4. Preserve OTP hash/expiry semantics when moving to cloud-backed storage.

## 7) Testing Instructions
Run:
```powershell
python -m pytest -q
```

Coverage now includes:
1. Health endpoint check.
2. Public page rendering checks.
3. Protected route redirect behavior.
4. Register -> blocked login -> OTP verify happy path.
5. Invalid OTP rejection path.
