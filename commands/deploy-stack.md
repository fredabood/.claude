Guided deployment workflow for an existing Docker Compose stack.

Ask: "Which stack do you want to deploy?" if not already specified.

Steps:
1. Pull latest images: docker compose -f stacks/<stack>.yml --env-file .env pull
2. Start: docker compose -f stacks/<stack>.yml --env-file .env up -d
3. After 10 seconds, check health: docker compose -f stacks/<stack>.yml --env-file .env ps
4. For each service in the stack with a Caddyfile entry, verify the external URL responds (non-5xx)
5. Surface any containers that failed to start or are unhealthy

If there is an active Jira ticket, offer to post a milestone comment with deployment results.
