/* GJUE78 rev 0: fn_8020F9C8, 12 bytes.
 * Semantic reconstruction from the original instructions:
 *   li r0, 1; stb r0, 4(r3); blr
 * main tests this byte before calling the next iteration.
 * The descriptive name is ours, not an original recovered symbol.
 * No matching CodeWarrior compilation has been performed.
 */
#include <stdint.h>

void tak_application_request_stop(void *application)
{
    ((uint8_t *)application)[4] = 1;
}
