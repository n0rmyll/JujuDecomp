/* Safe portable reader for observed 0x0601 records. Field offsets follow
 * fn_80280BB4 and fn_8027F680. This is an offline decoder, not a matching
 * reconstruction of the runtime constructor. Semantic field names remain
 * provisional; the original record is 192 bytes, big-endian.
 */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static uint32_t read_be32(const uint8_t *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
         | ((uint32_t)p[2] << 8) | p[3];
}

/* Output contains all 48 original word bit patterns in host byte order.
 * Float fields are represented as bits, avoiding host alignment/aliasing
 * assumptions and preserving all unknown fields exactly.
 */
int tak_world_volume_decode(const uint8_t *record, size_t length,
                           uint32_t words[48])
{
    if (!record || !words || length < 192)
        return 0;
    for (size_t i = 0; i < 48; ++i)
        words[i] = read_be32(record + 4*i);
    return 1;
}

/* Scalar reconstruction from fn_8027F680: flag bit zero copied to byte +0x20. */
uint8_t tak_world_volume_flag(uint32_t record_flags)
{
    return (uint8_t)(record_flags & 1u);
}
