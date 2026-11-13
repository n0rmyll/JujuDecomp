#include <stdint.h>
#include <stdio.h>
#include <string.h>

void tak_application_request_stop(void *application);

int main(void)
{
    /* Exercise every prior flag value and detect writes to adjacent bytes. */
    for (unsigned initial = 0; initial < 256; ++initial) {
        uint8_t actual[32], expected[32];
        memset(actual, 0xa5, sizeof(actual));
        actual[4] = (uint8_t)initial;
        memcpy(expected, actual, sizeof(actual));
        expected[4] = 1;
        tak_application_request_stop(actual);
        if (memcmp(actual, expected, sizeof(actual)) != 0) {
            fprintf(stderr, "Unexpected write for initial flag %u\n", initial);
            return 1;
        }
        tak_application_request_stop(actual);
        if (memcmp(actual, expected, sizeof(actual)) != 0)
            return 1;
    }
    puts("PASS: all 256 flag values, adjacent bytes, repeated stop requests");
    return 0;
}
