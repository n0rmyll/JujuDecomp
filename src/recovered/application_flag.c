/* GJUE78 rev 0: fn_8020F9C8, 12 bytes.
 * Semantic reconstruction from the original instructions:
 *   li r0, 1; stb r0, 4(r3); blr
 * main tests this byte before calling the next iteration.
 * The descriptive name is ours, not an original recovered symbol.
 * Exact 12-byte .text match with CodeWarrior GC 1.3.2, -O4,p -proc gekko.
 * This does not identify the original compiler or verify a linked rebuild.
 */
void tak_application_request_stop(void *application)
{
    ((unsigned char *)application)[4] = 1;
}
