/* Generated from analysis/scalar-helper-specs.json. See SCALAR_HELPERS.md.
 * Complete straight-line semantic models for GJUE78 rev 0.
 * a..d represent original r3..r6. The harness returns final r3;
 * this does not infer original return types or establish ABI matching.
 * No instruction bytes, assembly, or CPU interpreter are embedded here.
 */
#include "runtime_helpers.h"

static uint32_t leading_zeros(uint32_t value)
{
    return value ? (uint32_t)__builtin_clz(value) : 32u;
}

static uint32_t sign_byte(uint32_t value)
{
    value &= 255u;
    return (value & 128u) ? value | UINT32_C(0xffffff00) : value;
}

static uint32_t shift_signed(uint32_t value, unsigned amount)
{
    if (!amount) return value;
    uint32_t fill = (value & UINT32_C(0x80000000)) ? ~(UINT32_MAX >> amount) : 0;
    return (value >> amount) | fill;
}

/* 1 target read, scalar result; 20 original bytes. */
uint32_t tak_scalar_80005B10(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x78)));
    (void)value_0;
    return (((UINT32_C(0x0) - value_0) | value_0) >> 31);
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80008D6C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x8)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 6 target stores; 52 original bytes. */
uint32_t tak_scalar_80008DE4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x20)), (a + UINT32_C(0xa4)));
    m->w32((a + UINT32_C(0x10)), (a + UINT32_C(0xb8)));
    m->w32((a + UINT32_C(0x14)), (a + UINT32_C(0xcc)));
    m->w32((a + UINT32_C(0xa0)), (a + UINT32_C(0xe0)));
    m->w32((a + UINT32_C(0x30)), (a + UINT32_C(0xf4)));
    m->w32((a + UINT32_C(0x34)), (a + UINT32_C(0x108)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800090DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x11c)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 3 target stores; 20 original bytes. */
uint32_t tak_scalar_800174CC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x170)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x174)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x178)), UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80017A44(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x20)), UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8001C8D0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0xc0)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8001EC44(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x14c)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8001EF60(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xbc)));
    return a;
}

/* 4 target reads, 2 target stores; 28 original bytes. */
uint32_t tak_scalar_8001F158(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0x10a)));
    (void)value_0;
    uint32_t value_1 = m->r32((a + UINT32_C(0x4)));
    (void)value_1;
    m->w8((value_1 + UINT32_C(0x4088)), (uint8_t)value_0);
    uint32_t value_2 = m->r8((a + UINT32_C(0x109)));
    (void)value_2;
    uint32_t value_3 = m->r32((a + UINT32_C(0x4)));
    (void)value_3;
    m->w8((value_3 + UINT32_C(0x4087)), (uint8_t)value_2);
    return value_3;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8001F518(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x10c)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8001F5C4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x10c)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 5 target stores; 44 original bytes. */
uint32_t tak_scalar_8001FF28(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x18)), (a + UINT32_C(0xbc)));
    m->w32((a + UINT32_C(0x20)), (a + UINT32_C(0x15c)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xa0)));
    m->w32((a + UINT32_C(0x48)), (a + UINT32_C(0x1ac)));
    m->w32((a + UINT32_C(0x38)), (a + UINT32_C(0x1c0)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80024330(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x350)), (a + UINT32_C(0x354)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80024638(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x350)), (a + UINT32_C(0xb64)));
    return a;
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8002AA04(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x1048)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0x1044)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8002C668(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x1268)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8002DA08(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x0));
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    return value_0;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8002DE80(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r8(b);
    (void)value_0;
    m->w8((a + UINT32_C(0x18)), (uint8_t)value_0);
    return a;
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8002E958(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x18)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xbc)));
    return a;
}

/* 8 target stores; 52 original bytes. */
uint32_t tak_scalar_8003041C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0xe8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), (a + UINT32_C(0xbc)));
    m->w32((a + UINT32_C(0x8)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x20)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x18)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x58)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x28)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xa0)));
    return a;
}

/* 3 target reads, scalar result; 16 original bytes. */
uint32_t tak_scalar_800310A8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x4)));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x40dc)));
    (void)value_1;
    uint32_t value_2 = m->r32((value_1 + UINT32_C(0x94)));
    (void)value_2;
    return value_2;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_80031174(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xe8)));
    (void)value_0;
    m->w32((a + UINT32_C(0xe8)), (value_0 | UINT32_C(0x1)));
    return a;
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_800339FC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0xc)), (a + UINT32_C(0xbc)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xd0)));
    return a;
}

/* 2 target reads, scalar result; 24 original bytes. */
uint32_t tak_scalar_80033A10(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x4)));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x3c40)));
    (void)value_1;
    return (((UINT32_C(0x0) - value_1) | value_1) >> 31);
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_80035DF4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0xe8)));
    (void)value_0;
    m->w8((a + UINT32_C(0xe8)), (uint8_t)(value_0 & UINT32_C(0xffffff7f)));
    return a;
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_80035E08(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0xe8)));
    (void)value_0;
    m->w8((a + UINT32_C(0xe8)), (uint8_t)((value_0 & UINT32_C(0xffffff7f)) | UINT32_C(0x80)));
    return a;
}

/* 3 target stores; 28 original bytes. */
uint32_t tak_scalar_80035E1C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x18)), (a + UINT32_C(0xbc)));
    m->w32((a + UINT32_C(0x1c)), (a + UINT32_C(0xd0)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0xa0)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80036500(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x8)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_80036ADC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    m->w32((a + UINT32_C(0xc)), (value_0 | UINT32_C(0x2)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80038F3C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x180)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80038F48(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x180)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8003A5DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x9c)));
    (void)value_0;
    m->w8((value_0 + UINT32_C(0x5ab)), (uint8_t)UINT32_C(0x1));
    return value_0;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8003D640(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r32(b);
    (void)value_0;
    m->w32((a + UINT32_C(0x18)), value_0);
    return a;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8003D718(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r8(b);
    (void)value_0;
    m->w8((a + UINT32_C(0x18)), (uint8_t)value_0);
    return a;
}

/* 7 target stores; 60 original bytes. */
uint32_t tak_scalar_8003EA60(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x18)), (a + UINT32_C(0xa0)));
    m->w32((a + UINT32_C(0x20)), (a + UINT32_C(0xb4)));
    m->w32((a + UINT32_C(0x8)), (a + UINT32_C(0xc8)));
    m->w32((a + UINT32_C(0x10)), (a + UINT32_C(0xdc)));
    m->w32((a + UINT32_C(0x28)), (a + UINT32_C(0xf0)));
    m->w32((a + UINT32_C(0x2c)), (a + UINT32_C(0x104)));
    m->w32((a + UINT32_C(0x98)), (a + UINT32_C(0x118)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80040A50(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x394)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_80040B9C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r32(b);
    (void)value_0;
    m->w32((a + UINT32_C(0x18)), value_0);
    return a;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_80040C08(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r32(b);
    (void)value_0;
    m->w32((a + UINT32_C(0x18)), value_0);
    return a;
}

/* 4 target stores; 36 original bytes. */
uint32_t tak_scalar_8004156C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x170)), (a + UINT32_C(0x8)));
    m->w32((a + UINT32_C(0x16c)), (a + UINT32_C(0x1c)));
    m->w32((a + UINT32_C(0x174)), (a + UINT32_C(0x30)));
    m->w32((a + UINT32_C(0x1f4)), (a + UINT32_C(0x44)));
    return a;
}

/* 1 target read, scalar result; 20 original bytes. */
uint32_t tak_scalar_800440E0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    return (((UINT32_C(0x0) - value_0) | value_0) >> 31);
}

/* 2 target reads, 1 target store; 24 original bytes. */
uint32_t tak_scalar_80044528(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    uint32_t value_1 = m->r32((a + UINT32_C(0x4)));
    (void)value_1;
    m->w32((value_1 + UINT32_C(0x2c)), value_0);
    return (a + UINT32_C(0x58));
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_800452DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x1c)), (a + UINT32_C(0xa0)));
    m->w32((a + UINT32_C(0x9c)), (a + UINT32_C(0xb4)));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800454B0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0xc8)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80045980(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0xe4)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8004778C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x2ec)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 6 target stores; 56 original bytes. */
uint32_t tak_scalar_80047A98(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802add18));
    m->w32((a + UINT32_C(0x4)), b);
    m->w32(a, UINT32_C(0x802b29e0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x802ade60));
    m->w32((a + UINT32_C(0x10)), b);
    m->w8((a + UINT32_C(0x8)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 10 target stores; 48 original bytes. */
uint32_t tak_scalar_8004C538(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4074)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x4075)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x4076)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x4077)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x4078)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x4079)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x407a)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x407b)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x407c)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x407d)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 2 target reads, scalar result; 12 original bytes. */
uint32_t tak_scalar_8004F108(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x2dc)));
    (void)value_0;
    uint32_t value_1 = m->r32(value_0);
    (void)value_1;
    return value_1;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8004F144(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x3c28)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8004FAD0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x20c)));
    (void)value_0;
    m->w32((a + UINT32_C(0x20c)), (value_0 & UINT32_C(0xfffffffe)));
    return a;
}

/* 1 target read, 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8005344C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x1));
    uint32_t value_0 = m->r32(b);
    (void)value_0;
    m->w32((a + UINT32_C(0x18)), value_0);
    return a;
}

/* 5 target stores; 28 original bytes. */
uint32_t tak_scalar_8005357C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0x8)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0x9)), (uint8_t)UINT32_C(0x0));
    m->w8((a + UINT32_C(0xa)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80058C34(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x262)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80058D50(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x262)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80058D5C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x262)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 2 target reads, scalar result; 28 original bytes. */
uint32_t tak_scalar_8005A2F4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    uint32_t value_1 = m->r32((a + UINT32_C(0x4)));
    (void)value_1;
    return (value_1 + ((c + (b * value_0)) * UINT32_C(0x28)));
}

/* 9 target stores; 60 original bytes. */
uint32_t tak_scalar_8005A598(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802b3e50));
    m->w32(a, UINT32_C(0x802b3e70));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x14)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x18)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0x1c)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8005C1FC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x5d)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_80061E40(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x14)));
    (void)value_0;
    m->w32((a + UINT32_C(0x14)), (value_0 | b));
    return a;
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_80067C60(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((b + UINT32_C(0x28)));
    (void)value_0;
    uint32_t value_1 = m->r32((b + UINT32_C(0x2c)));
    (void)value_1;
    m->w32(a, value_0);
    m->w32((a + UINT32_C(0x4)), value_1);
    uint32_t value_2 = m->r32((b + UINT32_C(0x30)));
    (void)value_2;
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_80067C7C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((b + UINT32_C(0x1c)));
    (void)value_0;
    uint32_t value_1 = m->r32((b + UINT32_C(0x20)));
    (void)value_1;
    m->w32(a, value_0);
    m->w32((a + UINT32_C(0x4)), value_1);
    uint32_t value_2 = m->r32((b + UINT32_C(0x24)));
    (void)value_2;
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 3 target stores; 32 original bytes. */
uint32_t tak_scalar_80071A9C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802b7c60));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0xffffffff));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    return a;
}

/* 2 target reads, scalar result; 16 original bytes. */
uint32_t tak_scalar_80071FC4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x30)));
    (void)value_0;
    uint32_t value_1 = m->r16((value_0 + UINT32_C(0x2)));
    (void)value_1;
    return (value_1 & UINT32_C(0x1));
}

/* 4 target reads, scalar result; 24 original bytes. */
uint32_t tak_scalar_80073DF8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(b);
    (void)value_0;
    uint32_t value_1 = m->r32(a);
    (void)value_1;
    uint32_t value_2 = m->r32((value_0 + UINT32_C(0x4)));
    (void)value_2;
    uint32_t value_3 = m->r32((value_1 + UINT32_C(0x4)));
    (void)value_3;
    return (value_3 - value_2);
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8007BE04(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x2c)));
    (void)value_0;
    m->w32((a + UINT32_C(0x2c)), (value_0 & UINT32_C(0xffff7fff)));
    return a;
}

/* 3 target reads, scalar result; 32 original bytes. */
uint32_t tak_scalar_8007BE2C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x4)));
    (void)value_0;
    uint32_t value_1 = m->r32((b + UINT32_C(0x4)));
    (void)value_1;
    uint32_t value_2 = m->r32(b);
    (void)value_2;
    return (leading_zeros(((value_0 & value_1) - value_2)) >> 5);
}

/* 3 target reads, scalar result; 32 original bytes. */
uint32_t tak_scalar_8007BE4C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    uint32_t value_1 = m->r32((b + UINT32_C(0x4)));
    (void)value_1;
    uint32_t value_2 = m->r32(b);
    (void)value_2;
    return (leading_zeros(((value_0 & value_1) - value_2)) >> 5);
}

/* 2 target stores; 28 original bytes. */
uint32_t tak_scalar_8007C89C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x1a0)), (uint8_t)b);
    m->w32((a + UINT32_C(0x28)), (((UINT32_C(0x0) - (b & UINT32_C(0xff))) | (b & UINT32_C(0xff))) >> 31));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8007D788(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800835A0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x624)), UINT32_C(0x2));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800835AC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x624)), UINT32_C(0x8));
    return a;
}

/* 3 target reads, 1 target store; 24 original bytes. */
uint32_t tak_scalar_80096894(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x8033267c));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x51dc)));
    (void)value_1;
    uint32_t value_2 = m->r32((value_1 + UINT32_C(0x2c)));
    (void)value_2;
    m->w32((value_1 + UINT32_C(0x2c)), (value_2 | UINT32_C(0x20000)));
    return value_1;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800C8744(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x24c)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800CDBD4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x24c)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 12 original bytes. */
uint32_t tak_scalar_800CF7EC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x8)));
    (void)value_0;
    m->w32((a + UINT32_C(0x198)), value_0);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_800D41A0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(b, UINT32_C(0x0));
    return UINT32_C(0x0);
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_800D4CD8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + UINT32_C(0x40000)) + UINT32_C(0x4f20)), UINT32_C(0x0));
    return (a + UINT32_C(0x40000));
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_800D4CE8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + UINT32_C(0x40000)) + UINT32_C(0x4f20)));
    (void)value_0;
    return value_0;
}

/* 2 target reads, 1 target store; 16 original bytes. */
uint32_t tak_scalar_800D56B4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x8033267c));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x51e0)));
    (void)value_1;
    m->w32((value_1 + UINT32_C(0x44)), b);
    return value_1;
}

/* 3 target reads, scalar result; 16 original bytes. */
uint32_t tak_scalar_800D56C4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x8033267c));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x51e0)));
    (void)value_1;
    uint32_t value_2 = m->r32((value_1 + UINT32_C(0x44)));
    (void)value_2;
    return value_2;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_800D80DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(c, UINT32_C(0x0));
    return UINT32_C(0x0);
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_800DAC50(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(c, UINT32_C(0x0));
    m->w32(d, UINT32_C(0x0));
    return UINT32_C(0x0);
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800DF750(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffffa780)), b);
    return (a + UINT32_C(0x10000));
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_800DF75C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + UINT32_C(0x10000)) + UINT32_C(0xffffa780)));
    (void)value_0;
    return value_0;
}

/* 1 target read, scalar result; 16 original bytes. */
uint32_t tak_scalar_800E5540(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x80331508));
    (void)value_0;
    return (value_0 + (a * UINT32_C(0xe8)));
}

/* 1 target read, scalar result; 32 original bytes. */
uint32_t tak_scalar_800E6E28(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x8)));
    (void)value_0;
    return (((value_0 << 6) + UINT32_C(0x4)) + (((((value_0 << 6) + UINT32_C(0x4)) ^ UINT32_C(0xf)) + UINT32_C(0x1)) & UINT32_C(0xf)));
}

/* 1 target store; 20 original bytes. */
uint32_t tak_scalar_800E726C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802fc698), UINT32_C(0x0));
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_800F6344(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffff974c)), UINT32_C(0x0));
    return (a + UINT32_C(0x10000));
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_800F64B0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + UINT32_C(0x10000)) + UINT32_C(0xffff959c)));
    (void)value_0;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffff959c)), (value_0 - UINT32_C(0x1)));
    return value_0;
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_800F64C4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + UINT32_C(0x10000)) + UINT32_C(0xffff959c)));
    (void)value_0;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffff959c)), (value_0 + UINT32_C(0x1)));
    return value_0;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_800F9FFC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x4a)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target read, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_8010A1B8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x1b4)));
    (void)value_0;
    m->w32((value_0 + UINT32_C(0x20)), UINT32_C(0x5));
    m->w8((a + UINT32_C(0x3260)), (uint8_t)UINT32_C(0x1));
    m->w8((a + UINT32_C(0x28)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* scalar result; 20 original bytes. */
uint32_t tak_scalar_8010A6DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    return (a + ((b * UINT32_C(0x38)) + UINT32_C(0x23e8)));
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_8010A6F0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(c);
    (void)value_0;
    uint32_t value_1 = m->r32((c + UINT32_C(0x4)));
    (void)value_1;
    m->w32(a, value_0);
    uint32_t value_2 = m->r32((c + UINT32_C(0x8)));
    (void)value_2;
    m->w32((a + UINT32_C(0x4)), value_1);
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_8010A70C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(c);
    (void)value_0;
    uint32_t value_1 = m->r32((c + UINT32_C(0x4)));
    (void)value_1;
    m->w32(a, value_0);
    uint32_t value_2 = m->r32((c + UINT32_C(0x8)));
    (void)value_2;
    m->w32((a + UINT32_C(0x4)), value_1);
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_8010A75C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(c);
    (void)value_0;
    uint32_t value_1 = m->r32((c + UINT32_C(0x4)));
    (void)value_1;
    m->w32(a, value_0);
    uint32_t value_2 = m->r32((c + UINT32_C(0x8)));
    (void)value_2;
    m->w32((a + UINT32_C(0x4)), value_1);
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 3 target reads, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_8010A778(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(c);
    (void)value_0;
    uint32_t value_1 = m->r32((c + UINT32_C(0x4)));
    (void)value_1;
    m->w32(a, value_0);
    uint32_t value_2 = m->r32((c + UINT32_C(0x8)));
    (void)value_2;
    m->w32((a + UINT32_C(0x4)), value_1);
    m->w32((a + UINT32_C(0x8)), value_2);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801636B8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x80332c78), UINT32_C(0x0));
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_8017BDF0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, b);
    m->w32((a + UINT32_C(0x4)), c);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80185960(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 44 original bytes. */
uint32_t tak_scalar_8018D690(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((UINT32_C(0x8031b090) + (a << 2)) + UINT32_C(0x98)));
    (void)value_0;
    m->w8((value_0 + (((b & UINT32_C(0x7fff)) * UINT32_C(0x18)) + UINT32_C(0x14))), (uint8_t)UINT32_C(0x1));
    return value_0;
}

/* 1 target read, 13 target stores; 64 original bytes. */
uint32_t tak_scalar_801956F4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x80335c40));
    (void)value_0;
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0xc)), (uint8_t)UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x18)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x14)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0x1c)), (uint8_t)UINT32_C(0x0));
    m->w32((a + UINT32_C(0x20)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x28)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x24)), UINT32_C(0x0));
    m->w8((a + UINT32_C(0x2c)), (uint8_t)UINT32_C(0x0));
    m->w32((a + UINT32_C(0x30)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x34)), value_0);
    return a;
}

/* 4 target stores; 24 original bytes. */
uint32_t tak_scalar_80199830(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x1c)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x30)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x24)), UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801A7F74(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801B5980(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x804)), UINT32_C(0x0));
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_801C3BE0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x80332e2c), b);
    m->w32(UINT32_C(0x80332e30), c);
    return a;
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_801C3BEC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x14)));
    (void)value_0;
    return (value_0 & UINT32_C(0x3));
}

/* 1 target read, 1 target store; 12 original bytes. */
uint32_t tak_scalar_801CB7AC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    m->w32((a + UINT32_C(0x4)), value_0);
    return a;
}

/* 1 target read, 1 target store; 12 original bytes. */
uint32_t tak_scalar_801CB7B8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x4)));
    (void)value_0;
    m->w32(a, value_0);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801CCFF4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x14)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801D8C54(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x80323728), a);
    return a;
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_801DB0E0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x14)));
    (void)value_0;
    return (((value_0 << 4) | (value_0 >> 28)) & UINT32_C(0x1));
}

/* 1 target read, scalar result; 16 original bytes. */
uint32_t tak_scalar_801EAD84(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x28)));
    (void)value_0;
    return (value_0 + (b << 2));
}

/* 7 target reads, 2 target stores; 76 original bytes. */
uint32_t tak_scalar_801EAEF8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + (b << 2)) + UINT32_C(0xf0)));
    (void)value_0;
    uint32_t value_1 = m->r8((value_0 + UINT32_C(0x8)));
    (void)value_1;
    uint32_t value_2 = m->r32((value_0 + UINT32_C(0x34)));
    (void)value_2;
    uint32_t value_3 = m->r8((value_2 + sign_byte(value_1)));
    (void)value_3;
    m->w8(c, (uint8_t)(leading_zeros((UINT32_C(0x4) - value_3)) >> 5));
    uint32_t value_4 = m->r8((value_0 + UINT32_C(0x8)));
    (void)value_4;
    uint32_t value_5 = m->r32((value_0 + UINT32_C(0x30)));
    (void)value_5;
    m->w8((value_0 + UINT32_C(0x8)), (uint8_t)(value_4 - UINT32_C(0x1)));
    uint32_t value_6 = m->r32((value_5 + (sign_byte(value_4) << 2)));
    (void)value_6;
    return value_6;
}

/* scalar result; 36 original bytes. */
uint32_t tak_scalar_801EE758(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    return (((a & UINT32_C(0x1c03)) | ((a & UINT32_C(0xcc)) << 2)) | ((a & UINT32_C(0x330)) >> 2));
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801EED30(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w16(a, (uint16_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_801EFF9C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + (b << 2)) + UINT32_C(0x16c)));
    (void)value_0;
    m->w32((a + UINT32_C(0x168)), value_0);
    return a;
}

/* 1 target store; 20 original bytes. */
uint32_t tak_scalar_801EFFE4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + (b << 2)) + UINT32_C(0x16c)), UINT32_C(0x0));
    return (a + (b << 2));
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801F30A8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc60), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F30B4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc64), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F30C4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc74), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F30D4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc78), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F30E4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc7c), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F30F4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc88), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3104(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc8c), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3114(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc90), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3124(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc94), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3134(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecca8), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3144(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802eccac), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3154(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802eccb0), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3164(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc98), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3174(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecc9c), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3184(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecca0), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_801F3194(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802ecca4), a);
    return a;
}

/* 2 target reads, 4 target stores; 48 original bytes. */
uint32_t tak_scalar_801F87D0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(UINT32_C(0x80331fc0));
    (void)value_0;
    m->w32(a, value_0);
    uint32_t value_1 = m->r32(UINT32_C(0x80331fc4));
    (void)value_1;
    m->w32(b, value_1);
    m->w32(c, UINT32_C(0x802ecf88));
    m->w32(d, UINT32_C(0x802edf88));
    return UINT32_C(0x0);
}

/* 8 target stores; 48 original bytes. */
uint32_t tak_scalar_801FB9E8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), b);
    m->w32((a + UINT32_C(0x18)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x1c)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x20));
    m->w32((a + UINT32_C(0x14)), UINT32_C(0xffffffff));
    m->w32((a + UINT32_C(0xa0)), c);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801FE118(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target read, 2 target stores; 16 original bytes. */
uint32_t tak_scalar_801FE258(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    m->w32((b + UINT32_C(0x20)), value_0);
    m->w32(a, b);
    return a;
}

/* 4 target stores; 40 original bytes. */
uint32_t tak_scalar_801FE96C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ee364));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32(a, UINT32_C(0x802ee350));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    return a;
}

/* 1 target read, 3 target stores; 20 original bytes. */
uint32_t tak_scalar_801FF4D4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((b + UINT32_C(0x4)), a);
    uint32_t value_0 = m->r32((a + UINT32_C(0x8)));
    (void)value_0;
    m->w32((b + UINT32_C(0x8)), value_0);
    m->w32((a + UINT32_C(0x8)), b);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_801FF640(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target read, 3 target stores; 28 original bytes. */
uint32_t tak_scalar_801FF930(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, b);
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    m->w32((a + UINT32_C(0x4)), (value_0 + UINT32_C(0x1c)));
    m->w8((a + UINT32_C(0x34)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 4 target stores; 24 original bytes. */
uint32_t tak_scalar_80203198(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), b);
    m->w32((a + UINT32_C(0xc)), c);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_802045FC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802eea10), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_80204608(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802eea14), a);
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_80204618(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x802eea28), a);
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80204900(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_80205A88(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(UINT32_C(0x80332f18), UINT32_C(0x0));
    uint32_t value_0 = m->r32((a + UINT32_C(0x8)));
    (void)value_0;
    return value_0;
}

/* 1 target read, 1 target store; 24 original bytes. */
uint32_t tak_scalar_80205DC4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((UINT32_C(0x802eecd8) + (a << 2)));
    (void)value_0;
    m->w32(UINT32_C(0x80332f2c), value_0);
    return UINT32_C(0x802eecd8);
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_80205DDC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((UINT32_C(0x80332078) + (a << 2)));
    (void)value_0;
    m->w32(UINT32_C(0x80332f30), value_0);
    return UINT32_C(0x80332078);
}

/* 2 target reads, 6 target stores; 44 original bytes. */
uint32_t tak_scalar_802067C0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x4)));
    (void)value_0;
    uint32_t value_1 = m->r32(value_0);
    (void)value_1;
    m->w32((a + UINT32_C(0x4)), value_1);
    m->w32(value_0, UINT32_C(0x0));
    m->w32((value_0 + UINT32_C(0x4)), b);
    m->w32((value_0 + UINT32_C(0xc)), c);
    m->w16((value_0 + UINT32_C(0x8)), (uint16_t)d);
    m->w16((value_0 + UINT32_C(0xa)), (uint16_t)UINT32_C(0x0));
    return value_0;
}

/* scalar result; 20 original bytes. */
uint32_t tak_scalar_80206C60(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    return ((b + ((a + UINT32_C(0x7)) & UINT32_C(0xfffffff8))) - UINT32_C(0x8));
}

/* 1 target read, 2 target stores; 16 original bytes. */
uint32_t tak_scalar_80206F18(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    m->w32(b, value_0);
    m->w32(a, b);
    return a;
}

/* 3 target stores; 20 original bytes. */
uint32_t tak_scalar_802075D8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x0));
    m->w32((a + UINT32_C(0x4)), b);
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    return a;
}

/* 2 target reads, scalar result; 28 original bytes. */
uint32_t tak_scalar_80209038(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8(UINT32_C(0x80332f78));
    (void)value_0;
    uint32_t value_1 = m->r32(UINT32_C(0x80332f74));
    (void)value_1;
    return (value_1 & shift_signed(((UINT32_C(0x0) - value_0) | value_0), 31));
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_8020BD38(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x10)));
    (void)value_0;
    return (((value_0 << 31) | (value_0 >> 1)) & UINT32_C(0x1));
}

/* scalar result; 12 original bytes. */
uint32_t tak_scalar_80210158(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    return ((b + UINT32_C(0x1fff)) >> 13);
}

/* 3 target stores; 32 original bytes. */
uint32_t tak_scalar_80211554(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ef248));
    m->w32((a + UINT32_C(0x4)), b);
    m->w32(a, UINT32_C(0x802ef238));
    return a;
}

/* 7 target stores; 52 original bytes. */
uint32_t tak_scalar_80211CEC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ef2bc));
    m->w32(a, UINT32_C(0x802ef2a0));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x14)), UINT32_C(0x0));
    return a;
}

/* 3 target stores; 36 original bytes. */
uint32_t tak_scalar_80213850(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ef360));
    m->w8((a + UINT32_C(0x4)), (uint8_t)UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0xbadbad));
    return a;
}

/* 2 target stores; 20 original bytes. */
uint32_t tak_scalar_8021387C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(b, UINT32_C(0x0));
    m->w32(c, UINT32_C(0x0));
    return UINT32_C(0x0);
}

/* 4 target reads, scalar result; 20 original bytes. */
uint32_t tak_scalar_80214A48(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x10)));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + UINT32_C(0x34)));
    (void)value_1;
    uint32_t value_2 = m->r32((value_1 + UINT32_C(0xd8)));
    (void)value_2;
    uint32_t value_3 = m->r8((value_2 + UINT32_C(0xc8)));
    (void)value_3;
    return value_3;
}

/* 3 target stores; 28 original bytes. */
uint32_t tak_scalar_80217834(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ef748));
    m->w32((a + UINT32_C(0x8)), b);
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    return a;
}

/* 5 target stores; 36 original bytes. */
uint32_t tak_scalar_80218110(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ef7d8));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    return a;
}

/* 2 target reads, scalar result; 28 original bytes. */
uint32_t tak_scalar_80220FDC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    uint32_t value_1 = m->r32(b);
    (void)value_1;
    return (((UINT32_C(0x0) - (value_0 & value_1)) | (value_0 & value_1)) >> 31);
}

/* 1 target read, scalar result; 16 original bytes. */
uint32_t tak_scalar_80221008(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    return (((leading_zeros(value_0) << 27) | (leading_zeros(value_0) >> 5)) & UINT32_C(0xff));
}

/* 2 target reads, scalar result; 16 original bytes. */
uint32_t tak_scalar_80229D3C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x198)));
    (void)value_0;
    uint32_t value_1 = m->r32((value_0 + (b << 2)));
    (void)value_1;
    return value_1;
}

/* 1 target read, scalar result; 16 original bytes. */
uint32_t tak_scalar_80229D4C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x19c)));
    (void)value_0;
    return (value_0 + (b * UINT32_C(0xc)));
}

/* 6 target stores; 52 original bytes. */
uint32_t tak_scalar_8022EEE0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802ee364));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32(a, UINT32_C(0x802efdcc));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x7));
    return a;
}

/* 2 target reads, scalar result; 28 original bytes. */
uint32_t tak_scalar_8023503C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc)));
    (void)value_0;
    uint32_t value_1 = m->r32((a + UINT32_C(0x4)));
    (void)value_1;
    return (value_1 + ((c + (b * value_0)) * UINT32_C(0xc)));
}

/* 4 target reads, 1 target store; 36 original bytes. */
uint32_t tak_scalar_80239760(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc8)));
    (void)value_0;
    uint32_t value_1 = m->r32(UINT32_C(0x8033689c));
    (void)value_1;
    uint32_t value_2 = m->r32((value_0 + UINT32_C(0x15c)));
    (void)value_2;
    uint32_t value_3 = m->r32(UINT32_C(0x80336898));
    (void)value_3;
    m->w32((value_0 + UINT32_C(0x15c)), ((value_2 & ~(value_1 | value_1)) | value_3));
    return ~(value_1 | value_1);
}

/* 4 target reads, 1 target store; 36 original bytes. */
uint32_t tak_scalar_80239784(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc8)));
    (void)value_0;
    uint32_t value_1 = m->r32(UINT32_C(0x80336898));
    (void)value_1;
    uint32_t value_2 = m->r32((value_0 + UINT32_C(0x15c)));
    (void)value_2;
    uint32_t value_3 = m->r32(UINT32_C(0x8033689c));
    (void)value_3;
    m->w32((value_0 + UINT32_C(0x15c)), ((value_2 & ~(value_1 | value_1)) | value_3));
    return ~(value_1 | value_1);
}

/* 4 target reads, 1 target store; 32 original bytes. */
uint32_t tak_scalar_802397A8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc8)));
    (void)value_0;
    uint32_t value_1 = m->r32(UINT32_C(0x80336898));
    (void)value_1;
    uint32_t value_2 = m->r32((value_0 + UINT32_C(0x15c)));
    (void)value_2;
    uint32_t value_3 = m->r32(UINT32_C(0x8033689c));
    (void)value_3;
    m->w32((value_0 + UINT32_C(0x15c)), ((value_2 & ~value_1) & ~value_3));
    return value_1;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8023B124(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc8)));
    (void)value_0;
    m->w8((value_0 + UINT32_C(0x24c)), (uint8_t)UINT32_C(0x1));
    return value_0;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8023B1F4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0xc8)));
    (void)value_0;
    m->w8((value_0 + UINT32_C(0x24d)), (uint8_t)UINT32_C(0x0));
    return value_0;
}

/* 3 target stores; 24 original bytes. */
uint32_t tak_scalar_802424A4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, b);
    m->w8((a + UINT32_C(0x9)), (uint8_t)UINT32_C(0x1));
    m->w8((a + UINT32_C(0x8)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 24 original bytes. */
uint32_t tak_scalar_80242558(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(a);
    (void)value_0;
    m->w8((b + UINT32_C(0x252)), (uint8_t)(((UINT32_C(0x0) - value_0) | value_0) >> 31));
    return value_0;
}

/* 3 target stores; 20 original bytes. */
uint32_t tak_scalar_80252ED8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x252)), (uint8_t)UINT32_C(0x0));
    m->w32((a + UINT32_C(0x1e4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x1e8)), UINT32_C(0x0));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80257F90(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x344)), UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 16 original bytes. */
uint32_t tak_scalar_8025AFD0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x13c)));
    (void)value_0;
    m->w32((a + UINT32_C(0x13c)), (value_0 & UINT32_C(0xffffff)));
    return a;
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_8026060C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0x14)));
    (void)value_0;
    return (value_0 & UINT32_C(0x1));
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_80260650(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0x14)));
    (void)value_0;
    return (((value_0 << 31) | (value_0 >> 1)) & UINT32_C(0x1));
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_8026139C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x194)), (uint8_t)UINT32_C(0x1));
    return a;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_802613A8(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w8((a + UINT32_C(0x194)), (uint8_t)UINT32_C(0x0));
    return a;
}

/* 1 target read, 1 target store; 20 original bytes. */
uint32_t tak_scalar_802613B4(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r8((a + UINT32_C(0x194)));
    (void)value_0;
    m->w8((a + UINT32_C(0x194)), (uint8_t)(leading_zeros(value_0) >> 5));
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80261884(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x7e8)), b);
    m->w32((a + UINT32_C(0x7e4)), c);
    return a;
}

/* 1 target read, 1 target store; 12 original bytes. */
uint32_t tak_scalar_80262EE0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32((a + UINT32_C(0x88)));
    (void)value_0;
    m->w32((a + UINT32_C(0x84)), value_0);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265914(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x464)), c);
    m->w32((a + UINT32_C(0x468)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265920(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x46c)), c);
    m->w32((a + UINT32_C(0x470)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_8026592C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x474)), c);
    m->w32((a + UINT32_C(0x478)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265938(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x47c)), c);
    m->w32((a + UINT32_C(0x480)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265944(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x484)), c);
    m->w32((a + UINT32_C(0x488)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265950(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x48c)), c);
    m->w32((a + UINT32_C(0x490)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_8026595C(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x494)), c);
    m->w32((a + UINT32_C(0x498)), b);
    return a;
}

/* 2 target stores; 12 original bytes. */
uint32_t tak_scalar_80265968(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32((a + UINT32_C(0x49c)), c);
    m->w32((a + UINT32_C(0x4a0)), b);
    return a;
}

/* 5 target stores; 36 original bytes. */
uint32_t tak_scalar_802660DC(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(a, UINT32_C(0x802f1f68));
    m->w32((a + UINT32_C(0x4)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x8)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0xc)), UINT32_C(0x0));
    m->w32((a + UINT32_C(0x10)), UINT32_C(0x0));
    return a;
}

/* 1 target store; 16 original bytes. */
uint32_t tak_scalar_80268790(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffffa77c)), UINT32_C(0x0));
    return (a + UINT32_C(0x10000));
}

/* 1 target read, scalar result; 12 original bytes. */
uint32_t tak_scalar_802687A0(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    uint32_t value_0 = m->r32(((a + UINT32_C(0x10000)) + UINT32_C(0xffffa77c)));
    (void)value_0;
    return value_0;
}

/* 1 target store; 12 original bytes. */
uint32_t tak_scalar_80268E24(uint32_t a, uint32_t b, uint32_t c, uint32_t d,
                              const TakTarget *m)
{
    (void)a; (void)b; (void)c; (void)d; (void)m;
    m->w32(((a + UINT32_C(0x10000)) + UINT32_C(0xffffa73c)), b);
    return (a + UINT32_C(0x10000));
}
