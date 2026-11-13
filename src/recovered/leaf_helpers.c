/* GJUE78 rev 0: 70 complete leaf routine models. Target addresses and
 * descriptive operations only; original class names remain unknown.
 * Uniform host harness signature: a..d stand for original r3..r6. For
 * routines classified as void, the harness return value is unspecified.
 * No original ABI compatibility or binary matching is claimed.
 */
#include "runtime_helpers.h"

#define FN(address) uint32_t tak_leaf_##address(uint32_t a, uint32_t b, \
    uint32_t c, uint32_t d, const TakTarget *m) \
    { (void)a; (void)b; (void)c; (void)d; (void)m;
#define END return 0; }

/* Signed comparisons expressed without implementation-defined uint->int casts. */
static int less(uint32_t a, uint32_t b)
{
    return (a ^ 0x80000000u) < (b ^ 0x80000000u);
}
static uint32_t sign16(uint16_t x)
{
    return (x & 0x8000u) ? (uint32_t)x | 0xffff0000u : x;
}

FN(8015C924)
    m->w32(a+0x10, b); m->w32(a+0x14, c); m->w32(a+0x38, d);
END

FN(80160D8C)
    /* Compare signed bytes; equality is equivalent to low-byte equality.
     * The terminator is tested before comparison: searching for NUL fails.
     */
    for (;;) {
        uint8_t value = m->r8(b);
        if (!value) return 0;
        if (value == (uint8_t)a) return 1;
        ++b;
    }
}

FN(80160DC0)
    for (;;) {
        uint8_t value = m->r8(a);
        if (value != ' ' && value != '\t') return a;
        ++a;
    }
}

FN(80162950) return m->r8(a+0x44) ? 0x802eaa6c : 0x80331bdc; }
FN(80162B00) return m->r8(a+0x40) ? 0x80331bfc : 0x80331c04; }
FN(80162B9C) return m->r8(a+0x40) ? 0x80331c0c : 0x80331c14; }
FN(80162C38) return m->r8(a+0x40) ? 0x80331c1c : 0x80331c24; }
FN(8016332C)
    uint32_t owner = m->r32(a+0x28); m->w8(owner+0x11, 1);
END

FN(801633B0)
    uint32_t array = m->r32(a+0x28), index = m->r32(b);
    uint32_t count = m->r32(array+4);
    if (!less(index, count)) return 0;
    m->w32(b, index+1);
    array = m->r32(a+0x28);
    if (less(index, 0)) index = m->r32(array+4)-1;
    else {
        count = m->r32(array+4);
        /* The original's late failure path reads address zero. */
        if (!less(index, count)) return m->r32(0);
    }
    uint32_t table = m->r32(array);
    return m->r32(table+index*4u);
}

FN(80167CCC) m->w32(a+0x10f8, 0); m->w32(a+0x10fc, 0); END
FN(8016BBF8)
    m->w32(a, 0);
    for (uint32_t offset = 8; offset <= 0x24; offset += 4) m->w32(a+offset, 0);
    return a;
}

FN(8017860C)
    uint32_t used = m->r32(a+8), capacity = m->r32(a+4);
    if (!less(used, capacity)) return 0;
    uint32_t table = m->r32(a); m->w32(table+used*8, b);
    used = m->r32(a+8); table = m->r32(a); m->w32(table+used*8+4, c);
    used = m->r32(a+8); m->w32(a+8, used+1);
END

FN(80178A94)
    uint32_t owner = m->r32(a+0x40);
    if (owner && b) {
        uint32_t count = m->r32(owner+0x18);
        if (less(0, count)) {
            for (uint32_t i = 0; i < count; ++i) {
                uint32_t table = m->r32(owner+0x20);
                if (m->r32(table+i*4) == b) return 0;
            }
        }
    }
    return a+0x38;
}

FN(80179B98)
    uint32_t index = m->r32(a+0x58)+1; m->w32(a+0x58, index);
    uint32_t owner = m->r32(a+0x54), count = m->r32(owner+0x18);
    return less(index, count) ? a+0x4c : 0;
}
FN(80179BC4)
    uint32_t owner = m->r32(a+8), index = m->r32(a+0xc);
    uint32_t table = m->r32(owner+0x20); return m->r32(table+index*4);
}
FN(8017A52C) m->w32(c, b); m->w32(c+4, 0); END
FN(8017B30C)
    for (uint32_t i = 0; i < 256; ++i) {
        if (!m->r32(0x802eae88u+i*4)) {
            m->w32(0x802eae88u+i*4, a); return i;
        }
    }
    return 0;
}
FN(8017B358)
    uint32_t entry = 0x802eae88u+(a & 255u)*4;
    if (!m->r32(entry)) return 0;
    m->w32(entry, 0); return 1;
}
FN(8017BDE0) m->w32(a, 0); m->w32(a+4, 0); return a; }
FN(8017DAC0) return m->r32(0x8031a6b0u+a*0x18u+4); }
FN(8017E6F0)
    uint32_t count = m->r32(0x80332cbc), kept = 0;
    if (less(0, count)) {
        for (uint32_t i = 0; i < count; ++i) {
            uint32_t value = m->r32(0x8031a8ecu+i*4);
            if (value != a) {
                if (i != kept) m->w32(0x8031a8ecu+kept*4, value);
                ++kept;
            }
        }
    }
    count = m->r32(0x80332cbc);
    if (kept != count) m->w32(0x80332cbc, kept);
END
FN(801809FC)
    m->w32(a, 0x802eb410); m->w32(a+0x18, 0); m->w32(a+4, 0);
    m->w32(a+8, 0); m->w32(a+0xc, 0); m->w32(a+0x14, 0xffffffff);
    return a;
}
FN(80184564)
    uint32_t flags = m->r32(0x80332cb0); m->w32(0x80332cb0, flags | a);
END
FN(80184574)
    uint32_t flags = m->r32(0x80332cb0); m->w32(0x80332cb0, flags & ~a);
END
FN(8018580C) m->w32(b, (a << 13)+0xc0000u); END
FN(80185C6C)
    static const uint8_t offsets[] = {0x40, 0x38, 0x3c, 0x44, 0x48, 0x4c,
                                    0x50, 0x54, 0x58, 0x5c, 0x60};
    m->w32(a+0x2c, 0);
    for (unsigned i = 0; i < sizeof(offsets); ++i) m->w32(a+offsets[i], 0xffffffff);
    m->w8(a+0x88, 0);
END

/* Fixed-size global tables: no original bounds checks. */
FN(801862C0)
    uint32_t entry = 0x8031a778u+a*12;
    if (!m->r8(entry+8)) m->w32(entry, 1);
END
FN(801862E8) return m->r32(0x8031a778u+a*12+4); }
FN(8018640C) m->w8(0x8031a778u+a*12+8, 1); END
FN(80186428) m->w8(0x8031a778u+a*12+8, 0); END
FN(80186444) return m->r8(0x8031a778u+a*12+8); }
FN(80186664)
    uint32_t third = m->r8(a+2), fourth = m->r8(a+3), second = m->r8(a+1);
    uint32_t first = m->r8(a);
    return first | (second << 8) | (third << 16) | (fourth << 24);
}
FN(80186688)
    m->w8(a, (uint8_t)b); m->w8(a+1, (uint8_t)(b >> 8));
    m->w8(a+2, (uint8_t)(b >> 16)); m->w8(a+3, (uint8_t)(b >> 24));
END
FN(801866AC)
    uint32_t entry = 0x8031a778u+a*12; m->w32(entry+4, b); m->w32(entry, 0);
END
FN(801866CC) m->w32(0x8031a86c, a); m->w32(0x8031a868, 0); END
FN(80186B20)
    uint32_t entry = 0x8031a900u+a*0x54+b*12;
    if (!m->r8(entry+8)) m->w32(entry+4, 1);
END
FN(80186CC8) return m->r32(0x8031a900u+a*0x54+b*12); }
FN(80186D28) m->w8(0x8031a900u+a*0x54+b*12+8, 1); END
FN(80186D4C)
    uint32_t count = m->r32(0x80332cc8);
    if (less(0, count))
        for (uint32_t i = 0; i < count; ++i)
            for (uint32_t j = 0; j < 7; ++j) m->w8(0x8031a908u+i*0x54+j*12, 0);
END

FN(80188564) m->w32(0x802eb6d4, 0x12345678); END
FN(801885CC) m->w8(0x802eb69c, (uint8_t)a); END
static void copy_four(uint32_t source, uint32_t dest, const TakTarget *m)
{
    uint8_t first = m->r8(source), second = m->r8(source+1);
    uint8_t third = m->r8(source+2), fourth = m->r8(source+3);
    m->w8(dest, first); m->w8(dest+1, second); m->w8(dest+2, third); m->w8(dest+3, fourth);
}
FN(801885DC) copy_four(a, 0x802eb69d, m); END
FN(80188608) m->w32(0x802eb6a4, a); END
FN(80188628) copy_four(a, 0x802eb6ac, m); END
FN(80188654) m->w32(0x802eb6b0, (uint8_t)a ? 3 : 2); END
FN(80188834) m->w32(0x80332d14, a); m->w32(0x80332d00, 1); END
FN(8018B424)
    if ((uint8_t)b) {
        uint8_t value = m->r8(a+0x262); m->w8(a+0x24c, value);
        value = m->r8(a+0x263); m->w8(a+0x24d, value);
    } else { m->w8(a+0x24c, 0); m->w8(a+0x24d, 0); }
END
FN(8018B450) m->w32(a+0x25c, (uint8_t)b ? 3 : 2); END
FN(8018B558) m->w32(a+0x80, b); m->w32(a+0x84, c); m->w8(a+0x7c, 0); END
FN(8018C40C) return m->r8(0x8031b09a); }
FN(8018C41C) m->w8(0x8031b09a, (uint8_t)a); END
FN(8018C4F8) return m->r32(0x8031b154); }
FN(8018C510)
    uint32_t table = m->r32(a+0x2c); return m->r16(table+b*2);
}
FN(8018C8A4)
    uint32_t pointer = m->r32(0x8031b154), value = m->r32(0x8031b0c8);
    m->w32(0x8031b0d0, pointer); m->w32(0x8031b0cc, value);
END
FN(8018CC3C)
    uint32_t item = a+6, i = 0;
    while (less(i, m->r8(a+4))) {
        uint16_t value;
        if (m->r8(item+7) & 16u) value = m->r16(0x8031b094);
        else {
            uint32_t owner = m->r32(0x8031b154);
            uint32_t index = sign16(m->r16(item));
            uint32_t table = m->r32(owner+0x2c);
            value = m->r16(table+index*2);
        }
        m->w16(item, value); ++i; item += 0x28;
    }
END
FN(8018CC98) return m->r16(0x8031b094); }
FN(8018CE48) return m->r16(0x8031b0c0); }
FN(8018CE58) return m->r16(0x8031b0be); }
FN(8018CE78) return m->r16(0x8031b0c2); }
FN(8018CE88) return m->r16(0x8031b0c4); }
FN(8018CE98) m->w16(0x8031b0c2, 0); END
FN(8018CEAC) m->w16(0x8031b0c0, (uint16_t)a); END
FN(8018CEBC) m->w16(0x8031b0c4, 1); m->w16(0x8031b0be, (uint16_t)a); END
FN(8018D6BC)
    uint32_t node = m->r32(0x8031b160);
    while (node) {
        uint16_t flags = m->r16(node+0xe);
        m->w16(node+0xe, (uint16_t)((uint8_t)a ? flags | 2u : flags & 0xfffdu));
        node = m->r32(node);
    }
END
FN(8018DE8C)
    uint32_t owner = m->r32(b+0x94); m->w8(owner+0x20, 0);
END
FN(8018F74C)
    uint32_t array = m->r32(a);
    if (less(b, 0)) b = m->r32(array+4)-1;
    /* The original out-of-range path still executes a final load at zero. */
    else if (!less(b, m->r32(array+4))) return m->r32(0);
    uint32_t table = m->r32(array); return m->r32(table+b*4);
}
FN(80195AF4)
    uint32_t node = m->r32(a+4);
    while (node) {
        if (m->r32(node+0x40) == b) return node;
        node = m->r32(node+0x398);
    }
    return 0;
}
FN(8019D194)
    uint32_t stride = m->r32(a+0x94), table = m->r32(a+0x90);
    return table+(b+c*stride)*0xe0u;
}
FN(801A0C10)
    uint32_t stride = m->r32(a+0xc), table = m->r32(a+4);
    return table+(c+b*stride)*2;
}
FN(801AE384)
    if (!b) return 0;
    if (!m->r32(a)) {
        m->w32(a+4, b); m->w32(a, b); m->w32(b+8, 0); m->w32(b+4, 0);
    } else {
        m->w32(b+8, 0);
        uint32_t tail = m->r32(a+4); m->w32(b+4, tail);
        tail = m->r32(a+4); m->w32(tail+8, b); m->w32(a+4, b);
    }
    uint32_t count = m->r32(a+0xc); m->w32(a+0xc, count+1); return 1;
}

#undef FN
#undef END
