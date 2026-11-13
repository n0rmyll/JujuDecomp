/* Nintendo DTK stereo ADPCM decoding. See analysis/MUSIC_EXTRACTION.md. */
#include <stddef.h>
#include <stdint.h>

/* Defined arithmetic shifts, including negative values, without signed shifts. */
static int64_t floor_shift(int64_t value, unsigned bits) {
    int64_t divisor = (int64_t)1 << bits;
    return value >= 0 ? value / divisor : -((-value + divisor - 1) / divisor);
}

/* state: left history1/history2, right history1/history2; preserved across calls.
 * Output is little-endian interleaved PCM16, 112 bytes per 32-byte input block.
 * Return 0 on success; -1 truncated block; -2 header mismatch; -3 unsupported header.
 * Validate the entire buffer before changing output or history. */
int tak_dtk_decode(const uint8_t *input, size_t size, uint8_t *output, int32_t state[4]) {
    static const int coefficients[4][2] = {{0, 0}, {60, 0}, {115, 52}, {98, 55}};
    if (size % 32 != 0) return -1;
    for (size_t offset = 0; offset < size; offset += 32) {
        if (input[offset] != input[offset+2] || input[offset+1] != input[offset+3]) return -2;
        for (int channel = 0; channel < 2; channel++) {
            uint8_t header = input[offset+channel];
            if ((header >> 4) > 3 || (header & 15) > 12) return -3;
        }
    }
    size_t written = 0;
    for (size_t offset = 0; offset < size; offset += 32) {
        for (int sample = 0; sample < 28; sample++) {
            for (int channel = 0; channel < 2; channel++) {
                uint8_t header = input[offset+channel];
                int predictor = header >> 4;
                int nibble = (input[offset+4+(size_t)sample] >> (channel*4)) & 15;
                if (nibble >= 8) nibble -= 16;
                int64_t prediction = floor_shift((int64_t)state[channel*2]*coefficients[predictor][0]
                                     - (int64_t)state[channel*2+1]*coefficients[predictor][1]+32, 6);
                if (prediction > 2097151) prediction = 2097151;
                if (prediction < -2097152) prediction = -2097152;
                int32_t current = (int32_t)(floor_shift((int64_t)nibble*4096, header & 15)*64+prediction);
                state[channel*2+1] = state[channel*2];
                state[channel*2] = current; /* History is not clipped to PCM16. */
                int64_t value = floor_shift(current, 6);
                if (value > 32767) value = 32767;
                if (value < -32768) value = -32768;
                uint16_t bits = (uint16_t)value;
                output[written++] = (uint8_t)(bits & 255);
                output[written++] = (uint8_t)(bits >> 8);
            }
        }
    }
    return 0;
}
