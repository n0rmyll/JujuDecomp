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
    def test_signed_arithmetic_helpers_and_dependencies(self):
        row=routine(['mulhw r3, r3, r4','divw r3, r3, r4','divwu r3, r3, r4','subfc r3, r3, r4','blr'])
        source=render([translate(row,full_context=True)],full_context=True)
        self.assertIn('static int64_t signed_wide(',source)
        self.assertLess(source.index('static int64_t signed_wide('),source.index('static uint32_t multiply_high_signed('))
        self.assertIn('r3 = r4 - r3;',source)
        self.assertIn('UINT32_C(0x80000000) && y == UINT32_MAX',source)

    def test_extended_integer_operations(self):
        row=routine(['nop','xoris r3, r3, 0xffff','mulhwu r3, r3, r4','addic. r3, r3, -1','crclr cr1eq','crset 5','blr'])
        spec=translate(row,full_context=True)
        source=render([spec],full_context=True)
        self.assertIn('UINT32_C(0xffff0000)',source)
        self.assertIn('(uint64_t)r3 * (uint64_t)r4',source)
        self.assertIn('cr0 = cmp_signed(r3, 0u);',source)
        self.assertIn('cr1 = cr1 & UINT32_C(0xfffffffb);',source)
        self.assertIn('cr1 = cr1 | UINT32_C(0x2);',source)

    def test_reject_unmodeled_condition_so_bit(self):
        with self.assertRaisesRegex(ValueError,'Unmodeled condition SO bit'):
            translate(routine(['crclr 7','blr']),full_context=True)

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

    def test_full_context_makes_stack_and_saved_registers_explicit(self):
        spec=translate(routine(['stwu r1, -0x10(r1)','stmw r30, 0x8(r1)',
                                'lmw r30, 0x8(r1)','addi r1, r1, 0x10','blr']),full_context=True)
        source=render([spec],full_context=True)
        self.assertIn('r1 = input[1];',source)
        self.assertIn('r30 = input[30];',source)
        self.assertIn('output[41]=cr7;',source)

    def test_caller_render_keeps_memory_callbacks_and_explicit_boundary(self):
        row=routine(['mflr r31','bl fn_80002000','mtlr r31','lwz r3, 0x0(r3)','blr'])
        row['words']=[0x7fe802a6,0x48000ffd,0x7fe803a6,0x80630000,0x4e800020]
        spec=translate(row,full_context=True,allow_calls=True)
        source=render([spec],full_context=True,allow_calls=True)
        self.assertIn('calls->invoke((target), state)',source)
        self.assertIn('m->r32(',source)
        self.assertNotIn('m->state[',source)
        self.assertEqual(spec['external_call_sites'][0]['target'],'UINT32_C(0x80002000)')


if __name__ == '__main__': unittest.main()
