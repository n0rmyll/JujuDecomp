import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_all_matching import refinement_records, replace_refinement


class RefinementTests(unittest.TestCase):
    def report(self, *addresses):
        return {'results': [dict(address=a, function='fn_' + a[2:]) for a in addresses]}

    def test_disjoint_workers_preserve_own_object_directories(self):
        addresses = {'0x80001000', '0x80002000'}
        records = refinement_records([
            (self.report('0x80001000'), Path('/worker-one')),
            (self.report('0x80002000'), Path('/worker-two'))], addresses)
        self.assertEqual([(r[0]['address'], r[1], r[3]) for r in records], [
            ('0x80001000', Path('/worker-one'), 'fn_80001000.o'),
            ('0x80002000', Path('/worker-two'), 'fn_80002000.o')])

    def test_duplicate_within_one_report_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            refinement_records([(self.report('0x80001000', '0x80001000'), Path('/worker'))], {'0x80001000'})

    def test_overlapping_workers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            refinement_records([(self.report('0x80001000'), Path('/one')),
                                (self.report('0x80001000'), Path('/two'))], {'0x80001000'})

    def test_unregistered_address_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-caller'):
            refinement_records([(self.report('0x80001000'), Path('/one'))], {'0x80002000'})

    def test_wrong_function_name_is_rejected(self):
        report = self.report('0x80001000')
        report['results'][0]['function'] = 'fn_80002000'
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            refinement_records([(report, Path('/one'))], {'0x80001000'})

    def test_refinement_replaces_prior_result_without_touching_other_addresses(self):
        results = [dict(address='0x80001000', status='different'),
                   dict(address='0x80002000', status='match')]
        remaining = replace_refinement(results, '0x80001000', True)
        self.assertEqual(remaining, [results[1]])
        self.assertEqual(len(results), 2)

    def test_refinement_cannot_regress_match(self):
        with self.assertRaisesRegex(ValueError, 'regresses'):
            replace_refinement([dict(address='0x80001000', status='match')], '0x80001000', False)

    def test_refinement_requires_validated_baseline(self):
        with self.assertRaisesRegex(ValueError, 'no validated baseline'):
            replace_refinement([], '0x80001000', True)


if __name__ == '__main__':
    unittest.main()
