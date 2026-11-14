import sys
import subprocess
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_new_matching import PREAMBLE, caller_candidate, context_candidate, adapt_candidate, definitions, direct, original_bytes, unroll_offsets


class CandidateTests(unittest.TestCase):
    def test_context_projection_preserves_every_input_without_constants(self):
        candidate = context_candidate(dict(address='0x80001000', body=[
            'uint32_t r3 = input[3];', 'uint32_t r1 = input[1];',
            'uint32_t cr0 = input[34];', 'TAK_INTEGER_STEP();',
            'm->w32(r1, cr0);', 'return r3;']))
        self.assertIn('r3 = arg0', candidate)
        self.assertIn('r1 = arg9', candidate)
        self.assertIn('cr0 = arg34', candidate)
        self.assertIn('WRITE32(r1, cr0)', candidate)
        self.assertNotIn('input[', candidate)
        self.assertNotIn('TAK_INTEGER_STEP', candidate)

    def test_context_helper_boundaries_compile_and_run(self):
        candidate = context_candidate(dict(address='0x80001000', body=['return input[3];']))
        checks = r'''
int main() {
    if (sign_byte(0x80u) != 0xffffff80u || sign_byte(0xffu) != 0xffffffffu ||
        sign_byte(0x100u) != 0 || sign_byte(0x7fu) != 127u) return 1;
    unsigned values[] = {0, 1, 0x7fffffffu, 0x80000000u, 0xffffffffu};
    for (unsigned i=0; i<5; ++i) {
        for (unsigned n=0; n<32; ++n)
            if (shift_signed(values[i],n) != (unsigned)((int)values[i] >> n)) return 2;
        for (unsigned j=0; j<5; ++j) {
            unsigned a=values[i], b=values[j];
            if (cmp_unsigned(a,b) != (a<b ? 1u : a>b ? 2u : 4u)) return 3;
            if (cmp_signed(a,b) != ((int)a<(int)b ? 1u : (int)a>(int)b ? 2u : 4u)) return 4;
        }
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / 'helpers')
            subprocess.run(['clang', '-x', 'c++', '-', '-o', executable],
                           input=candidate.replace("#define __builtin_clz(x) __cntlzw(x)", "") + checks, text=True, capture_output=True, check=True)
            subprocess.run([executable], check=True)

    def test_caller_direct_and_indirect_destinations(self):
        candidate = caller_candidate(dict(address='0x80001000', body=[
            'uint32_t r3 = input[3];', 'uint32_t r4 = input[4];',
            'uint32_t call_target_80001004 = UINT32_C(0x80002000);',
            'TAK_OPAQUE_CALL(call_target_80001004);',
            'uint32_t call_target_80001008 = r4;',
            'TAK_OPAQUE_CALL(call_target_80001008);', 'return r3;']))
        self.assertIn('extern "C" uint32_t fn_80002000(', candidate)
        self.assertIn('r3 = fn_80002000(r3, r4, r5, r6, r7, r8, r9, r10);', candidate)
        self.assertIn('))call_target_80001008)(r3, r4, r5, r6, r7, r8, r9, r10);', candidate)
        self.assertNotIn('TAK_OPAQUE_CALL', candidate)
        with self.assertRaisesRegex(ValueError, 'Unconverted opaque'):
            caller_candidate(dict(address='0x80001000', body=['TAK_OPAQUE_CALL(r3 + 4);']))

    def test_caller_passes_integer_arguments_and_returns_callee_result(self):
        body = [f'uint32_t r{i} = input[{i}];' for i in range(3, 11)]
        body += ['uint32_t call_target_80001004 = UINT32_C(0x80002000);',
                 'TAK_OPAQUE_CALL(call_target_80001004);', 'return r3;']
        candidate = caller_candidate(dict(address='0x80001000', body=body))
        stub = 'extern "C" uint32_t fn_80002000(' + ', '.join(
            f'uint32_t a{i}' for i in range(8)) + ') { return ' + ' + '.join(
            f'a{i} * {i+1}u' for i in range(8)) + '; }'
        arguments = ', '.join([str(i) for i in range(1, 9)] + ['0'] * 34)
        main = 'int main() { return fn_80001000(' + arguments + ') == 204u ? 0 : 1; }'
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / 'caller')
            subprocess.run(['clang', '-x', 'c++', '-', '-o', executable],
                           input=candidate.replace('#define __builtin_clz(x) __cntlzw(x)', '') + stub + main,
                           text=True, capture_output=True, check=True)
            subprocess.run([executable], check=True)

    def test_extracts_nested_functions_without_neighbor(self):
        parsed = definitions('static int helper(int a) { if(a) { return 1; } return 0; }\n'
                             'uint32_t target(uint32_t a) { return helper(a); }')
        self.assertEqual(set(parsed), {'helper', 'target'})
        self.assertNotIn('target', parsed['helper'][1])

    def test_callbacks_become_width_correct_direct_accesses(self):
        text = direct('uint32_t f(uint32_t a, const TakTarget *m) { '
                      'm->w16(a, (uint16_t)m->r32(a+4)); return helper(a,m); }')
        self.assertIn('WRITE16(a, (uint16_t)READ32(a+4))', text)
        self.assertIn('helper(a)', text)
        self.assertNotIn('TakTarget', text)

    def test_global_adaptation_precedes_helpers_and_preserves_width(self):
        source = PREAMBLE + 'static inline uint32_t h() { return READ32(0x803312fc); }'
        adapted = adapt_candidate(source, 'globals')
        self.assertIn('extern uint8_t lbl_803312FC[1];', adapted)
        self.assertIn('READ32(((uint32_t)&lbl_803312FC))', adapted)
        self.assertLess(adapted.index('extern uint8_t'), adapted.index('static inline'))

    def test_signed_adaptation_is_explicit_and_unknown_variants_fail(self):
        self.assertEqual(adapt_candidate('(a ^ 0x80000000u) < (b ^ 0x80000000u)', 'signed'),
                         '(int32_t)a < (int32_t)b')
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            adapt_candidate(PREAMBLE, 'unverified')

    def test_unknown_callbacks_fail(self):
        with self.assertRaisesRegex(ValueError, 'Unconverted'):
            direct('m->call(a,b,c,d)')

    def test_unroll_preserves_store_order_and_surrounding_statements(self):
        body = ('static const uint8_t offsets[] = {0x40, 0x38, 0x3c};'
                'm->w8(a,1); for (unsigned i = 0; i < sizeof(offsets); ++i) '
                'm->w32(a+offsets[i], 0); m->w8(a+1,2);')
        result = unroll_offsets(body)
        self.assertNotIn('offsets', result)
        self.assertLess(result.index('a+0x40'), result.index('a+0x38'))
        self.assertLess(result.index('a+0x38'), result.index('a+0x3c'))
        self.assertLess(result.index('m->w8(a,1)'), result.index('a+0x40'))
        self.assertGreater(result.index('m->w8(a+1,2)'), result.index('a+0x3c'))

    def test_original_encoding_uses_values_in_address_order(self):
        self.assertEqual(original_bytes({0x80000004: 0x4e800020, 0x80000000: 0x38600001}),
                         bytes.fromhex('386000014e800020'))

    def test_unrecognized_table_use_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            unroll_offsets('static const uint8_t offsets[] = {1,2}; return offsets[a];')


if __name__ == '__main__':
    unittest.main()
