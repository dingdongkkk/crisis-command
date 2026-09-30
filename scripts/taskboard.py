#!/usr/bin/env python3
"""Read dependency state from GitHub; optionally reconcile managed status labels."""
import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'ready', 'blocked', 'doing', 'review', 'done', 'cancelled'}


def validate_graph(tasks):
    ids = [t['id'] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate task IDs')
    by_id = {t['id']: t for t in tasks}
    visiting, visited = set(), set()

    def visit(task_id):
        if task_id not in by_id:
            raise ValueError(f'Unknown dependency: {task_id}')
        if task_id in visiting:
            raise ValueError(f'Dependency cycle at {task_id}')
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in by_id[task_id]['depends_on']:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task in tasks:
        if not re.fullmatch(r'CC-\d{2}', task['id']):
            raise ValueError('Invalid task ID')
        if task['owner'] not in {'claude', 'codex'}:
            raise ValueError('Invalid owner')
        if task['reviewer'] not in {'claude', 'codex'} or task['reviewer'] == task['owner']:
            raise ValueError('Reviewer must be the other agent')
        if not task['acceptance'] or not task['paths']:
            raise ValueError('Task needs acceptance criteria and owned paths')
        visit(task['id'])
    return by_id


def classify(tasks, issues):
    """Completed means completed with recursively completed prerequisites."""
    by_id = validate_graph(tasks)
    memo = {}

    def status(task_id):
        if task_id in memo:
            return memo[task_id]
        issue = issues[task_id]  # A missing live issue must fail, never imply ready.
        deps_done = all(status(d) == 'done' for d in by_id[task_id]['depends_on'])
        if not deps_done:
            result = 'blocked'
        elif issue['state'].lower() == 'closed':
            result = 'done' if issue.get('state_reason') == 'completed' else 'cancelled'
        else:
            labels = {x['name'] for x in issue.get('labels', [])}
            result = 'review' if 'status:review' in labels else (
                'doing' if 'status:doing' in labels else 'ready')
        memo[task_id] = result
        return result

    return {task['id']: status(task['id']) for task in tasks}


def gh(*args, payload=None):
    result = subprocess.run(['gh', *args], input=None if payload is None else json.dumps(payload),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def live_issues(repo, mapping):
    pages = gh('api', f'repos/{repo}/issues?state=all&per_page=100', '--paginate', '--slurp')
    by_number = {i['number']: i for page in pages for i in page if 'pull_request' not in i}
    missing = set(mapping.values()) - set(by_number)
    if missing:
        raise ValueError(f'Cannot find mapped issues: {sorted(missing)}')
    return {task_id: by_number[number] for task_id, number in mapping.items()}


def sync_labels(repo, mapping, issues, states):
    for task_id, status in states.items():
        number = mapping[task_id]
        labels = {x['name'] for x in issues[task_id].get('labels', [])}
        desired = f'status:{status}'
        if desired not in labels:
            gh('api', '--method', 'POST', f'repos/{repo}/issues/{number}/labels',
               '--input', '-', payload={'labels': [desired]})
        for old in sorted(labels & {f'status:{s}' for s in STATUSES} - {desired}):
            gh('api', '--method', 'DELETE', f'repos/{repo}/issues/{number}/labels/{quote(old, safe="")}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Show initial all-open plan, not live state')
    parser.add_argument('--sync', action='store_true', help='Write managed status labels to GitHub')
    args = parser.parse_args()
    if args.offline and args.sync:
        parser.error('--offline cannot be combined with --sync')
    manifest = json.loads((ROOT / 'docs/tasks.json').read_text())
    tasks, repo = manifest['tasks'], manifest['repository']
    mapping = json.loads((ROOT / '.github/task-map.json').read_text())
    validate_graph(tasks)
    if args.offline:
        issues = {t['id']: {'state': 'open', 'labels': []} for t in tasks}
    else:
        if set(mapping) != {t['id'] for t in tasks}:
            raise ValueError('Incomplete issue map; finish GitHub bootstrap first')
        issues = live_issues(repo, mapping)
    states = classify(tasks, issues)
    if args.sync:
        sync_labels(repo, mapping, issues, states)
    print('# Initial plan (offline; no live status)' if args.offline else '# Agent handoff queue')
    print('\n| Task | Agent | Status | Depends on | Issue |\n| --- | --- | --- | --- | --- |')
    for t in tasks:
        number = mapping.get(t['id'])
        link = f'[#{number}](https://github.com/{repo}/issues/{number})' if number else '-'
        print(f"| {t['id']} | {t['owner']} | {states[t['id']]} | {', '.join(t['depends_on']) or '-'} | {link} |")
    print('\nReady tasks: ' + ', '.join(t['id'] for t in tasks if states[t['id']] == 'ready'))
    print('\nAgents are started manually; these labels do not verify review quality or run a model.')


if __name__ == '__main__':
    main()
