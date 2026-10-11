# Atlair

> Atlair takes a project from "I think it's ready" to a live link you can send. Connect a GitHub repository, watch each deploy stage from clone to health check, and see which step failed and why. Atlair Cloud is in private preview.

## What Atlair does today

- Deploys from a GitHub repository and branch.
- Recognises Next.js, Nuxt, Astro, Vite and Angular, and suggests a start command and port.
- Builds Go, Python, Rust and Bun projects automatically, or from your own Dockerfile. Ruby, PHP, Java and more build too.
- Shows deploy stages as they happen: Clone, Build, Push, Deploy, Health check.
- When a deploy fails: the failed stage, a reason code (for example BUILD_FAILED), a practical next step, and the timestamped build output. It does not write AI explanations or pinpoint source lines.
- Gives each project a live HTTPS URL on atlair.app.

## Coming soon (not available yet)

- GitLab repositories: Connect projects that live on GitLab.
- Custom domains: Serve your project from a domain you own.
- Pull request previews: A live link for every pull request.
- Rollback: Return to an earlier release in one step.
- Your own cloud: Deploy the same way into infrastructure you own.

## Questions people ask

- What does Atlair cost? Pricing hasn't been decided yet. If it matters for your plans, write to hello@atlair.cloud.
- Are there limits on builds? No. There are no build limits right now.
- What do I need to start? A GitHub account and a repository. Connect GitHub, pick the repository and branch, and Atlair builds it.
- Will my project work? Atlair recognises Next.js, Nuxt, Astro, Vite, Create React App, Angular and Node.js, and suggests how to start them. Go, Python, Rust, Bun, Ruby, PHP, Java and more build straight from the repository. Anything with a Dockerfile builds from your Dockerfile.
- What happens when a build fails? See which step failed, read the build output, and get a practical next step. Once it's fixed, deploy again.
- Where does my app run? On Atlair Cloud, at its own HTTPS address on atlair.app. Deploying into infrastructure you own is coming soon.
- Can I use my own domain? Not yet. Custom domains are coming soon. Until then every project gets its own address on atlair.app.
- How are my environment variables stored? Variables you mark as secret are kept in a secret manager, and their values are never shown again. Other variables are stored as plain text in Atlair's database, so mark anything sensitive, like API keys or database URLs, as a secret.
- How long are logs kept? 30 days.
- Where can I get help? Email hello@atlair.cloud.

## Pages

- [The moment it's live.](https://atlair.cloud/): What Atlair is, what it deploys today, and what is coming soon.
- [Open Atlair](https://app.atlair.cloud): Sign in and deploy a project.

## Guides

- [Kubernetes deployment guides for small teams](https://atlair.cloud/guides)
- [A practical Kubernetes deployment checklist](https://atlair.cloud/guides/kubernetes-deployment-checklist)
- [How to deploy from GitHub Actions to Kubernetes](https://atlair.cloud/guides/github-actions-to-kubernetes)
- [How DNS and TLS fit into a Kubernetes deployment](https://atlair.cloud/guides/kubernetes-dns-tls)
- [When multi-cloud Kubernetes makes sense for a small team](https://atlair.cloud/guides/multi-cloud-kubernetes-small-teams)
