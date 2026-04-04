Run the comprehensive homelab health check script and interpret the results.

1. Run: `./internal/scripts/health-check.sh production`
2. If there are failures, analyze each one:
   - Container not running: check exit code, error message, NAS mount dependency
   - Unhealthy container: check health check logs with `docker inspect --format='{{json .State.Health}}' <name>`
   - HTTP endpoint failed: check if container is running first, then Caddy connectivity
3. For each failure, suggest the specific fix (restart, recreate, mount NAS, check logs)
4. Summarize: total checks, pass rate, and actionable next steps
