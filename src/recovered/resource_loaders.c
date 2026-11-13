/* GJUE78 revision 0, complete semantic models of six original routines.
 * Address-based names avoid assuming original resource/class names.
 * Callbacks stand in for target memory and unresolved per-record callees.
 * No compiler matching or original executable integration is claimed.
 */
#include "resource_loaders.h"

void tak_resource_array_relocate(uint32_t, uint16_t (*)(uint32_t),
                               uint32_t (*)(uint32_t),
                               void (*)(uint32_t, uint16_t),
                               void (*)(uint32_t, uint32_t));
uint32_t tak_resource_array_item(uint32_t, uint32_t,
                                uint16_t (*)(uint32_t), uint32_t (*)(uint32_t));

static void relocate(uint32_t payload, const TakResourceMemory *m)
{
    tak_resource_array_relocate(payload, m->read16, m->read32,
                               m->write16, m->write32);
}

/* The output store precedes the header read, including when they alias. */
static uint32_t publish(uint32_t payload, uint32_t header, uint32_t output,
                        uint32_t size_output, const TakResourceMemory *m)
{
    m->write32(output, payload);
    uint32_t size = m->read32(header + UINT32_C(4));
    m->write32(size_output, size);
    return 1;
}

/* Three distinct 96-byte original routines have the same complete logic. */
uint32_t tak_load_801C5944(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                          const TakResourceMemory *m)
{
    relocate(p, m);
    return publish(p, h, o, s, m);
}

uint32_t tak_load_801C59A4(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                          const TakResourceMemory *m)
{
    relocate(p, m);
    return publish(p, h, o, s, m);
}

uint32_t tak_load_801C5A04(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                          const TakResourceMemory *m)
{
    relocate(p, m);
    return publish(p, h, o, s, m);
}

static uint32_t process_array(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                              const TakResourceMemory *m,
                              void (*process)(uint32_t))
{
    relocate(p, m);
    /* Original reloads count after each callback; do not cache it. */
    for (uint32_t i = 0; (uint16_t)i < m->read16(p); ++i) {
        uint32_t item = tak_resource_array_item(p, (uint16_t)i,
                                               m->read16, m->read32);
        process(item);
    }
    uint16_t flags = m->read16(h + UINT32_C(2));
    m->write16(h + UINT32_C(2), (uint16_t)(flags & UINT16_C(0xfffe)));
    return publish(p, h, o, s, m);
}

/* 0x801C5BAC..0x801C5C34: process is original fn_801C5D28.
 * Its return value is ignored by the original caller.
 */
uint32_t tak_load_801C5BAC(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                          const TakResourceMemory *m, void (*process)(uint32_t))
{
    return process_array(p, h, o, s, m, process);
}

/* 0x801C5C34..0x801C5CBC: process is original fn_801C5F1C. */
uint32_t tak_load_801C5C34(uint32_t p, uint32_t h, uint32_t o, uint32_t s,
                          const TakResourceMemory *m, void (*process)(uint32_t))
{
    return process_array(p, h, o, s, m, process);
}

/* 0x801B90D0..0x801B90F4: no bounds checks; unsigned wrap is intentional.
 * Both original loads precede both stores.
 */
void tak_dbu_advance_801B90D0(uint32_t amount, const TakResourceMemory *m)
{
    uint32_t cursor = m->read32(UINT32_C(0x80322e18));
    uint32_t remaining = m->read32(UINT32_C(0x80322e1c));
    m->write32(UINT32_C(0x80322e18), cursor + amount);
    m->write32(UINT32_C(0x80322e1c), remaining - amount);
}
