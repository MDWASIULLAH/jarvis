# Security Policy

Jarvis is designed as a high-security local-first assistant.

## Security Model

- Desktop actions require the Local Core connector.
- Hosted Vercel functions must not directly control a user's laptop.
- Email, WhatsApp, terminal commands, shutdown, file edits, deployments, and automation flows require approval in the UI.
- API keys and credentials must stay in backend/local settings only.
- `jarvis_data/settings.json` is ignored by git so local secrets are not uploaded.

## Reporting Issues

For support or security reports, contact:

```text
mdwasiullah445@gmail.com
```

Please include:

- what happened
- steps to reproduce
- expected behavior
- screenshots or logs if available

## Safe Usage

Review every approval card before continuing. Do not approve terminal, email, sharing, deployment, or system actions unless the plan and target are correct.
