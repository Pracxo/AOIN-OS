#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
"$PYTHON_BIN" - <<'__AION204_NOGO__'
import json, os, re, subprocess
from pathlib import Path
ROOT=Path(os.environ['AION_REPO_ROOT'])
EXPECTED='105fe29348160a2218ac095cfffadcb6f234421f'
PROHIBITED_PREFIXES=('.github/workflows/','services/brain-api/src/aion_brain/','services/brain-api/pyproject.toml','packages/aion-sdk-python/src/','migrations/','services/brain-api/migrations/','infra/postgres/migrations/')
PROHIBITED_NAMES={'package.json','package-lock.json','pnpm-lock.yaml','yarn.lock','poetry.lock','uv.lock','Pipfile','Pipfile.lock'}
AION205=('services/brain-api/src/aion_brain/contracts/knowledge_research.py','services/brain-api/src/aion_brain/knowledge_intelligence/')
SOURCE_REGISTRY_SOURCE={
    'services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py',
    'services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py',
}
SECRET=re.compile(r'(?i)(sk-[a-z0-9]|ghp_[a-z0-9]|gho_[a-z0-9]|xoxb-|bearer\s+[a-z0-9])')
URL=re.compile(r'''https?://([^/\s"']+)''')
def run(args, check=True): return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)
def ref_exists(ref): return run(['git','rev-parse','--verify','--quiet',ref],False).returncode==0
def base():
    candidates=[]
    if os.environ.get('GITHUB_BASE_REF'): candidates += [f"origin/{os.environ['GITHUB_BASE_REF']}", os.environ['GITHUB_BASE_REF']]
    candidates += ['origin/main','main']
    for c in candidates:
        if ref_exists(c):
            mb=run(['git','merge-base','HEAD',c],False)
            if mb.returncode==0 and mb.stdout.strip(): return mb.stdout.strip()
    return 'HEAD~1' if ref_exists('HEAD~1') else None
b=base()
entries=[]
program_state=''
program_path=ROOT/'docs/knowledge-intelligence/program-ledger.json'
if program_path.exists():
    program_state=json.loads(program_path.read_text()).get('program_state','')
implemented_states = {
    'research_plane_implemented_disabled_pending_closeout',
    'source_provenance_registry_authorized_not_implemented',
    'source_provenance_registry_implemented_write_disabled_pending_closeout',
    'temporal_claim_evidence_graph_authorized_not_implemented',
}
if b is not None:
    entries += [line.split('\t') for line in run(['git','diff','--name-status',b,'HEAD']).stdout.splitlines() if line.strip()]
entries += [line.split('\t') for line in run(['git','diff','--name-status']).stdout.splitlines() if line.strip()]
entries += [line.split('\t') for line in run(['git','diff','--cached','--name-status']).stdout.splitlines() if line.strip()]
for line in run(['git','status','--porcelain=v1']).stdout.splitlines():
    if not line:
        continue
    code = line[:2]
    path = line[3:]
    if code == '??':
        entries.append(['A', path])
    elif path and ' -> ' not in path:
        entries.append([code.strip() or 'M', path])
for parts in entries:
    status=parts[0]
    paths=parts[1:]
    if status.startswith('D') or status.startswith('R'): raise SystemExit(f'destructive deletion or rename is not authorized: {parts}')
    for p in paths:
        n=p.replace('\\','/')
        if n in PROHIBITED_NAMES or Path(n).name in PROHIBITED_NAMES: raise SystemExit(f'dependency/package file changed: {n}')
        aion205_allowed = program_state in implemented_states and (n == AION205[0] or n.startswith(AION205[1]))
        source_registry_allowed = program_state == 'source_provenance_registry_implemented_write_disabled_pending_closeout' and n in SOURCE_REGISTRY_SOURCE
        if n.startswith(PROHIBITED_PREFIXES) and not (aion205_allowed or source_registry_allowed): raise SystemExit(f'prohibited runtime/source path changed: {n}')
        if n.startswith(AION205) and not aion205_allowed: raise SystemExit(f'AION-205 implementation source added by AION-204: {n}')
if program_state not in implemented_states:
    for p in AION205:
        if (ROOT/p).exists(): raise SystemExit(f'AION-205 source exists during AION-204: {p}')
for path in list((ROOT/'examples/knowledge-intelligence').glob('*.json'))+list((ROOT/'operator-console-static/demo-data').glob('knowledge-intelligence*.json')):
    text=path.read_text()
    if SECRET.search(text): raise SystemExit(f'sensitive token pattern found in {path}')
    for host in URL.findall(text):
        h=host.lower().split(':',1)[0]
        if not (h.endswith('.example') or h.endswith('.test') or h.endswith('.invalid')):
            raise SystemExit(f'live URL host is not reserved documentation domain in {path}: {host}')
if run(['git','rev-parse','aion-v0.1.0^{commit}']).stdout.strip()!=EXPECTED: raise SystemExit('aion-v0.1.0 tag moved')
if run(['git','tag','--list','v0.2*','aion-v0.2*']).stdout.strip(): raise SystemExit('v0.2 tag exists')
__AION204_NOGO__
echo "knowledge intelligence research authorization no-go PASS"
