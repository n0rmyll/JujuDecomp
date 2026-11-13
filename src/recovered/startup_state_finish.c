/* fn_800CEB2C, semantic reconstruction, GJUE78 rev 0.
 * Original globals: selection at 0x802F58A4; game pointer at 0x8033267C.
 * game field +0xEC is named mode here provisionally. Pointer parameters and
 * callback replace original globals; this is not a matching replacement.
 */
#include <stdint.h>

int32_t tak_startup_state_finish(int32_t *selection, int32_t *game_mode,
                                void (*cleanup_80260a80)(void))
{
    cleanup_80260a80();
    if (*selection == -1) {
        *selection = 0x37;
        return 1;
    }
    if (*selection == 0x37) {
        *game_mode = 1;
        return 2;
    }
    return 3;
}
