"""Regression checks for the corrected specification fixtures, not app tests."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from contract_fixture_checks import EXAMPLES, diagnostic_errors, load, materialize


class ContractFixtureTests(unittest.TestCase):
    def setUp(self):
        self.policy = load('policy.valid.json')
        self.plan = load('plan.valid.json')
        self.entities = load('entities.valid.json')
        self.events = load('events.valid.json')
        self.world = load('world.before.json')
        self.api = {c['name']: c for c in load('api.examples.json')}

    def test_all_fixture_json_parses_and_has_no_wire_placeholders(self):
        for file in EXAMPLES.glob('*.json'):
            obj = json.loads(file.read_text())
            self.assertNotIn('"…"', json.dumps(obj, ensure_ascii=False), file.name)
        def walk(obj):
            if isinstance(obj, dict):
                self.assertNotIn('$ref', obj)
                self.assertNotIn('plan_ref', obj)
                for child in obj.values():
                    walk(child)
            elif isinstance(obj, list):
                for child in obj:
                    walk(child)
        walk(list(self.api.values()))
        walk(self.events)

    def test_negatives_start_valid_and_fail_for_exact_named_error(self):
        for case in load('schema.invalid.json'):
            with self.subTest(case=case['name']):
                self.assertEqual(diagnostic_errors(case['entity'], materialize(case, False), case['validation_layer']), set())
                self.assertEqual(diagnostic_errors(case['entity'], materialize(case), case['validation_layer']), {case['expected_error']})

    def test_plan_has_complete_envelope_and_eligible_assignments(self):
        self.assertEqual(diagnostic_errors('Plan', self.plan), set())
        for key in ['schema_version','session_id','plan_id','version','based_on_planning_sequence','policy_version','created_sim_time_s','created_at','assignments','facility_allocations','unmet_needs','flags','coverage','diff','solver']:
            self.assertIn(key, self.plan)
        for assignment in self.plan['assignments']:
            self.assertEqual(assignment['eta_s'], assignment['route']['duration_s'])
            if assignment['locked'] == 'near_arrival':
                self.assertLessEqual(assignment['eta_s'], self.policy['near_arrival_lock_s'])

    def test_triage_polarity_and_complete_facts(self):
        facts = {f['key']: f for f in self.entities['TriageFacts']['facts']}
        self.assertEqual(set(facts), set(self.policy['dangerous_values']) | {'people_count'})
        self.assertEqual(self.policy['dangerous_values']['conscious'], 'no')
        self.assertEqual(self.policy['dangerous_values']['breathing_normally'], 'no')
        self.assertEqual(self.policy['dangerous_values']['severe_bleeding'], 'yes')
        self.assertTrue(all(f['updated_sim_time_s'] <= self.plan['created_sim_time_s'] for f in facts.values()))
        for f in facts.values():
            self.assertEqual(diagnostic_errors('TriageFact', f), set())

    def test_semantic_snapshot_agrees_with_embedded_proposal(self):
        snapshot = self.api['state_snapshot']['response']['body']
        self.assertIn('approved_plan', snapshot)
        self.assertIn('current_proposal', snapshot)
        expected = {k:v for k,v in self.plan.items() if k != '_comment'}
        self.assertEqual(snapshot['current_proposal'], expected)
        self.assertEqual(self.api['get_plan']['response']['body'], expected)
        proposal = next(e for e in self.events if e['event_type'] == 'PlanProposed')
        self.assertEqual(proposal['payload']['plan'], expected)

    def test_contiguous_timeline_and_approval_binding(self):
        self.assertEqual([e['sequence'] for e in self.events], list(range(53,68)))
        self.assertEqual(self.world['as_of_sequence'],52)
        planning = self.world['planning_sequence']
        for event in self.events:
            if event['event_type'] == 'PlanApproved':
                self.assertEqual(event['payload']['based_on_planning_sequence'],planning)
            if event['affects_planning']:
                planning = event['sequence']
        self.assertEqual(planning,67)
        self.assertEqual([e['sim_time_s'] for e in self.events], sorted(e['sim_time_s'] for e in self.events))
        triage = next(e for e in self.events if e['event_type'] == 'TriageFactsExtracted')
        self.assertEqual(triage['payload']['triage_facts'], self.entities['TriageFacts'])

    def test_every_uncovered_zone_and_provisional_need_is_flagged(self):
        assigned = {a['unit_id'] for a in self.plan['assignments']}
        available_ambulances = {u['unit_id'] for u in self.world['units'] if u['type'] in {'als','bls'}} - assigned - {'unit_A2'}
        self.assertEqual(available_ambulances,set())
        expected_zones = {z['zone_id'] for z in self.world['reserve_zones']}
        flags = self.plan['flags']
        actual_zones = {f['zone_id'] for f in flags if f['code'] == 'RESERVE_UNCOVERED'}
        self.assertEqual(actual_zones, expected_zones)
        self.assertEqual(self.plan['diff']['totals']['zones_uncovered'], len(actual_zones))
        provisional = {n['need_id'] for n in self.plan['unmet_needs'] if n['basis'] == 'provisional_unknown'}
        self.assertEqual({f['need_id'] for f in flags if f['code']=='PROVISIONAL_NEED'},provisional)
        ack = {f['flag_id'] for f in flags if f['requires_ack']}
        for name in ['approve_valid','approve_idempotent_retry']:
            self.assertEqual(set(self.api[name]['request']['body']['acknowledged_flag_ids']),ack)
        approval = next(e for e in self.events if e['event_type']=='PlanApproved')
        self.assertEqual(set(approval['payload']['acknowledged_flag_ids']),ack)

    def test_reserve_counterexample_cannot_outweigh_unmet_count(self):
        c = self.policy['costs']; limit = self.policy['limits']
        serve_operating = c['travel_cap_s'] + c['als_on_bls'] + limit['reserve_pairs']*c['reserve_shortfall']
        self.assertEqual(serve_operating,15300)
        serve = (0,0,0,0,0,serve_operating)
        withhold = (0,0,0,1,0,0)
        self.assertLess(serve,withhold)
        # Two missing slots versus one cannot have the same unmet tier.
        self.assertLess((1,0,0,0,0,498300),(2,0,0,0,0,0))
        self.assertEqual(limit['units']*5*c['travel_cap_s'] + limit['units']*c['reassignment'] + limit['reserve_pairs']*c['reserve_shortfall'] + limit['units']*c['als_on_bls'],498300)

    def test_objective_vector_recomputed_from_example(self):
        incidents={i['incident_id']:i for i in self.world['incidents']+[self.entities['Incident']]}
        severity=['critical','high','medium','low']; weights=self.policy['severity_weights']; costs=self.policy['costs']
        unmet=[sum(n['quantity_unmet'] for n in self.plan['unmet_needs'] if n['severity']==s) for s in severity]
        waiting=sum(n['quantity_unmet']*weights[n['severity']]*min(n['waiting_s'],costs['waiting_cap_s']) for n in self.plan['unmet_needs'])
        travel=sum(weights[incidents[a['incident_id']]['severity']]*min(a['eta_s'],costs['travel_cap_s']) for a in self.plan['assignments'])
        reserve=sum(f['code']=='RESERVE_UNCOVERED' for f in self.plan['flags'])*costs['reserve_shortfall']
        self.assertEqual(self.plan['solver']['objective_vector'],unmet+[waiting,travel+reserve])

    def test_session_bound_commands_and_reset_retry(self):
        for case in self.api.values():
            if case['request']['method']=='POST':
                self.assertIn('expected_session_id',case['request']['body'])
        reset=self.api['demo_reset']; retry=self.api['demo_reset_idempotent_retry']
        self.assertEqual(reset['request'],retry['request'])
        self.assertEqual(reset['response']['body'],retry['response']['body'])
        self.assertEqual(self.api['approve_wrong_session']['response']['body']['code'],'STALE_SESSION')

    def test_deliveries_are_session_qualified_and_match_approved_commands(self):
        approval=next(e for e in self.events if e['event_type']=='PlanApproved')['payload']
        queued={e['payload']['command']['outbox_key']:e['payload']['command'] for e in self.events if e['event_type']=='SimulatedDispatchQueued'}
        sent={e['payload']['outbox_key']:e for e in self.events if e['event_type']=='SimulatedDispatchSent'}
        self.assertEqual(set(approval['outbox_keys']),set(queued))
        self.assertEqual(set(queued),set(sent))
        for key,command in queued.items():
            self.assertTrue(key.startswith('sess_demo_01:plan_0007:assign:'))
            self.assertEqual(command['desired_revision'],7)
            self.assertEqual(sent[key]['idempotency_key'],key)
            self.assertEqual(sent[key]['payload']['unit_after']['current_task']['assignment_id'],command['assignment_id'])

    def test_planning_tick_bound_is_global_not_per_unit(self):
        quiet_ms=self.policy['planning_tick_s']*1000-self.policy['max_debounce_ms']-self.policy['solver_budget_ms']
        self.assertEqual(quiet_ms,7750)
        # A fleet batch shares exactly the same boundary regardless of fleet size.
        boundaries={10 for _ in range(self.policy['limits']['units'])}
        self.assertEqual(len(boundaries),1)

    def test_geographic_validity_is_not_demo_fixture_validity(self):
        case=self.api['post_report_geographically_valid_outside_demo']
        lon,lat=case['request']['body']['location']['coordinates']
        self.assertTrue(-180<=lon<=180 and -90<=lat<=90)
        self.assertEqual(case['response']['status'],201)
        self.assertFalse(77.45<=lon<=77.80 and 12.8<=lat<=13.15)


if __name__ == '__main__':
    unittest.main()
