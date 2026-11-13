/* fn_801B92FC: semantic target-memory model. Header count is not checked
 * by the original accessor. Mode 1 assumes fn_801B91FC has relocated entries.
 * Header/record semantics beyond layout remain unknown.
 */
#include <stdint.h>

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
