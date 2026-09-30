#!/usr/bin/env python3
"""Create/reuse task issues and labels in the configured repository (explicit write)."""
import json
import sys
from pathlib import Path
from taskboard import gh, validate_graph

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.argv[1:] != ['--apply']:
        raise SystemExit('Usage: python3 scripts/bootstrap_github.py --apply (writes GitHub issues and labels)')
    manifest = json.loads((ROOT / 'docs/tasks.json').read_text())
    tasks, repo = manifest['tasks'], manifest['repository']
    validate_graph(tasks)
    labels = {
        'agent:claude': ('D97757', 'Development task owned by Claude'),
        'agent:codex': ('1F6FEB', 'Development task owned by Codex'),
        'status:ready': ('2DA44E', 'All prerequisite tasks completed; ready to start'),
        'status:blocked': ('D4C5F9', 'Waiting for prerequisite tasks'),
        'status:doing': ('0969DA', 'Claimed and being implemented'),
        'status:review': ('FBCA04', 'Waiting for independent agent review'),
        'status:done': ('0E8A16', 'Completed with completed prerequisites'),
        'status:cancelled': ('B60205', 'Closed without completing; does not unlock dependents'),
        'scope:core': ('C2E0C6', 'Core build and acceptance'),
        'scope:stretch': ('E4E669', 'Optional extension after core acceptance'),
    }
    existing_labels = gh('api', f'repos/{repo}/labels?per_page=100')
    known = {l['name'] for l in existing_labels}
    for name, (color, description) in labels.items():
        if name not in known:
            gh('api', '--method', 'POST', f'repos/{repo}/labels', '--input', '-',
               payload=dict(name=name, color=color, description=description))
    pages = gh('api', f'repos/{repo}/issues?state=all&per_page=100', '--paginate', '--slurp')
    existing = {i['title']: i for page in pages for i in page if 'pull_request' not in i}
    map_path = ROOT / '.github/task-map.json'
    mapping = json.loads(map_path.read_text())
    for task in tasks:
        title = f"[{task['id']}] {task['title']}"
        if task['id'] in mapping:
            continue
        if title in existing:
            mapping[task['id']] = existing[title]['number']
        else:
            deps = ', '.join(f"{d} (#{mapping[d]})" for d in task['depends_on']) or 'None: start here'
            next_tasks = ', '.join(f"{t['id']} ({t['owner']})" for t in tasks if task['id'] in t['depends_on']) or 'No automatic successor'
            criteria = '\n'.join(f'- [ ] {x}' for x in task['acceptance'])
            body = f"""## Assignment

- **Agent:** {task['owner']}
- **Reviewer:** {task['reviewer']}
- **Dependencies:** {deps}
- **Owned paths:** {', '.join('`' + p + '`' for p in task['paths'])}
- **Scope:** {'Optional stretch' if task['optional'] else 'Core'}

## Acceptance criteria

{criteria}

## Handoff

Save `docs/handoffs/{task['id']}.md` with exact checks, contract changes, reviewed commit and remaining limitations. Open a PR with `Closes #<this issue>`. Complete only after acceptance, review and merge. Never close an unfinished task merely to unlock the next one.

**Successors after completion:** {next_tasks}. Other prerequisites may still block them.

Read `AGENTS.md`, `docs/WORKFLOW.md`, `docs/MODELS.md` and `docs/START-HERE.md`. The machine-readable dependency source is `docs/tasks.json`. GitHub Actions updates readiness labels; it does not start an AI model.
"""
            result = gh('api', '--method', 'POST', f'repos/{repo}/issues', '--input', '-', payload={
                'title': title, 'body': body,
                'labels': [f"agent:{task['owner']}", 'scope:stretch' if task['optional'] else 'scope:core',
                           'status:blocked' if task['depends_on'] else 'status:ready']})
            mapping[task['id']] = result['number']
        map_path.write_text(json.dumps(mapping, indent=2) + '\n')
        print(f"{task['id']}: https://github.com/{repo}/issues/{mapping[task['id']]}", flush=True)


if __name__ == '__main__':
    main()
