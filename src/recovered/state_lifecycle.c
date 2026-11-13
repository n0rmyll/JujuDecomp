/* GJUE78 rev 0: semantic host model of fn_80213140 and fn_802131A0.
 * Original offsets: active +4, pending +8, force byte +0x10 (32-bit PPC).
 * This struct is deliberately a host model, NOT an original memory layout.
 * Callback signatures and descriptive names are provisional.
 */
#include <stdint.h>

typedef struct TakStateModel {
    void *object;
    uint32_t (*initialize_slot_0c)(void *);
    int32_t (*finish_slot_14)(void *);
} TakStateModel;

typedef struct TakStateOwnerModel {
    TakStateModel *active;
    uint8_t force;
    void *object;
    void (*transition_slot_24)(void *, int32_t);
} TakStateOwnerModel;

void tak_state_finish(TakStateOwnerModel *owner)
{
    if (owner->active) {
        int32_t result = owner->active->finish_slot_14(owner->active->object);
        owner->active = 0;
        if (owner->force)
            result = -1;
        owner->transition_slot_24(owner->object, result);
    }
}

uint32_t tak_state_activate(TakStateOwnerModel *owner, TakStateModel *next)
{
    tak_state_finish(owner);
    owner->active = next;
    if (next)
        return next->initialize_slot_0c(next->object);
    return 1;
}
