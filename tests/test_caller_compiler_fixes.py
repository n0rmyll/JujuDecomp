import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from caller_compiler_fixes import recover, render


class CallerCompilerFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = json.loads((ROOT / 'analysis/call-helper-specs.json').read_text())['routines']
        cls.by_address = {s['address']: s for s in cls.specs}

    def entry(self, address):
        found = recover([self.by_address[address]])
        self.assertEqual(len(found), 1)
        return found[0]

    def run_host(self, address, extra):
        source = '#define TAK_FN ' + address + '\n' + render([self.entry(address)]) + extra
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / 'caller')
            run = subprocess.run(['clang++', '-x', 'c++', '-', '-o', executable],
                                 input=source, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            subprocess.run([executable], check=True)

    def test_recovers_four_complete_shapes_and_rejects_all_changed_statements(self):
        expected = {'0x800099CC': 'embedded_guard', '0x800C76F8': 'switch_guard',
                    '0x800718D4': 'swap_zero', '0x8008A318': 'result_flags'}
        self.assertEqual({e['address']: e['kind'] for e in recover(self.specs)}, expected)
        for address in expected:
            spec = self.by_address[address]
            self.assertEqual(recover([dict(spec, original_bytes=52)]), [])
            for i in range(84, len(spec['body'])):
                if spec['body'][i] == 'TAK_INTEGER_STEP();':
                    continue
                body = list(spec['body']); body[i] += ' /* changed */'
                with self.subTest(address=address, statement=i):
                    self.assertEqual(recover([dict(spec, body=body)]), [])

    def test_embedded_guard_passes_subobject_only_when_nonzero(self):
        self.run_host('0x800099CC', r'''
static int calls; static Embedded *seen;
extern "C" void fn_801B5550(Embedded *p) { ++calls; seen=p; }
int main() {
    Object self;
    self.sub.value=0; fn_800099CC(&self); if(calls) return 1;
    self.sub.value=0x80000000u; fn_800099CC(&self);
    if(calls!=1 || seen!=&self.sub) return 2;
    self.sub.value=0; fn_800099CC(&self);
    return calls==1 ? 0 : 3;
}
''')

    def test_switch_guard_accepts_only_case_two(self):
        self.run_host('0x800C76F8', r'''
static int calls; static Object *seen;
extern "C" void fn_800C81E4(Object *p) { ++calls; seen=p; }
int main() {
    Object self; int values[]={-1,0,1,3,0x7fffffff};
    for(unsigned i=0;i<5;++i) { self.value=values[i]; fn_800C76F8(&self); }
    if(calls) return 1;
    self.value=2; fn_800C76F8(&self);
    return calls==1 && seen==&self ? 0 : 2;
}
''')

    def test_swap_forwards_both_pointers_and_zero(self):
        self.run_host('0x800718D4', r'''
static void *first_seen, *second_seen; static u32 third_seen=99;
extern "C" void fn_801B50C4(void *first, void *second, u32 third) {
    first_seen=first; second_seen=second; third_seen=third;
}
int main() {
    int first,second; fn_800718D4(&first,&second);
    return first_seen==&second && second_seen==&first && third_seen==0 ? 0 : 1;
}
''')

    def test_result_flags_update_callee_result_without_neighbor_writes(self):
        self.run_host('0x8008A318', r'''
static Object output; static void *seen;
extern "C" Object *fn_801EAE24(void *p) { seen=p; return &output; }
int main() {
    Object input;
    for(unsigned i=0;i<sizeof(output.pad);++i) output.pad[i]=0x5a;
    input.one=input.zero=0xaa; output.one=output.zero=0xff;
    fn_8008A318(&input);
    if(seen!=&input || output.one!=1 || output.zero!=0) return 1;
    if(input.one!=0xaa || input.zero!=0xaa) return 2;
    for(unsigned i=0;i<sizeof(output.pad);++i) if(output.pad[i]!=0x5a) return 3;
    return 0;
}
''')


if __name__ == '__main__':
    unittest.main()
