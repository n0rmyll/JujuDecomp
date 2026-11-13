/* fn_801B8FD0, 0x801B8FD0..0x801B9014 (68 bytes).
 * Semantic target-memory model, not compiler-matched source. The global
 * context is at 0x80322E00. Handler names are addresses because their full
 * semantics are not yet recovered. Callbacks replace original direct calls.
 */
#include <stdint.h>

void tak_dbu_payload_dispatch(uint16_t (*read_u16)(uint32_t),
                              uint32_t (*read_u32)(uint32_t),
                              void (*handler_801B9014)(uint32_t),
                              void (*handler_801B90D0)(uint32_t))
{
    uint16_t flags = read_u16(UINT32_C(0x80322e4e));
    uint32_t value = read_u32(UINT32_C(0x80322e50));
    if (flags & 1u)
        handler_801B9014(value);
    else
        handler_801B90D0(value);
}
