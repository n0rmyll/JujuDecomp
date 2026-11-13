/* GJUE78 rev 0: 100 complete semantic leaf models, not original ABI or
 * compiler-matched replacements. a..d represent input r3..r6. Address
 * labels preserve provenance; class/type names remain unresolved.
 * Harness results of routines classified as void are unspecified.
 */
#include "runtime_helpers.h"

#define FN(address) uint32_t tak_resource_leaf_##address(uint32_t a, uint32_t b, \
    uint32_t c, uint32_t d, const TakTarget *m) \
    { (void)a; (void)b; (void)c; (void)d; (void)m;
#define END return 0; }

static int less(uint32_t a, uint32_t b)
{
    return (a ^ 0x80000000u) < (b ^ 0x80000000u);
}
static uint32_t sign8(uint8_t x)
{
    return (x & 0x80u) ? (uint32_t)x | 0xffffff00u : x;
}

FN(801A1798)
    m->w32(a+4, 0); m->w32(a, 0); m->w8(a+8, 0); m->w32(a+0xc, 0);
    m->w32(a+0x14, 0); m->w32(a+0x10, 0); m->w8(a+0x18, 0); m->w32(a+0x1c, 0);
    return a;
}
FN(801A1C30) if (!b) return 0; m->w8(b+0xf4, 1); return 1; }
FN(801A1C50) if (!b) return 0; m->w8(b+0xf4, 0); return 1; }
FN(801A1C70) return b ? m->r8(b+0xf4) : 1; }
FN(801A2210)
    uint16_t flags = m->r16(a+2); m->w16(a+2, (uint16_t)(flags | 1u));
END
FN(801A2220)
    uint16_t flags = m->r16(a+2); m->w16(a+2, (uint16_t)(flags & 0xfffeu));
END
FN(801AE290)
    m->w32(a+4, 0); m->w32(a, 0); m->w8(a+8, 0); m->w32(a+0xc, 0); return a;
}
FN(801B0170)
    uint32_t old_second = m->r32(a+0x14), old_first = m->r32(a+0x10);
    m->w32(a+0x10, b);
    uint32_t new_first = m->r32(a+0x10);
    m->w32(a+0x14, new_first-(old_first-old_second));
END
FN(801B3660)
    m->w32(a, 0); m->w32(a+0xc, 0); m->w32(a+0x10, 0);
    m->w8(a+4, 1); m->w8(a+5, 0); m->w32(a+0x14, 0); m->w32(a+0x18, 0);
    return a;
}
FN(801B5620) if (a) m->w32(a, 0); END
FN(801B6A14) m->w32(0x80322dac, 0); END
FN(801B6A28) m->w32(0x80322db4, 0); END
FN(801B6A3C)
    uint32_t current = m->r32(0x80322dac);
    if (current == a) { uint32_t next = m->r32(current); m->w32(0x80322dac, next); }
END
FN(801B6A5C)
    uint32_t current = m->r32(0x80322db4);
    if (current == a) { uint32_t next = m->r32(current); m->w32(0x80322db4, next); }
END

static uint32_t filtered_next(const TakTarget *m)
{
    for (;;) {
        uint32_t node = m->r32(0x80322dac);
        if (!node) break;
        uint16_t type = m->r16(node+8), wanted = m->r16(0x80322db0);
        if (type == wanted) break;
        uint32_t next = m->r32(node); m->w32(0x80322dac, next);
    }
    /* The original performs a second cursor read before yielding. */
    uint32_t node = m->r32(0x80322dac);
    if (!node) return 0;
    uint32_t value = m->r32(node+4), next = m->r32(node);
    m->w32(0x80322dac, next); return value;
}
FN(801B6A7C)
    uint32_t head = m->r32(0x80322d88);
    m->w16(0x80322db0, (uint16_t)a); m->w32(0x80322dac, head);
    return filtered_next(m);
}
FN(801B6ADC) return filtered_next(m); }
FN(801B72EC)
    uint32_t flags = m->r32(0x80322e00); m->w32(0x80322e00, flags | a);
END
FN(801B7300)
    uint32_t depth = m->r32(0x80322e10), flags = m->r32(0x80322e00);
    m->w32(0x80322e10, depth+1); m->w32(0x80322e04u+depth*4, flags);
END
FN(801B7328)
    uint32_t depth = m->r32(0x80322e10)-1;
    m->w32(0x80322e10, depth);
    uint32_t flags = m->r32(0x80322e04u+depth*4); m->w32(0x80322e00, flags);
END
FN(801B7350)
    uint16_t flags = m->r16(a+2);
    if ((flags & 2u) && m->r8(a+0xa)) return a+0xa;
    return 0;
}
FN(801B8778) return a ? m->r16(a) : 0; }
FN(801B8790) return a ? m->r16(a+2) : 0; }
FN(801B8A9C) m->w8(0x80322ea0, (uint8_t)a); END
FN(801B8B30)
    if (a) { uint8_t flags = m->r8(a+0x10); m->w8(a+0x10, (uint8_t)(flags | 0x40u)); }
END
FN(801B8C64)
    m->w32(0x80322e14, a); m->w32(0x80322e18, a); m->w32(0x80322e1c, b); return 1;
}
FN(801B976C)
    uint16_t flags = m->r16(a+2); m->w16(a+2, (uint16_t)(flags & 0xfffeu));
END
FN(801B977C)
    uint16_t flags = m->r16(a+2); m->w16(a+2, (uint16_t)(flags | 1u));
END
FN(801B99C8)
    uint16_t flags = m->r16(a+2);
    if (flags & 4u) { uint32_t table = m->r32(a+0x78); return m->r32(table+b*4); }
    return b ? 0 : m->r32(a+0x78);
}
FN(801B99FC)
    uint16_t flags = m->r16(a+2); uint32_t value = m->r32(a+0x78);
    if (flags & 4u) { m->w32(b+4, value); m->w32(b, 0); }
    else { m->w32(b, value); m->w32(b+4, 0); }
END
FN(801BA5E0)
    uint8_t byte = m->r8(a+1);
    m->w8(a+1, (uint8_t)((uint8_t)b ? byte | 0x12u : byte & 0xedu));
    uint16_t flags = m->r16(a+2);
    m->w16(a+2, (uint16_t)((uint8_t)b ? flags | 0x1400u : flags & 0xebffu));
END
FN(801BB8E8)
    m->w32(a+4, 0); m->w32(a+0xc, 0); m->w32(a+0x10, 0); m->w32(a+8, 0);
    m->w32(a, 0); m->w8(a+0x2c, 0); m->w32(a+0x14, 0); m->w8(a+0x34, 0); return a;
}
FN(801BCF90)
    uint8_t local = m->r8(a+0x4c), global = m->r8(0x80336058);
    m->w8(a+0x4c, (uint8_t)(local | global));
END
FN(801BD24C)
    uint32_t table = m->r32(a+0xc), record = m->r32(table+b*0x24u);
    uint32_t owner = m->r32(record), index = m->r32(record+4);
    owner = m->r32(owner);
    uint32_t stride = m->r32(owner+0x24), data = m->r32(owner+0x2c);
    return data+index*stride;
}
FN(801BEFE0)
    uint32_t owner = m->r32(a+4), table = m->r32(owner+4); return table+b*0x1cu;
}
FN(801C235C)
    for (uint32_t i = 0; less(i, m->r32(a+4)); ++i) {
        uint32_t table = m->r32(a+0xc), record = m->r32(table+i*0xb0u+0x78);
        m->w32(record+0x40, b);
    }
END
FN(801C275C)
    uint32_t table = m->r32(a+8); m->w32(table+b*4, c);
END
FN(801C3284)
    uint32_t node = m->r32(a+8);
    while (node) { if (m->r32(node) == b) return 1; node = m->r32(node+8); }
    return 0;
}
FN(801C3A88)
    for (uint32_t i = 0; i < c; ++i) {
        if (!m->r32(a+i*4)) { m->w32(a+i*4, b); return 1; }
    }
    return 0;
}
FN(801C3ABC)
    uint32_t table = m->r32(a+4); return m->r32(table+(b & 0xffffu)*4);
}
FN(801C3ACC)
    /* Each extraction keeps only 15 bits. The count spans the original
     * low 16 bits, not all 32 bits of the input word.
     */
    uint32_t count = 0; a &= 0xffffu;
    for (unsigned i = 0; i < 16; ++i) { count += a & 1u; a >>= 1; }
    return count;
}
FN(801C3B54)
    uint32_t old = m->r32(a+4); m->w32(b+8, old); m->w32(a+4, b); m->w32(b+0xc, a);
END
FN(801C3B68)
    uint32_t owner = m->r32(a+0xc), head = m->r32(owner+4);
    if (head == a) { uint32_t next = m->r32(a+8); m->w32(owner+4, next); }
    else {
        uint32_t previous = head;
        for (;;) {
            uint32_t next = m->r32(previous+8);
            if (next == a) break;
            previous = next;
        }
        uint32_t next = m->r32(a+8); m->w32(previous+8, next);
    }
    m->w32(a+0xc, 0);
END
FN(801C3BB8)
    uint32_t node = m->r32(a+4);
    while (node) { if (m->r32(node) == b) return node; node = m->r32(node+8); }
    return 0;
}
FN(801C3EEC) return ((m->r32(a+0x14) >> 30) & 1u) ^ 1u; }
FN(801C4FAC)
    uint8_t type = m->r8(a); uint32_t count = m->r32(a+0x8c), data = m->r32(a+0x90);
    uint32_t address = data+count*8;
    return (type == 0xe || type == 0x13) ? (address+31u) & ~31u : (address+15u) & ~15u;
}
FN(801C5378)
    uint32_t ones = 0, result = 0; int saw_zero = 0;
    for (uint32_t i = 0; i < 32; ++i) {
        if (!(a & 1u)) { if (!saw_zero) { result = ones; saw_zero = 1; } }
        else { ++ones; if (saw_zero) result = i+1; }
        a >>= 1;
    }
    return result;
}
FN(801C63A4)
    uint16_t flags = m->r16(b+2); m->w16(b+2, (uint16_t)(flags & 0xfffeu));
    m->w32(c, a); uint32_t size = m->r32(b+4); m->w32(d, size); return 1;
}
FN(801C8BC4)
    uint32_t node = m->r32(0x80322f9c);
    while (node) { if (m->r16(node+8) == (uint16_t)a) return 1; node = m->r32(node+0x84); }
    return 0;
}
FN(801CACD4)
    m->w32(0x80322fbc, 0); uint32_t node = m->r32(0x80322f9c);
    while (node) {
        uint32_t current = node; node = m->r32(current+0x84);
        uint16_t flags = m->r16(current+2);
        if ((flags & 0x200u) && (flags & b)) {
            uint32_t count = m->r32(0x80322fbc), output = m->r32(0x80322fb8);
            m->w32(0x80322fbc, count+1); m->w32(output+count*4, current);
        }
    }
    return m->r32(0x80322fbc);
}
FN(801CB534) return m->r32(0x80322fc0); }
FN(801CB550) uint32_t pointer = m->r32(0x80322fc0); return pointer ? pointer+0x18 : 0; }
FN(801CB7C4)
    uint32_t count = m->r32(a+4); m->w32(a+4, count+1); return m->r32(a+4)-1;
}
FN(801CBA5C) return 0x80323008; }
FN(801CBB60) m->w8(0x80323024, 0); END
FN(801CC83C)
    m->w8(0x80323025, 0); uint32_t node = m->r32(0x80322fec);
    while (node) {
        uint32_t flags = m->r32(node+4);
        if ((flags & 8u) && (flags & 1u)) { m->w8(0x80323025, 1); return 0; }
        node = m->r32(node);
    }
END
FN(801CD000)
    m->w32(a+4, b); m->w32(a+8, c); m->w32(a+0xc, d); m->w32(a, 0);
    uint32_t value = m->r32(a+4); m->w32(a+0x10, value); m->w8(a+0x14, 1);
END
FN(801CD280)
    uint32_t node = m->r32(a);
    while (node) { if (m->r32(node+4) == b) return node; node = m->r32(node); }
    return 0;
}
FN(801CDB38) m->w8(0x80323201, (uint8_t)a); END
FN(801CE658)
    if (m->r32(0x803231e0) == a) return 0;
    if (m->r32(0x803231e4) == a) return 1;
    if (m->r32(0x803231e8) == a) return 2;
    return 3;
}
FN(801CE720) m->w32(0x803231f8, a); END
FN(801CFEE8)
    uint32_t node = m->r32(0x803231a0);
    while (node) { if (m->r16(node+0xb8) == (uint16_t)a) return 1; node = m->r32(node+0xb4); }
    return 0;
}
FN(801CFF24) m->w32(0x80323248, a); END
FN(801CFF34) m->w32(0x8032324c, a); END
FN(801D8C44) m->w8(0x80323749, (uint8_t)a); END
FN(801D8C60)
    uint32_t entry = 0x803236e0u+a*12;
    m->w8(entry, 1); m->w32(entry+4, b); m->w32(entry+8, c);
END
FN(801D8C84)
    uint32_t entry = 0x803236e0u+a*12;
    m->w8(entry, 0); m->w32(entry+4, 0); m->w32(entry+8, 0);
END
FN(801D8DE4) m->w8(0x80323748, (uint8_t)a); END
FN(801D8F30) return m->r8(0x80323747); }
FN(801D90A4) m->w32(0x80323770, a); END
FN(801D9224) return (m->r32(0x8032374c) >> 7) & 1u; }
FN(801D928C) return m->r32(0x8032375c); }
FN(801D929C) m->w8(0x8032376c, (uint8_t)a); END
FN(801DA394)
    uint32_t node = m->r32(0x80323844);
    if (a == 2) return node;
    while (node) { if (m->r32(node+0x2f8) == a) return node; node = m->r32(node); }
    return 0;
}
FN(801DA3DC)
    uint32_t node = m->r32(a);
    if (b == 2) return node;
    while (node) { if (m->r32(node+0x2f8) == b) return node; node = m->r32(node); }
    return 0;
}
FN(801DA410) uint32_t pointer = m->r32(0x80323868); return pointer ? pointer+0xc : 0; }
FN(801DB0EC)
    uint32_t flags = m->r32(a+0x14);
    m->w32(a+0x14, (uint8_t)b ? flags | 0x10000000u : flags & 0xefffffffu);
END
FN(801DB114)
    uint32_t flags = m->r32(a+0x14);
    m->w32(a+0x14, (uint8_t)b ? flags | 0x80000000u : flags & 0x7fffffffu);
END
FN(801DB5B8)
    uint32_t node = m->r32(0x80323864);
    if (!node) return 0;
    uint32_t next = m->r32(node); m->w32(0x80323864, next); return node+0x98;
}
FN(801DB750) m->w8(0x803238a8, (uint8_t)a); END
FN(801DB8A0) m->w32(0x80323830, 0); END
FN(801DCD90) m->w8(0x80323924, 1); END
FN(801DCDA4) m->w8(0x80323924, 0); END
FN(801DCE50)
    if (!m->r8(0x80323924)) return 0;
    uint32_t node = m->r32(0x80323910);
    while (node) {
        if (m->r32(node+4) == a) m->w32(node+4, b);
        node = m->r32(node);
    }
END
FN(801DEC18)
    uint32_t current = m->r32(0x80323958);
    if (a == current) { m->w32(0x80323958, 0); m->w32(0x8032395c, 0); }
END
static void list_flags(uint32_t wanted, int enabled, const TakTarget *m)
{
    uint32_t node = m->r32(0x80323948);
    while (node) {
        if (m->r16(node+0x12) == (uint16_t)wanted) {
            uint32_t flags = m->r32(node+8);
            m->w32(node+8, enabled ? flags | 0x40u : flags & ~0x40u);
        }
        node = m->r32(node);
    }
}
FN(801DF2C0) list_flags(a, 0, m); END
FN(801DF2FC) list_flags(a, 1, m); END
FN(801E0C2C)
    static const uint8_t offsets[] = {0x3c, 0x40, 0x44, 0x7c, 0x80, 0x84, 0x88, 0x8c, 0x90, 0x94};
    for (unsigned i = 0; i < sizeof(offsets); ++i) m->w32(a+offsets[i], 0);
END
FN(801E1CE8) uint32_t flags = m->r32(a+8); m->w32(a+8, flags | 8u); END
FN(801E4E08) uint32_t slot = m->r32(a+b*4+0xf0); return slot ? m->r32(slot+0x18) : 0; }
FN(801E5530)
    uint32_t location = a+b*4+0xf0, slot = m->r32(location), base = 0, table = 0;
    if (slot) { uint32_t owner = m->r32(slot+0x1c); base = m->r32(owner+0x20); }
    if (slot) { uint32_t owner = m->r32(slot+0x1c); table = m->r32(owner+0x20); }
    uint32_t offset = m->r32(table+c*4); m->w32(slot+0xc, base+offset);
    slot = m->r32(location); m->w32(slot+0x10, 0);
END
FN(801E5878)
    uint32_t owner = m->r32(0x80332fd0), node = m->r32(owner+0x18);
    while (node) {
        uint32_t object = m->r32(node+4), key = m->r32(object+0x13c);
        if (a == key) return object;
        node = m->r32(node+0x18);
    }
    return 0;
}
FN(801E58C0)
    uint32_t found = 0;
    if (m->r32(a+0xf0)) found = 1;
    if (m->r32(a+0xf4)) found = 1;
    if (m->r32(a+0xf8)) found = 1;
    if (m->r32(a+0xfc)) found = 1;
    return found;
}
FN(801E5910)
    uint32_t slot = m->r32(a+b*4+0xf0); if (slot) m->w8(slot+5, (uint8_t)c);
END
FN(801E6228)
    uint32_t slot = m->r32(a+b*4+0xf0); if (slot) m->w8(slot+6, (uint8_t)c);
END
FN(801E6244)
    uint32_t slot = m->r32(a+b*4+0xf0); if (slot) m->w8(slot+7, (uint8_t)c);
END
FN(801E6260)
    uint32_t slot = m->r32(a+b*4+0xf0); return slot ? sign8(m->r8(slot+6)) : 0xffffffff;
}
FN(801E6288)
    uint32_t slot = m->r32(a+b*4+0xf0); return slot ? sign8(m->r8(slot+7)) : 0xffffffff;
}
/* The conditional cursor skip does not guard the routine's later effects. */
static uint32_t skip_slot_word(uint32_t object, uint32_t index, uint32_t cursor,
                               const TakTarget *m)
{
    uint32_t slot = m->r32(object+index*4+0xf0);
    if (slot) {
        uint32_t owner = m->r32(slot+0x1c), flag = m->r32(owner+0x38);
        if (flag) { uint32_t value = m->r32(cursor); m->w32(cursor, value+4); }
    }
    return slot;
}
FN(801E6688)
    (void)skip_slot_word(a, b, c, m);
    uint32_t flags = m->r32(a+0x110); m->w32(a+0x110, flags | 1u); return 0;
}
FN(801E66CC)
    (void)skip_slot_word(a, b, c, m);
    uint32_t flags = m->r32(a+0x110); m->w32(a+0x110, flags & ~1u); return 0;
}
FN(801E6710)
    uint32_t slot = skip_slot_word(a, b, c, m);
    if (slot) { uint8_t count = m->r8(slot+8); m->w8(slot+8, (uint8_t)(count-1)); }
    else { uint32_t value = m->r32(c); m->w32(c, value+4); }
    return 0;
}

#undef FN
#undef END
