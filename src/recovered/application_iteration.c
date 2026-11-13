/* Semantic reconstruction of fn_80213584 (GJUE78 rev 0).
 * Callback parameters stand in for the original 32-bit virtual dispatch and
 * global singleton. This host-side model is NOT a matching binary replacement.
 * Names describe observed call order; subsystem semantics remain provisional.
 */
#include <stdint.h>

typedef void (*TakObjectCall)(void *object);
typedef uint32_t (*TakObjectResultCall)(void *object);

void tak_application_request_stop(void *application);

void tak_application_iteration(
    void *application,
    void *game,
    TakObjectCall input_slot_0c,
    TakObjectCall subsystem_80283f7c,
    TakObjectResultCall game_slot_1c,
    TakObjectCall input_slot_10)
{
    uint8_t *bytes = application;
    input_slot_0c(bytes + 0x478);
    subsystem_80283f7c(bytes + 0x4d8);
    if ((game_slot_1c(game) & 0xffu) == 0)
        tak_application_request_stop(application);
    input_slot_10(bytes + 0x478);
}
