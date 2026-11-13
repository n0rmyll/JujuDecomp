#ifndef TAK_RESOURCE_LOADERS_H
#define TAK_RESOURCE_LOADERS_H
#include <stdint.h>

/* Host callback interface for the 32-bit target address space. This is not
 * an original ABI or object layout. Callbacks must implement target accesses.
 */
typedef struct TakResourceMemory {
    uint16_t (*read16)(uint32_t);
    uint32_t (*read32)(uint32_t);
    void (*write16)(uint32_t, uint16_t);
    void (*write32)(uint32_t, uint32_t);
} TakResourceMemory;

typedef uint32_t (*TakResourceLoader)(uint32_t, uint32_t, uint32_t, uint32_t,
                                    const TakResourceMemory *);
uint32_t tak_load_801C5944(uint32_t, uint32_t, uint32_t, uint32_t, const TakResourceMemory *);
uint32_t tak_load_801C59A4(uint32_t, uint32_t, uint32_t, uint32_t, const TakResourceMemory *);
uint32_t tak_load_801C5A04(uint32_t, uint32_t, uint32_t, uint32_t, const TakResourceMemory *);
uint32_t tak_load_801C5BAC(uint32_t, uint32_t, uint32_t, uint32_t, const TakResourceMemory *, void (*)(uint32_t));
uint32_t tak_load_801C5C34(uint32_t, uint32_t, uint32_t, uint32_t, const TakResourceMemory *, void (*)(uint32_t));
void tak_dbu_advance_801B90D0(uint32_t, const TakResourceMemory *);
#endif
