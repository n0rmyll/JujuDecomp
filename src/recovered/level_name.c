/* fn_801042FC, semantic 32-bit address-space model, GJUE78 rev 0.
 * No bounds check exists in the original. The callback implements target
 * big-endian word reads; the result is a target address, not a host pointer.
 */
#include <stdint.h>

uint32_t tak_level_name_address(uint32_t state_address,
                                uint32_t (*read_u32)(uint32_t))
{
    uint32_t config = read_u32(state_address + UINT32_C(0x1b4));
    uint32_t index = read_u32(config + UINT32_C(4));
    return read_u32(UINT32_C(0x802cd918) + index * UINT32_C(0x1c));
}
