#ifndef TAK_TRANSFER_CONTEXT_H
#define TAK_TRANSFER_CONTEXT_H
#include "runtime_helpers.h"
/* Research interface: 42 integer words plus 32 scalar PS0 binary64 words.
 * PS1, FPSCR, XER, hardware and real callee behavior are unresolved.
 * Single conversions admit signed zero or exactly representable normal
 * binary32 values only; other inputs are outside the model domain.
 * Double transfers use two ordered 32-bit target-memory callbacks.
 */
typedef struct TakTransferCalls {
    void (*invoke)(uint32_t target, uint32_t state[42], uint64_t scalar[32]);
} TakTransferCalls;
#endif
