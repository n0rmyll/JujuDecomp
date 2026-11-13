"""Small independent checks for the differential oracle's CPU semantics."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ppc_leaf import execute, bitmask, rotate, signed


class Memory:
    def __init__(self):
        self.values = {}
        self.events = []

    def read(self, a, size):
        self.events.append(('read', a, size))
        return self.values.get((a, size), 0)

    def write(self, a, value, size):
        self.events.append(('write', a, value, size))
        self.values[a, size] = value


class PowerPCOracleTests(unittest.TestCase):
    def test_bit_numbering(self):
        self.assertEqual(bitmask(0, 7), 0xff000000)
        self.assertEqual(bitmask(31, 29), 0xfffffffd)
        self.assertEqual(rotate(0x12345678, 8), 0x34567812)
        self.assertEqual(rotate(0x12345678, 0), 0x12345678)
        self.assertEqual(signed(0xffff, 16), -1)

    def test_wrapping_add_and_return(self):
        # addi r3,r3,1; blr
        self.assertEqual(execute({0: 0x38630001, 4: 0x4e800020},
                                 (0xffffffff, 0, 0, 0), Memory()), 0)

    def test_signed_compare_and_conditional_return(self):
        # cmpwi r3,0; bltlr; li r3,7; blr
        words = {0: 0x2c030000, 4: 0x4d800020, 8: 0x38600007, 12: 0x4e800020}
        self.assertEqual(execute(words, (0xffffffff, 0, 0, 0), Memory()), 0xffffffff)
        self.assertEqual(execute(words, (0, 0, 0, 0), Memory()), 7)

    def test_count_register_loop(self):
        # li r0,3; mtctr r0; addi r3,r3,1; bdnz -4; blr
        words = {0: 0x38000003, 4: 0x7c0903a6, 8: 0x38630001,
                 12: 0x4200fffc, 16: 0x4e800020}
        self.assertEqual(execute(words, (10, 0, 0, 0), Memory()), 13)

    def test_signed_halfword_and_store_width(self):
        # lha r3,0(r4); stb r3,0(r5); blr
        words = {0: 0xa8640000, 4: 0x98650000, 8: 0x4e800020}
        memory = Memory()
        memory.values[0x1000, 2] = 0xff80
        self.assertEqual(execute(words, (0, 0x1000, 0x2000, 0), memory), 0xffffff80)
        self.assertEqual(memory.events, [('read', 0x1000, 2), ('write', 0x2000, 128, 1)])

    def test_sda_base_and_width(self):
        # lbz r3,-0x6f84(r13); blr (global 0x803312FC)
        memory = Memory()
        memory.values[0x803312fc, 1] = 255
        self.assertEqual(execute({0: 0x886d907c, 4: 0x4e800020}, (0, 0, 0, 0), memory), 255)

    def test_load_with_update_changes_base(self):
        # lwzu r5,4(r3); lwz r3,4(r3); blr
        memory = Memory()
        memory.values[0x1004, 4] = 111
        memory.values[0x1008, 4] = 222
        words = {0: 0x84a30004, 4: 0x80630004, 8: 0x4e800020}
        self.assertEqual(execute(words, (0x1000, 0, 0, 0), memory), 222)
        self.assertEqual(memory.events, [('read', 0x1004, 4), ('read', 0x1008, 4)])

    def test_load_with_update_invalid_operands_fail(self):
        # lwzu r3,4(r3) is invalid: source and destination cannot coincide.
        with self.assertRaisesRegex(ValueError, 'Invalid load-with-update'):
            execute({0: 0x84630004}, (0x1000, 0, 0, 0), Memory())

    def test_negate_and_count_leading_zeros(self):
        # neg r3,r3; blr, then cntlzw r3,r3; blr.
        for value, expected in ((0, 0), (1, 0xffffffff), (0x80000000, 0x80000000)):
            self.assertEqual(execute({0: 0x7c6300d0, 4: 0x4e800020},
                                     (value, 0, 0, 0), Memory()), expected)
        for value, expected in ((0, 32), (1, 31), (0x80000000, 0), (0xffffffff, 0), (0x100, 23)):
            self.assertEqual(execute({0: 0x7c630034, 4: 0x4e800020},
                                     (value, 0, 0, 0), Memory()), expected)

    def test_immediate_subtraction_modulo(self):
        # subfic r3,r3,1; blr. This routine subset does not consume XER carry.
        for value, expected in ((0, 1), (1, 0), (2, 0xffffffff), (0xffffffff, 2)):
            self.assertEqual(execute({0: 0x20630001, 4: 0x4e800020},
                                     (value, 0, 0, 0), Memory()), expected)

    def test_signed_shift(self):
        # srawi r3,r3,31; blr
        for value, expected in ((0, 0), (0x7fffffff, 0), (0x80000000, 0xffffffff), (0xffffffff, 0xffffffff)):
            self.assertEqual(execute({0: 0x7c63fe70, 4: 0x4e800020},
                                     (value, 0, 0, 0), Memory()), expected)

    def test_nor(self):
        # nor r3,r3,r4; blr
        self.assertEqual(execute({0: 0x7c6320f8, 4: 0x4e800020},
                                 (0xff000000, 0x000000ff, 0, 0), Memory()), 0x00ffff00)

    def test_indexed_byte_read(self):
        # lbzx r3,r4,r5; blr, including address addition wrap.
        memory = Memory()
        memory.values[1, 1] = 0xab
        self.assertEqual(execute({0: 0x7c6428ae, 4: 0x4e800020},
                                 (0, 0xffffffff, 2, 0), memory), 0xab)
        self.assertEqual(memory.events, [('read', 1, 1)])

    def test_recording_immediate_subtraction(self):
        # addic. r3,r3,-1; bltlr; addi r3,r3,5; blr
        words = {0: 0x3463ffff, 4: 0x4d800020, 8: 0x38630005, 12: 0x4e800020}
        self.assertEqual(execute(words, (0, 0, 0, 0), Memory()), 0xffffffff)
        self.assertEqual(execute(words, (2, 0, 0, 0), Memory()), 6)

    def test_byte_load_with_update(self):
        # lbzu r3,1(r4); add r3,r3,r4; blr
        memory = Memory(); memory.values[0x1001, 1] = 0xab
        self.assertEqual(execute({0: 0x8c640001, 4: 0x7c632214, 8: 0x4e800020},
                                 (0, 0x1000, 0, 0), memory), 0x10ac)

    def test_byte_store_with_update(self):
        # stbu r3,-1(r4); mr r3,r4; blr
        memory = Memory()
        self.assertEqual(execute({0: 0x9c64ffff, 4: 0x7c832378, 8: 0x4e800020},
                                 (0x123456ab, 0x1000, 0, 0), memory), 0xfff)
        self.assertEqual(memory.events, [('write', 0xfff, 0xab, 1)])

    def test_halfword_load_with_update(self):
        # lhzu r3,2(r4); mr r3,r4; blr
        memory = Memory(); memory.values[0x1002, 2] = 0xffff
        self.assertEqual(execute({0: 0xa4640002, 4: 0x7c832378, 8: 0x4e800020},
                                 (0, 0x1000, 0, 0), memory), 0x1002)
        self.assertEqual(memory.events, [('read', 0x1002, 2)])

    def test_indexed_halfword_store(self):
        # sthx r3,r4,r5; blr
        memory = Memory()
        execute({0: 0x7c642b2e, 4: 0x4e800020}, (0x12345678, 0x1000, 6, 0), memory)
        self.assertEqual(memory.events, [('write', 0x1006, 0x5678, 2)])

    def test_variable_right_shift(self):
        # srw r3,r3,r4; blr: low six shift bits matter.
        for amount, expected in ((0, 0x80000000), (31, 1), (32, 0), (63, 0), (64, 0x80000000)):
            self.assertEqual(execute({0: 0x7c632430, 4: 0x4e800020},
                                     (0x80000000, amount, 0, 0), Memory()), expected)

    def test_xor_and_eighth_argument(self):
        self.assertEqual(execute({0: 0x7c632278, 4: 0x4e800020},
                                 (0xff00, 0x0ff0, 0, 0), Memory()), 0xf0f0)
        # mr r3,r10; blr
        self.assertEqual(execute({0: 0x7d435378, 4: 0x4e800020},
                                 (0, 0, 0, 0, 0, 0, 0, 123), Memory()), 123)

    def test_return_register_snapshot(self):
        # addi r4,r4,1; blr: r4 may hold the low part of a wide result.
        registers = []
        result = execute({0: 0x38840001, 4: 0x4e800020},
                         (7, 0xffffffff, 2, 3, 4, 5, 6, 8), Memory(), final_registers=registers)
        self.assertEqual(result, 7)
        self.assertEqual(registers[3:11], [7, 0, 2, 3, 4, 5, 6, 8])

    def test_unsupported_instruction_fails(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            execute({0: 0}, (0, 0, 0, 0), Memory())

    def test_runaway_and_external_branch_fail(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            execute({0: 0x48000000}, (0, 0, 0, 0), Memory(), budget=5)
        with self.assertRaisesRegex(ValueError, 'outside'):
            execute({0: 0x48000008}, (0, 0, 0, 0), Memory())


if __name__ == '__main__':
    unittest.main()
