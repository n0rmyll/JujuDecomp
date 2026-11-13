/* Header-size selection in fn_801B8E60, 0x801B8F24..0x801B8F5C.
 * Input flags are already decoded to host order. No compiler matching yet.
 */
#include <stdint.h>

uint32_t tak_dbu_chunk_header_size(uint16_t flags)
{
    if (flags & 8u)
        return (flags & 2u) ? 64u : 32u;
    return (flags & 2u) ? 42u : 10u;
}
