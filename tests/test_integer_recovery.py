"""Validate recovery boundaries and control-flow input analysis."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from integer_recovery import translate, render


def routine(instructions):
    return {'address':'0x80001000','name':'fn_80001000',
            'size':str(len(instructions)*4),'ins':instructions}


class RecoveryBoundaryTests(unittest.TestCase):
    def test_accept_defined_loop_and_arguments(self):
        spec = translate(routine(['li r0, 0x3','mtctr r0','addi r3, r3, 0x1',
                                  'bdnz .L_80001008','blr']))
        source = render([spec])
        self.assertIn('if (ctr) goto block_80001008;', source)
        self.assertEqual(spec['static_reachable_instructions'], 5)
        self.assertNotIn('switch (', source)

    def test_reject_undefined_temporary(self):
        with self.assertRaisesRegex(ValueError, 'Implicit incoming state'):
            translate(routine(['mr r3, r11','blr']))

    def test_reject_only_conditionally_defined_temporary(self):
        with self.assertRaisesRegex(ValueError, 'Implicit incoming state'):
            translate(routine(['cmpwi r3, 0','beq .L_8000100C','li r11, 1','mr r3, r11','blr']))

    def test_reject_undefined_comparison(self):
        with self.assertRaisesRegex(ValueError, 'Implicit incoming state'):
            translate(routine(['beqlr','li r3, 1','blr']))

    def test_reject_external_jump_and_call(self):
        for instructions in (['b fn_80002000','blr'], ['bl fn_80002000','blr']):
            with self.assertRaises(ValueError): translate(routine(instructions))

    def test_reject_global_base_mutation(self):
        with self.assertRaisesRegex(ValueError, 'base-register mutation'):
            translate(routine(['li r13, 0','blr']))

    def test_reject_unsupported_fpu(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            translate(routine(['fadds f1, f1, f2','blr']))

    def test_unreachable_state_is_reported(self):
        spec = translate(routine(['blr','mr r3, r11','blr']))
        self.assertEqual(spec['static_reachable_instructions'], 1)
        self.assertEqual(spec['static_unreachable_addresses'], ['0x80001004','0x80001008'])

    def test_sda_symbol_resolution_uses_actual_base(self):
        row = routine(['lwz r3, gx@sda21(r0)','blr'])
        # lwz r3,-0x100(r2), not r13.
        row['words'] = [0x8062ff00,0x4e800020]
        spec = translate(row)
        self.assertIn('r3 = m->r32(UINT32_C(0x8033b040));', spec['body'])


if __name__ == '__main__': unittest.main()
