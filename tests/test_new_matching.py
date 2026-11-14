import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_new_matching import PREAMBLE, adapt_candidate, definitions, direct, original_bytes, unroll_offsets


class CandidateTests(unittest.TestCase):
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
