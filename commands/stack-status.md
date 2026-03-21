Check the health of all Docker Compose stacks and surface any problems.

1. Run: docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
2. Run: docker ps -a --filter status=exited --format "table {{.Names}}\t{{.Status}}" to find stopped containers
3. Run: docker ps --filter health=unhealthy --format "table {{.Names}}\t{{.Status}}" to find unhealthy containers

Group results by stack using container name prefixes.

Present:
- Summary: "X running, Y stopped, Z unhealthy"
- Stopped or unhealthy containers listed with last status
- Containers in restart loops (status contains "Restarting")

Report only — do not restart anything without being asked.
