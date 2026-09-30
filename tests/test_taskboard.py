import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from taskboard import classify, validate_graph


def task(id, deps):
    return dict(id=id, depends_on=deps, owner='codex', reviewer='claude', paths=['backend/'], acceptance=['verified'])


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [task('CC-01', []), task('CC-02', ['CC-01']), task('CC-03', ['CC-01']),
                      task('CC-04', ['CC-02', 'CC-03'])]
        self.issues = {t['id']: dict(state='open', labels=[]) for t in self.tasks}

    def complete(self, id):
        self.issues[id].update(state='closed', state_reason='completed')

    def test_initial_queue_has_only_root(self):
        self.assertEqual(classify(self.tasks, self.issues),
                         {'CC-01': 'ready', 'CC-02': 'blocked', 'CC-03': 'blocked', 'CC-04': 'blocked'})

    def test_parallel_lanes_and_join(self):
        self.complete('CC-01')
        state = classify(self.tasks, self.issues)
        self.assertEqual((state['CC-02'], state['CC-03']), ('ready', 'ready'))
        self.complete('CC-02')
        self.assertEqual(classify(self.tasks, self.issues)['CC-04'], 'blocked')
        self.complete('CC-03')
        self.assertEqual(classify(self.tasks, self.issues)['CC-04'], 'ready')

    def test_cancelled_is_not_completed(self):
        self.issues['CC-01'].update(state='closed', state_reason='not_planned')
        states = classify(self.tasks, self.issues)
        self.assertEqual(states['CC-01'], 'cancelled')
        self.assertEqual(states['CC-02'], 'blocked')

    def test_reopen_invalidates_descendants(self):
        for id in self.issues:
            self.complete(id)
        self.issues['CC-01']['state'] = 'open'
        self.assertEqual(classify(self.tasks, self.issues)['CC-04'], 'blocked')

    def test_keeps_active_status_only_if_dependencies_complete(self):
        self.issues['CC-02']['labels'] = [{'name': 'status:doing'}]
        self.assertEqual(classify(self.tasks, self.issues)['CC-02'], 'blocked')
        self.complete('CC-01')
        self.assertEqual(classify(self.tasks, self.issues)['CC-02'], 'doing')
        self.issues['CC-02']['labels'] = [{'name': 'status:review'}]
        self.assertEqual(classify(self.tasks, self.issues)['CC-02'], 'review')

    def test_missing_live_issue_fails_closed(self):
        del self.issues['CC-03']
        with self.assertRaises(KeyError):
            classify(self.tasks, self.issues)

    def test_rejects_cycles_unknown_dependencies_and_duplicates(self):
        bad = copy.deepcopy(self.tasks)
        bad[0]['depends_on'] = ['CC-04']
        with self.assertRaises(ValueError):
            validate_graph(bad)
        bad[0]['depends_on'] = ['CC-99']
        with self.assertRaises(ValueError):
            validate_graph(bad)
        with self.assertRaises(ValueError):
            validate_graph(self.tasks + [self.tasks[0]])


if __name__ == '__main__':
    unittest.main()
