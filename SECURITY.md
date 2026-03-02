# 🔐 SECURITY.md – athomic

This document outlines the security practices adopted in the `athomic` project, as well as guidance for reporting vulnerabilities or unsafe behaviors.

---

## ✅ Security Principles

- **Secure by default**: the project prioritizes secure defaults across all modules.
- **Protected secrets**: secrets must never be included in code or logs.
- **Least privilege**: access and permissions are granted in a restricted and auditable manner.
- **Auditability and traceability**: logs and commits should allow tracking of decisions and actions.

---

## 🧩 Best Practices for Contributors

- Never include keys, tokens, passwords, or sensitive data in the repository.
- Use environment variables or secure secrets management mechanisms.
- Protect endpoints with authentication and access control.
- Rigorously validate user inputs.
- Use up-to-date and trusted libraries.
- Monitor dependencies using tools like `pip-audit` or `safety`.

---

## 🤖 Automated Agents

- Agents should operate with minimal permission profiles.
- Agent commits must be traceable and not include sensitive data.
- Execution logs should be masked and auditable.
- It is recommended to run agents in isolated (sandboxed) environments.

---

## 📣 Vulnerability Reporting

If you discover a vulnerability or unsafe behavior in the project, please:

1. Do not immediately open a public issue.
2. Send an email to the security team: `security@test-nala.ai` (example)
3. Provide as many details as possible for safe and responsible investigation.

---

## 🛡️ Monitoring and Remediation

The project team is committed to:

- Analyzing vulnerabilities with top priority.
- Providing timely fixes.
- Publishing changelogs with relevant security information.

---

The security of our users and the integrity of the code are a priority. We appreciate your collaboration in keeping the project safe, resilient, and trustworthy.