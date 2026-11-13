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
