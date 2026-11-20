import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from caller_patterns_next import recover, render


class NextCallerPatternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = json.loads((ROOT / 'analysis/call-helper-specs.json').read_text())['routines']
        cls.entries = recover(cls.specs)
        cls.by_kind = {entry['kind']: entry for entry in cls.entries}

    def test_recovers_observed_interfaces(self):
        self.assertEqual(self.by_kind['null_delegate'],
                         dict(address='0x8004B5F8', kind='null_delegate', offset=0x2f0, target=0x800537f4))
        self.assertEqual(self.by_kind['sentinel']['global'], 0x803324c8)
        self.assertEqual(self.by_kind['store_result']['field'], 0x540)
        self.assertEqual(self.by_kind['init_pointer']['offset'], 0xd0)
        self.assertEqual({entry['kind'] for entry in self.entries},
                         {'two_calls', 'clear_guard', 'store_result', 'init_pointer',
                          'null_delegate', 'sentinel', 'clear_subobject'})

    def test_rejects_every_changed_executable_statement(self):
        selected = {entry['address'] for entry in self.entries}
        for spec in self.specs:
            if spec['address'] not in selected:
                continue
            for index in range(84, len(spec['body'])):
                if spec['body'][index] == 'TAK_INTEGER_STEP();':
                    continue
                changed = dict(spec, body=list(spec['body']))
                changed['body'][index] += ' /* altered */'
                with self.subTest(address=spec['address'], statement=index):
                    self.assertEqual(recover([changed]), [])

    def test_rejects_wrong_size_and_inconsistent_repeated_offset(self):
        spec = next(spec for spec in self.specs if spec['address'] == self.by_kind['clear_guard']['address'])
        self.assertEqual(recover([dict(spec, original_bytes=56)]), [])
        body = list(spec['body'])
        index = next(i for i, line in enumerate(body) if line.startswith('m->w8((r3 +'))
        body[index] = body[index].replace('0x4bc', '0x4bd')
        self.assertEqual(recover([dict(spec, body=body)]), [])

    def test_compiled_behavior_for_all_seven_shapes(self):
        # Host-sized pointers need host-aligned fixture fields. Target offsets
        # and frame/layout bytes are independently checked against the DOL.
        kinds = ['two_calls', 'clear_guard', 'store_result', 'init_pointer',
                 'null_delegate', 'sentinel', 'clear_subobject']
        entries = []
        for index, kind in enumerate(kinds):
            entry = dict(self.by_kind[kind], address=f'0x8000{0x1000+index*0x100:04X}')
            if kind in ('clear_guard', 'store_result', 'init_pointer', 'null_delegate', 'clear_subobject'):
                entry['offset'] = 0
            if kind == 'init_pointer':
                entry.update(offset=16, field=0)
            if kind == 'store_result':
                entry['field'] = 0
            if kind == 'clear_subobject':
                entry.update(field=1, subobject=4)
            entries.append(entry)
        source = re.sub(r'#if TAK_FN == 0x[0-9A-Fa-f]+', '#if 1', render(entries))
        lookup = {entry['kind']: entry for entry in entries}
        two = lookup['two_calls']; guard = lookup['clear_guard']; store = lookup['store_result']
        init = lookup['init_pointer']; null = lookup['null_delegate']; sentinel = lookup['sentinel']; sub = lookup['clear_subobject']
        source += '\nstatic void *expected_self; static int sequence, calls, failure; static u32 destination;\n'
        source += f'extern "C" void fn_{two["target"]:08X}(void *p) {{ if(p!=expected_self || sequence!=0) failure=1; sequence=1; }}\n'
        source += f'extern "C" void fn_{two["target2"]:08X}(void *p) {{ if(p!=expected_self || sequence!=1) failure=1; sequence=2; }}\n'
        source += f'extern "C" void fn_{guard["target"]:08X}(void *p) {{ if(p!=expected_self || *(u8 *)p) failure=1; ++calls; }}\n'
        # Callee changes the destination pointer: the model loads it after call.
        source += f'extern "C" u32 fn_{store["target"]:08X}(void *p) {{ *(u32 **)p=&destination; return 0x1234abcd; }}\n'
        source += f'extern "C" void fn_{init["target"]:08X}(void *p) {{ if(p!=expected_self) failure=1; ++calls; }}\n'
        source += f'extern "C" u32 fn_{null["target"]:08X}(void *p) {{ if(p!=expected_self) failure=1; ++calls; return 0xabcd1234; }}\n'
        label = f'lbl_{sentinel["global"]:08X}'
        source += f'int {label}=7;\nextern "C" void fn_{sentinel["target"]:08X}(int value) {{ if(value!=7) failure=1; ++calls; }}\n'
        source += f'extern "C" void fn_{sub["target"]:08X}(void *p) {{ if(p!=(u8 *)expected_self+4 || *((u8 *)expected_self+1)) failure=1; ++calls; }}\n'
        source += r'''
int main() {
    union { void *alignment; u8 bytes[32]; } self;
    expected_self=&self; sequence=0;
    fn_80001000(&self); if(sequence!=2 || failure) return 1;
    calls=0; self.bytes[0]=0; fn_80001100(&self); if(calls) return 2;
    self.bytes[0]=255; fn_80001100(&self); if(calls!=1 || self.bytes[0] || failure) return 3;
    u32 old=0; u32 *result_field=&old;
    fn_80001200(&result_field); if(old || destination!=0x1234abcd) return 4;
    calls=0; expected_self=&self;
    fn_80001300(&self); if(calls!=1 || *(void **)&self!=(u8 *)&self+16 || failure) return 5;
    void *object=0; calls=0;
    if(fn_80001400(&object)!=0 || calls) return 6;
    object=&self;
    if(fn_80001400(&object)!=0xabcd1234 || calls!=1 || failure) return 7;
    calls=0; fn_80001500(); fn_80001500();
'''
        source += f'    if(calls!=1 || {label}!=-2 || failure) return 8;\n'
        source += r'''
    u8 child[16]; child[1]=255; u8 *child_field=child;
    expected_self=child; calls=0;
    fn_80001600(&child_field);
    if(child[1] || calls!=1 || failure) return 9;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / 'caller-patterns')
            run = subprocess.run(['clang++', '-x', 'c++', '-', '-o', executable],
                                 input=source, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            subprocess.run([executable], check=True)


if __name__ == '__main__':
    unittest.main()
