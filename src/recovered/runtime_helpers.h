#ifndef TAK_RUNTIME_HELPERS_H
#define TAK_RUNTIME_HELPERS_H
#include <stdint.h>
/* Semantic target interface. call receives target, r3, r4, r5; unused
 * argument positions are zero placeholders, not recovered ABI guarantees.
 * copy models the original memcpy call; no overlap safety is added.
 */
typedef struct TakTarget {
    uint8_t (*r8)(uint32_t);
    uint16_t (*r16)(uint32_t);
    uint32_t (*r32)(uint32_t);
    void (*w8)(uint32_t, uint8_t);
    void (*w16)(uint32_t, uint16_t);
    void (*w32)(uint32_t, uint32_t);
    uint32_t (*call)(uint32_t, uint32_t, uint32_t, uint32_t);
    void (*copy)(uint32_t, uint32_t, uint32_t);
} TakTarget;
uint32_t tak_fn_801B90F4(uint32_t, uint32_t, const TakTarget *);
uint32_t tak_fn_801B9190(uint32_t, uint32_t, uint32_t, uint32_t, const TakTarget *);
void tak_fn_801B9244(uint32_t, const TakTarget *);
uint32_t tak_fn_801C5A64(uint32_t, uint32_t, uint32_t, uint32_t, const TakTarget *);
uint32_t tak_fn_8021311C(uint32_t, uint32_t, const TakTarget *);
uint32_t tak_fn_80213480(uint32_t, const TakTarget *);
uint32_t tak_fn_80213710(uint32_t, const TakTarget *);
uint32_t tak_fn_80213744(uint32_t, const TakTarget *);
uint32_t tak_fn_800E53C4(const TakTarget *);
void tak_fn_800E53CC(uint32_t, const TakTarget *);
void tak_fn_80211ED4(uint32_t, const TakTarget *);
void tak_fn_80211F54(uint32_t, const TakTarget *);
uint32_t tak_fn_8020F964(uint32_t, const TakTarget *);
uint32_t tak_fn_80213708(void);
uint32_t tak_fn_80280928(uint32_t, uint32_t, const TakTarget *);
#endif
