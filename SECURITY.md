# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Agent Skills Marketplace seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **security@coreline.ai**

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Varies based on complexity

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report.
2. **Investigation**: Our security team will investigate the issue.
3. **Updates**: We will keep you informed of the progress.
4. **Resolution**: Once resolved, we will notify you and discuss disclosure.

## Security Best Practices

### For Users

- Never commit `.env` files or secrets to version control
- Rotate API keys and tokens regularly
- Use strong, unique passwords for admin accounts
- Keep all dependencies up to date

### For Contributors

- Follow secure coding practices
- Never log sensitive information
- Validate all user inputs
- Use parameterized queries for database operations
- Review dependencies for known vulnerabilities

## Security Features

This project implements the following security measures:

- **Authentication**: JWT-based authentication with bcrypt password hashing
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Pydantic models for request validation
- **CORS**: Configurable Cross-Origin Resource Sharing
- **Rate Limiting**: API rate limiting (configurable)
- **Content Security**: Automated security scanning for skill content (`app/quality/security_scan.py`)

## Known Security Considerations

- GitHub tokens should be kept secure and have minimal required permissions
- Admin credentials should be changed from defaults before production deployment
- Database connections should use SSL in production environments

---

Thank you for helping keep Agent Skills Marketplace and our users safe!
