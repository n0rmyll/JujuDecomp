#ifndef TAK_CALL_CONTEXT_H
#define TAK_CALL_CONTEXT_H
#include "runtime_helpers.h"
/* Research integer context: GPR0..31, LR, CTR, eight LT/GT/EQ flag fields.
 * invoke represents an external callee boundary, not an implementation of
 * that callee. The callback can update context and shared target memory.
 * FPU, XER, exceptions and hardware behavior are outside this interface.
 */
typedef struct TakOpaqueCalls {
    void (*invoke)(uint32_t target, uint32_t state[42]);
} TakOpaqueCalls;
#endif
