#!/usr/bin/env bash
# Adapt Compose builds to the cloud proxy without storing credentials in files.
set -euo pipefail
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cloud_dir=${HYP_CLOUD_DIR:-/workspace/hyp-docker-cloud}
export DOCKER_CONFIG=${DOCKER_CONFIG:-/workspace/.cache/docker}
mkdir -p "$cloud_dir/trust" "$DOCKER_CONFIG"
python - "$repo_dir" "$cloud_dir" <<'PY'
from pathlib import Path
import json
import os
import secrets
import shutil
import socket
import sys
from urllib.parse import urlsplit

repo, cloud = map(Path, sys.argv[1:])
shutil.copyfile('/etc/ssl/certs/ca-certificates.crt', cloud / 'trust/ca.crt')
services = {}
for service in ('backend', 'frontend'):
    dockerfile = (repo / service / 'Dockerfile').read_text()
    trust = 'COPY --from=cloudtrust ca.crt /usr/local/share/ca-certificates/cloud.crt\n'
    if service == 'backend':
        trust += 'RUN update-ca-certificates\n'
    else:
        trust += 'ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/cloud.crt\n'
    (cloud / f'{service}.Dockerfile').write_text(
        dockerfile.replace('WORKDIR /app', trust + 'WORKDIR /app', 1)
    )
    build = {
        'dockerfile': str(cloud / f'{service}.Dockerfile'),
        'network': 'host',
        'additional_contexts': {'cloudtrust': str(cloud / 'trust')},
        'args': {'HTTP_PROXY': '${HTTP_PROXY:-}', 'HTTPS_PROXY': '${HTTPS_PROXY:-}', 'NO_PROXY': ''},
    }
    hosts = {}
    for key in ('HTTP_PROXY', 'HTTPS_PROXY'):
        hostname = urlsplit(os.environ.get(key, '')).hostname
        if hostname:
            hosts[hostname] = socket.gethostbyname(hostname)
    if hosts:
        build['extra_hosts'] = hosts
    services[service] = {'build': build}
# JSON is a YAML subset. Only variable references, never proxy values, are saved.
(cloud / 'compose.cloud.json').write_text(json.dumps({'services': services}, indent=2))
env_file = repo / '.env'
if not env_file.exists():
    text = (repo / '.env.example').read_text().replace(
        'change-me-in-production', secrets.token_urlsafe(48)
    )
    with env_file.open('x', opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
        stream.write(text)
PY
docker compose -f "$repo_dir/docker-compose.yml" -f "$cloud_dir/compose.cloud.json" up -d --build
