# Coraza local learning lab

Build a working example of a reverse proxy inspecting requests before forwarding them to an API. Docker runs two services: Caddy with the Coraza plugin and embedded OWASP CRS, plus a small Python API. You do not need to install Go or Caddy locally.

The API echoes parameters as JSON. It has no database and does not execute the supplied attack patterns. This exercise demonstrates WAF detection, not successful exploitation of an application.

## Requirements

- Docker Desktop running with Linux containers (on Windows, use its WSL 2 backend).
- Internet access for the initial image/module downloads.
- Optional: local Python 3 to run the automated checks.

## Start

Extract the ZIP. Open a terminal inside the `coraza-lab` directory, where `compose.yaml` lives:

```sh
docker compose up --build -d
docker compose logs -f waf
```

The first build downloads Go modules and compiles the plugin; it can take several minutes. When ready, open http://localhost:8080/health. Expect `{"status": "ok"}`. Press Ctrl+C to leave the log viewer; the services keep running.

## Experiment 1: allowed request

Open http://localhost:8082/api/search?q=laptop

Expect HTTP 200 and JSON saying the request reached the API. The proxy received your request, Coraza inspected it, and Caddy forwarded it to `api:8000` on Docker's internal network.

## Experiment 2: custom rule

Open http://localhost:8082/api/search?message=waf-test

Expect HTTP 403. Read the custom `SecRule` at the end of the directives in `Caddyfile`: it inspects `ARGS:message`, matches the text `waf-test`, and denies the request in phase 2. Search WAF logs for rule ID `10001` or `Learning rule matched`:

```sh
docker compose logs waf
docker compose logs api
```

A request blocked during the request phases should not appear in the API's request log. A WAF access log records status and path; an audit log provides security event details such as matched rules. The demo intentionally logs request information, so use synthetic data.

## Experiment 3: OWASP CRS

Run the included checks using local Python:

```sh
python check.py
```

On systems where Python is named `python3`, use that instead. To test manually, use these URLs in a browser:

- Normal: http://localhost:8080/api/search?q=laptop
- SQL injection pattern: http://localhost:8080/api/search?q=1%27%20OR%20%271%27%3D%271%27%20--%20
- XSS pattern: http://localhost:8080/api/search?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E

The checks expect 200 for normal traffic and 403 for the three matching requests. CRS rules usually contribute to an anomaly score; the blocking evaluation compares that score against its threshold. If a CRS example returns 200, inspect the audit log and matched scores instead of assuming every suspicious string must always be blocked.

## Experiment 4: detection-only mode

Change `SecRuleEngine On` in `Caddyfile` to `SecRuleEngine DetectionOnly`, save, and restart the proxy:

```sh
docker compose restart waf
python check.py detection
```

All four requests should now reach the API with HTTP 200, while matching rules still produce security logs. Restore `On` and restart again to enable blocking.

## Experiment 5: write your own rule

Add the following inside the directives block and restart the proxy:

```apache
SecRule REQUEST_URI "@beginsWith /private" "id:10002,phase:1,t:none,deny,status:403,log,msg:'Private path blocked in lab'"
```

Request http://localhost:8080/private. With blocking enabled, expect 403. Without that rule, the API would return 404 because it has no such route. Compare the status and logs to understand which component handled the request.

## Files and roles

| File | Role |
|---|---|
| compose.yaml | Starts the proxy and API; publishes only the proxy on local port 8080 |
| Dockerfile | Builds Caddy with Coraza; the plugin includes CRS |
| Caddyfile | Configures the WAF, rules, logs, and backend destination |
| app/server.py | Demo backend listening internally on port 8000 |
| check.py | Checks allowed traffic, custom blocking, CRS, and detection-only behavior |

The API has no published host port. Caddy can reach it through the Compose service name `api`. The published proxy port is bound to 127.0.0.1 for local experiments.

## Troubleshooting and cleanup

- Connection refused: confirm `docker compose ps` and inspect `docker compose logs waf` for startup errors.
- Port 8080 busy: change the host mapping to `127.0.0.1:8082:8080`, then use port 8082 in URLs and check.py.
- Module/image downloads fail: check Docker's internet access and retry the build.
- Unknown `coraza_waf` directive: check that the custom Dockerfile built successfully; the ordinary Caddy image alone does not include Coraza.
- Configuration changes take effect after `docker compose restart waf`.

Stop and remove the lab containers/network:

```sh
docker compose down
```

## Validation and scope

The Python code and demo API were checked when this package was created. Docker was unavailable in the authoring environment, so the complete Caddy/Coraza build and request checks have not been run there. Run `python check.py` locally to verify the full setup.

This is a learning setup. The Dockerfile intentionally resolves current Caddy and plugin versions at build time; future builds may differ. For a maintained deployment, pin tested versions/digests, test normal application traffic, tune false positives, and retain application security controls.

Official references:
- https://github.com/corazawaf/coraza-caddy (plugin build, ordering, embedded CRS includes)
- https://coreruleset.org/docs/ (scoring and tuning)
- https://coraza.io/docs/ (engine and SecLang)
