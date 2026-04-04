Check the health of all Docker Compose stacks, NAS mounts, and surface any problems.

## Step 1: Container status overview

Run these commands:
1. `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"` — all running containers
2. `docker ps -a --filter status=exited --format "table {{.Names}}\t{{.Status}}"` — stopped containers
3. `docker ps -a --filter status=restarting --format "table {{.Names}}\t{{.Status}}"` — restart loops
4. `docker ps --filter health=unhealthy --format "table {{.Names}}\t{{.Status}}"` — unhealthy containers

## Step 2: Diagnose stopped/restarting containers

For each stopped or restarting container:
1. Get exit code and error: `docker inspect --format='ExitCode={{.State.ExitCode}} Error={{.State.Error}}' <name>`
2. Get restart count: `docker inspect --format='RestartCount={{.RestartCount}}' <name>`
3. Get last 10 log lines: `docker logs <name> --tail 10`
4. Check if it has NAS bind mounts: `docker inspect --format='{{range .Mounts}}{{if contains .Source "Personal-Drive"}}NAS: {{.Source}} -> {{.Destination}}{{end}}{{end}}' <name>`

## Step 3: NAS mount check

1. Check if NAS is mounted: `mount | grep Personal-Drive`
2. If not mounted, warn: "NAS not mounted at /Volumes/Personal-Drive — containers with NAS bind mounts will not have NAS data. Run: ./internal/scripts/mount-unas.sh"
3. List stack files with NAS mount dependencies: `grep -rn "Personal-Drive" stacks/*.yml`

## Step 4: Prometheus alerts check

Run: `curl -s http://localhost:9090/api/v1/alerts | python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'  FIRING: {a[\"labels\"][\"alertname\"]} — {a[\"annotations\"].get(\"summary\",\"\")}') for a in data['data']['alerts'] if a['state']=='firing']"`

## Present results

- Summary line: "X running, Y stopped, Z unhealthy, W restarting"
- NAS mount status (mounted/unmounted + affected containers)
- Firing Prometheus alerts
- For each problem container: name, exit code, error message, NAS mount dependency, last log lines
- Containers in restart loops with restart counts

Report only — do not restart anything without being asked.
