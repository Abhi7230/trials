# Cybersecurity Fundamentals

## Common Vulnerabilities

### SQL Injection

SQL injection attacks insert malicious SQL code through user inputs. Attackers can read, modify, or delete database data.

Prevention methods:
- Use parameterized queries
- Validate and sanitize inputs
- Apply least privilege principle
- Use ORM frameworks

### Cross-Site Scripting (XSS)

XSS allows attackers to inject client-side scripts into web pages viewed by others. Types include stored, reflected, and DOM-based XSS.

Mitigation:
- Escape output properly
- Use Content Security Policy headers
- Validate inputs
- Use HttpOnly cookies

### Cross-Site Request Forgery (CSRF)

CSRF tricks authenticated users into performing unwanted actions. Attacks exploit trust that sites have in users' browsers.

Protection:
- CSRF tokens in forms
- SameSite cookie attribute
- Verify origin headers
- Require re-authentication for sensitive actions

## Encryption

### Symmetric Encryption

Same key encrypts and decrypts data. Fast but requires secure key distribution. Examples: AES, DES, 3DES.

### Asymmetric Encryption

Uses public-private key pairs. Public key encrypts, private key decrypts. Slower but enables secure key exchange. Examples: RSA, ECC.

### Hashing

One-way function that produces fixed-size output. Used for password storage and data integrity. Common algorithms: SHA-256, bcrypt, Argon2.

## Authentication and Authorization

### Multi-Factor Authentication

Combines multiple verification methods:
- Something you know (password)
- Something you have (token, phone)
- Something you are (biometrics)

### OAuth and JWT

OAuth 2.0 provides delegated authorization framework. JSON Web Tokens (JWT) securely transmit information between parties as JSON objects.

## Network Security

### Firewalls

Firewalls filter network traffic based on rules. Types include:
- Packet filtering firewalls
- Stateful inspection firewalls
- Application-layer firewalls
- Next-generation firewalls (NGFW)

### VPN and TLS

Virtual Private Networks encrypt connections over public networks. Transport Layer Security (TLS) secures web communications through HTTPS.

### Intrusion Detection Systems

IDS monitors network traffic for suspicious activity. Can be signature-based (known attacks) or anomaly-based (unusual patterns).

## Security Best Practices

- Keep software updated
- Use strong, unique passwords
- Enable automatic backups
- Implement logging and monitoring
- Conduct security audits
- Train users on security awareness
- Follow principle of least privilege
- Use encryption for sensitive data
