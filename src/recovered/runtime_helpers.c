/* Fifteen complete semantic routine models, GJUE78 rev 0. Address names
 * describe provenance, not original symbols. See RUNTIME_HELPERS.md for
 * instruction verification and callback boundaries. No binary match claimed.
 */
#include "runtime_helpers.h"
#include "resource_loaders.h"

void tak_resource_array_relocate(uint32_t, uint16_t (*)(uint32_t),
                               uint32_t (*)(uint32_t),
                               void (*)(uint32_t, uint16_t),
                               void (*)(uint32_t, uint32_t));

uint32_t tak_fn_801B90F4(uint32_t mode, uint32_t reset, const TakTarget *m)
{
    if ((uint8_t)reset) {
        m->w32(0x80322e14, 0);
        return 1;
    }
    if ((uint8_t)mode == 1) {
        uint32_t pointer = m->r32(0x80322e14);
        if (pointer)
            m->call(0x802061b8, pointer, 0, 0);
        m->w32(0x80322e14, 0);
    } else if (!(m->r32(0x80322e00) & 8u)) {
        uint32_t pointer = m->r32(0x80322e14);
        uint32_t cursor = m->r32(0x80322e18);
        m->call(0x80205f64, pointer, cursor - pointer, 0);
    }
    return 1;
}

uint32_t tak_fn_801C5A64(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                        const TakTarget *m)
{
    uint16_t flags = m->r16(h + 2u);
    m->w16(h + 2u, (uint16_t)(flags & 0xfffeu));
    m->w32(o, p);
    uint32_t size = m->r32(h + 4u);
    m->w32(s, size);
    return 1;
}

uint32_t tak_fn_801B9190(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                        const TakTarget *m)
{
    tak_resource_array_relocate(p, m->r16, m->r32, m->w16, m->w32);
    return tak_fn_801C5A64(p, h, o, s, m);
}

static uint16_t swap16(uint16_t value)
{
    return (uint16_t)((value >> 8) | (value << 8));
}

static uint32_t swap32(uint32_t value)
{
    return (value >> 24) | ((value >> 8) & 0xff00u)
         | ((value << 8) & 0xff0000u) | (value << 24);
}

void tak_fn_801B9244(uint32_t p, const TakTarget *m)
{
    uint16_t count = m->r16(p);
    m->w16(p, swap16(count));
    uint16_t flags = m->r16(p + 2u);
    m->w16(p + 2u, swap16(flags));
    /* Original rereads the swapped flags from target memory. */
    flags = m->r16(p + 2u);
    if (!(flags & 1u))
        return;
    m->w16(p + 2u, (uint16_t)(flags | 4u));
    for (uint32_t i = 0; (uint16_t)i < m->r16(p); ++i) {
        uint32_t entry = p + 4u + (uint16_t)i * 4u;
        uint32_t offset = m->r32(entry);
        m->w32(entry, swap32(offset) + p);
    }
}

uint32_t tak_fn_8021311C(uint32_t owner, uint32_t next, const TakTarget *m)
{
    m->call(0x802131a0, owner, next, 0);
    return 1;
}

uint32_t tak_fn_80213710(uint32_t app, const TakTarget *m)
{
    return (uint8_t)m->call(0x80211dd8, app + 0x478u, 0, 0) != 0;
}

uint32_t tak_fn_80213744(uint32_t app, const TakTarget *m)
{
    return (uint8_t)m->call(0x80282250, app + 0x4d8u, 0, 0) != 0;
}

uint32_t tak_fn_80213480(uint32_t app, const TakTarget *m)
{
    if (!tak_fn_80213710(app, m))
        return 0;
    (void)tak_fn_80213744(app, m);
    return 1;
}

uint32_t tak_fn_800E53C4(const TakTarget *m)
{
    return m->r8(0x803312fc);
}

void tak_fn_800E53CC(uint32_t value, const TakTarget *m)
{
    m->w8(0x803312fc, (uint8_t)value);
}

/* Each device slot is read when reached; callbacks may change later slots. */
static void devices(uint32_t object, uint32_t slot, const TakTarget *m)
{
    for (uint32_t i = 0; i < 4; ++i) {
        uint32_t device = m->r32(object + 8u + 4u*i);
        if (device) {
            uint32_t table = m->r32(device);
            uint32_t method = m->r32(table + slot);
            m->call(method, device, 0, 0);
        }
    }
}

void tak_fn_80211ED4(uint32_t object, const TakTarget *m)
{
    uint32_t app = m->r32(0x803320e0);
    m->copy(object + 0x18u, app + 0x334u, 0x30);
    m->w32(object + 0x5cu, 0);
    devices(object, 0x28, m);
}

void tak_fn_80211F54(uint32_t object, const TakTarget *m)
{
    if (m->r8(object + 0x58u))
        m->call(0x8011dcac, object + 0x48u, 0, 0);
    uint32_t pending = m->r32(object + 0x5cu);
    if (pending)
        m->call(0x8011d5e8, pending, 0, 0);
    devices(object, 0x2c, m);
}

uint32_t tak_fn_8020F964(uint32_t object, const TakTarget *m)
{
    m->w32(object, 0x802ef19c);
    m->w8(object + 4u, 0);
    uint32_t allocation = m->call(0x802062a8, 0x6c, 0, 0);
    if (allocation)
        allocation = m->call(0x8017fd08, allocation, 0, 0);
    m->w32(0x80332ca0, allocation);
    m->w8(object + 0xcu, 0);
    return object;
}

uint32_t tak_fn_80213708(void)
{
    return 1;
}

uint32_t tak_fn_80280928(uint32_t object, uint32_t record, const TakTarget *m)
{
    return m->call(0x80280bb4, object, record, 0) != 0;
}
