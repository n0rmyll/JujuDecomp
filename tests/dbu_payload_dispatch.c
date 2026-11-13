#include <assert.h>
#include <stdint.h>
#include <stdio.h>

void tak_dbu_payload_dispatch(uint16_t (*)(uint32_t), uint32_t (*)(uint32_t),
                              void (*)(uint32_t), void (*)(uint32_t));

static uint16_t flags;
static uint32_t value;
static unsigned stage;

static uint16_t read16(uint32_t address)
{
    assert(stage++ == 0);
    assert(address == UINT32_C(0x80322e4e));
    return flags;
}

static uint32_t read32(uint32_t address)
{
    assert(stage++ == 1);
    assert(address == UINT32_C(0x80322e50));
    return value;
}

static void odd_handler(uint32_t argument)
{
    assert(stage++ == 2);
    assert(flags & 1u);
    assert(argument == value);
}

static void even_handler(uint32_t argument)
{
    assert(stage++ == 2);
    assert(!(flags & 1u));
    assert(argument == value);
}

int main(void)
{
    const uint32_t values[] = {0, 1, UINT32_C(0x80000000), UINT32_MAX};
    for (uint32_t f = 0; f <= UINT16_MAX; ++f) {
        flags = (uint16_t)f;
        for (unsigned i = 0; i < sizeof(values) / sizeof(values[0]); ++i) {
            value = values[i];
            stage = 0;
            tak_dbu_payload_dispatch(read16, read32, odd_handler, even_handler);
            assert(stage == 3);
        }
    }
    puts("PASS: 262144 dispatch cases, exact read order/addresses and one handler call");
    return 0;
}
