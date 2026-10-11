# Atlair Post

> Atlair Post is an open-source (AGPL-3.0) transactional email API and panel that sends through your own Amazon SES account. It runs on Postgres with an API and a worker process, and you can host it yourself. Source: https://github.com/atlair-cloud/atlair-mail

Atlair Post is made by Atlair (A-T-L-A-I-R), sometimes searched as "Atlair email". It is not Altair Engineering and has no connection to Siemens.

## What it does today

- Send API: one HTTP request per email, with idempotency keys and scheduling up to 30 days ahead.
- Sends through the organization's own Amazon SES account. AWS credentials are encrypted and never returned.
- Domains: DKIM, SPF, custom MAIL FROM and DMARC records, with verification.
- Templates: a visual editor with variables, phone preview, versions and rollback.
- Webhooks: 9 event types signed to the Standard Webhooks spec, retried 8 times over about 27 hours.
- Automatic suppression of hard bounces and complaints, with checks again right before sending.
- A panel with an overview, email logs, a playground, organizations, roles and an audit log.

## Not built yet

- Attachments, batch sending, a Node SDK, open and click tracking, contacts and broadcasts.

## Comparisons (pages on post.atlair.cloud/alternatives)

Resend, SendGrid, Mailgun, Postmark, Amazon SES, Mailchimp Transactional, Brevo, Loops, Plunk, useSend.

## Use cases (pages on post.atlair.cloud/use-cases)

Password reset emails, magic link emails, verification code emails, receipt emails, welcome emails, scheduled emails.

## Questions people ask

- Why send from my own AWS account? You pay AWS directly, and your sending reputation stays yours.
- Can I host it myself? Yes. It's AGPL-3.0. You need Postgres, the API and the worker.
- Which languages work? Anything that can make an HTTP request. A Node SDK is coming.
- Are my AWS keys safe? They're encrypted, tied to your organization, and never shown again.
- How much does it cost? Pricing isn't decided yet. Hosting it yourself is free. Ask at hello@atlair.cloud.
- Support: hello@atlair.cloud or GitHub issues at github.com/atlair-cloud/atlair-mail.
