import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from caller_interfaces import recover, render


class CallerInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = json.loads((ROOT / 'analysis/call-helper-specs.json').read_text())['routines']
        cls.virtual = next(s for s in cls.specs if s['address'] == '0x80017024')
        cls.fill = next(s for s in cls.specs if s['address'] == '0x80003458')

    def test_recovers_observed_field_slot_and_fill_target(self):
        self.assertEqual(recover([self.virtual, self.fill]), [
            dict(address='0x80017024', kind='virtual', offset=0x123c, slot=0x14),
            dict(address='0x80003458', kind='fill', target=0x80003488)])

    def test_every_executable_statement_is_required(self):
        for spec in [self.virtual, self.fill] + [next(s for s in self.specs if s['address'] == address)
                     for address in ('0x8004F1E8', '0x8001F174', '0x8003F054', '0x800C87D0', '0x800CAD70')]:
            for index in range(84, len(spec['body'])):
                if spec['body'][index] == 'TAK_INTEGER_STEP();':
                    continue
                changed = dict(spec, body=list(spec['body']))
                changed['body'][index] += ' /* altered */'
                with self.subTest(address=spec['address'], statement=index):
                    self.assertEqual(recover([changed]), [])

    def test_rejects_wrong_region_size_and_unverified_fill_target(self):
        self.assertEqual(recover([dict(self.virtual, original_bytes=52)]), [])
        changed = dict(self.fill, body=[line.replace('0x80003488', '0x80003540') for line in self.fill['body']])
        self.assertEqual(recover([changed]), [])

    def run_host(self, source):
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / 'caller')
            run = subprocess.run(['clang++', '-x', 'c++', '-', '-o', executable],
                                 input=source, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            subprocess.run([executable], check=True)

    def test_compiled_fill_passes_arguments_and_preserves_destination(self):
        source = '#define TAK_FN 0x80003458\n' + render(recover([self.fill]))
        source += '''
static void *seen; static int value_seen; static u32 size_seen;
extern "C" void fn_80003488(void *p, int v, u32 n) {
    seen=p; value_seen=v; size_seen=n;
}
int main() {
    char destination[8];
    void *result=fn_80003458(destination, -17, 8);
    return result==destination && seen==destination && value_seen==-17 && size_seen==8 ? 0 : 1;
}
'''
        self.run_host(source)

    def test_compiled_virtual_dispatch_selects_recovered_slot(self):
        # Host pointer layout differs; exercise the generated C++ dispatch with
        # a naturally aligned field while machine-byte checks cover target offsets.
        entry = dict(address='0x80001000', kind='virtual', offset=0, slot=0x14)
        source = '#define TAK_FN 0x80001000\n' + render([entry])
        source += '''
static int called;
void CallerVirtual::slot_08() { called=8; }
void CallerVirtual::slot_0C() { called=12; }
void CallerVirtual::slot_10() { called=16; }
void CallerVirtual::slot_14() { called=20; }
int main() {
    CallerVirtual target; CallerVirtual *field=&target;
    fn_80001000(&field);
    return called==20 ? 0 : 1;
}
'''
        self.run_host(source)

    def test_compiled_swap_forwards_loaded_object_and_reversed_arguments(self):
        entry = dict(address='0x80001000', kind='swap', target=0x80002000, offset=0)
        source = '#define TAK_FN 0x80001000\n' + render([entry])
        source += r"""
static void *seen; static u32 first_seen, second_seen;
extern "C" void fn_80002000(void *p, u32 a, u32 b) { seen=p; first_seen=a; second_seen=b; }
int main() {
    int target; void *field=&target;
    fn_80001000(&field, 0x1234, 0xabcd);
    return seen==&target && first_seen==0xabcd && second_seen==0x1234 ? 0 : 1;
}
"""
        self.run_host(source)

    def test_compiled_nested_guards_take_both_paths_at_observed_widths(self):
        for width in (8, 32):
            entry = dict(address='0x80001000', kind='nested_guard', target=0x80002000,
                         offset=0, guard=4, width=width)
            source = '#define TAK_FN 0x80001000\n' + render([entry])
            source += r"""
static int calls; static void *seen;
extern "C" void fn_80002000(void *p) { ++calls; seen=p; }
int main() {
    u32 storage[2]={0,0}; u8 *field=(u8 *)storage;
    fn_80001000(&field); if(calls) return 1;
    storage[1]=0xffffffffu;
    fn_80001000(&field); if(calls!=1 || seen!=&field) return 2;
    storage[1]=0; fn_80001000(&field);
    return calls==1 ? 0 : 3;
}
"""
            with self.subTest(width=width):
                self.run_host(source)

    def test_compiled_byte_boolean_covers_every_byte(self):
        entry = dict(address='0x80001000', kind='byte_bool', target=0x80002000)
        source = '#define TAK_FN 0x80001000\n' + render([entry])
        source += r"""
static u8 result; static void *seen;
extern "C" u8 fn_80002000(void *p) { seen=p; return result; }
int main() {
    int self;
    for(u32 i=0;i<256;++i) {
        result=(u8)i;
        if(fn_80001000(&self)!=(i!=0) || seen!=&self) return 1;
    }
    return 0;
}
"""
        self.run_host(source)

    def test_compiled_bit_guard_forwards_subobject_only_when_active(self):
        entry = dict(address='0x80001000', kind='bit_guard', target=0x80002000, guard=0, offset=16)
        source = '#define TAK_FN 0x80001000\n' + render([entry])
        source += r"""
static int calls; static void *seen;
extern "C" void fn_80002000(void *p) { ++calls; seen=p; }
int main() {
    struct { CallerActiveFlag flag; u8 padding[31]; } self;
    self.flag.active=0; self.flag.other=127;
    fn_80001000(&self); if(calls) return 1;
    self.flag.active=1;
    fn_80001000(&self);
    return calls==1 && seen==(u8 *)&self+16 ? 0 : 2;
}
"""
        self.run_host(source)


if __name__ == '__main__':
    unittest.main()
