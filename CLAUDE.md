@AGENTS.md

## Time: IST only, on this whole computer (mandatory)

The user, 2026-10-21: "dont use UTC timing anywhere on this computer ... apply 1 common rule to use IST only."

- Every time you say, write, log, store, schedule, compare or show is IST (India Standard Time, UTC+05:30, this PC's own clock). Never UTC, GMT or a "Z" time.
- A day is an IST calendar day, midnight to midnight. When a service resets at another time of day, give that time in IST ("LinkedIn's count resets at 05:30 IST"), never as "00:00 UTC".
- A time you meet in UTC (a site's reset time, a cloud tool's log, an API field) is converted to IST before you use, show or store it. A time the user quotes is IST.
- Code written or edited here uses local time (`datetime.now()`, `Get-Date`) or `ZoneInfo("Asia/Kolkata")`. No `utcnow()`, `gmtime`, `-AsUTC`, `ToUniversalTime()`, `date -u`, `TZ=UTC`, and no `Z`-suffixed timestamps in logs, files, databases, dashboards, file names, schedules or messages.
- Only a third-party protocol that forces UTC (HTTP headers, JWT or cookie expiry, a GitHub Actions cron) may touch UTC, and only at that edge: convert on the way in, never store or show it.
