#!/usr/bin/env python3
"""Check setup consistency without requiring app dependencies or credentials."""
import json
import re
from pathlib import Path
from taskboard import validate_graph

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'docs/tasks.json').read_text())
tasks = manifest['tasks']
validate_graph(tasks)
required = ['AGENTS.md', 'CLAUDE.md', 'README.md', 'docs/START-HERE.md',
            'docs/WORKFLOW.md', 'docs/MODELS.md', 'docs/BRIEF.md',
            'docs/handoffs/TEMPLATE.md', '.github/workflows/ci.yml',
            '.github/workflows/handoffs.yml']
for path in required:
    assert (ROOT / path).is_file(), f'Missing {path}'
mapping = json.loads((ROOT / '.github/task-map.json').read_text())
if mapping:
    assert set(mapping) == {t['id'] for t in tasks}, 'Partial issue map'
    assert all(type(n) is int and n > 0 for n in mapping.values()), 'Invalid issue number'
    assert len(set(mapping.values())) == len(mapping), 'Duplicate issue numbers'
workflow = (ROOT / 'docs/WORKFLOW.md').read_text()
for task in tasks:
    assert task['id'] in workflow, f'Task missing from workflow: {task["id"]}'
for path in (ROOT / '.claude/agents').glob('*.md'):
    text = path.read_text()
    assert text.startswith('---\n'), f'No frontmatter: {path}'
    frontmatter = text.split('---', 2)[1]
    for key in ['name', 'description', 'model']:
        assert re.search(rf'^{key}: .+', frontmatter, re.M), f'Missing {key}: {path}'
# Catch broken relative file links in authored Markdown, excluding scratch output.
for path in [ROOT / 'README.md', * (ROOT / 'docs').rglob('*.md')]:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        dest = target.split('#', 1)[0]
        assert (path.parent / dest).exists(), f'Broken link in {path}: {target}'
print(f'Setup valid: {len(tasks)} acyclic tasks, instruction files and links checked.')
