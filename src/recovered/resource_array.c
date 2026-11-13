/* fn_801B92FC: semantic target-memory model. Header count is not checked
 * by the original accessor. Mode 1 assumes fn_801B91FC has relocated entries.
 * Header/record semantics beyond layout remain unknown.
 */
#include <stdint.h>

/* fn_801B91FC (0x801B91FC..0x801B9244): in-place relocation.
 * Unlike the accessor, this routine has no null-base guard. Bit 2 is
 * recorded but never tested: calling twice adds base twice. The count is
 * reloaded on each iteration, as in the original target-memory loop.
 */
void tak_resource_array_relocate(uint32_t base,
                                uint16_t (*read_u16)(uint32_t),
                                uint32_t (*read_u32)(uint32_t),
                                void (*write_u16)(uint32_t, uint16_t),
                                void (*write_u32)(uint32_t, uint32_t))
{
    uint16_t flags = read_u16(base + UINT32_C(2));
    if (!(flags & 1u))
        return;
    write_u16(base + UINT32_C(2), (uint16_t)(flags | 4u));
    for (uint32_t i = 0; (uint16_t)i < read_u16(base); ++i) {
        uint32_t address = base + UINT32_C(4) + (uint16_t)i * UINT32_C(4);
        write_u32(address, read_u32(address) + base);
    }
}

uint32_t tak_resource_array_item(uint32_t base, uint32_t index,
                                 uint16_t (*read_u16)(uint32_t),
                                 uint32_t (*read_u32)(uint32_t))
{
    if (!base)
        return 0;
    uint16_t flags = read_u16(base + UINT32_C(2));
    index &= UINT32_C(0x00ffffff);
    switch (flags & 3u) {
    case 1:
        return read_u32(base + UINT32_C(4) + index * UINT32_C(4));
    case 2:
        return base + ((flags & 8u) ? UINT32_C(16) : UINT32_C(8))
                    + index * read_u32(base + UINT32_C(4));
    default:
        return 0;
    }
}
