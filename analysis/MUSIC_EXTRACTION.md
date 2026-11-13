# Nintendo DTK music extraction

The 19 local `assets/disc/stream/music/*.adp` files are headerless Nintendo
DTK stereo ADPCM streams. They contain 117,833,728 bytes, or 3,682,304
32-byte blocks. Every block passed the duplicated-channel-header,
predictor (0 through 3), and shift (0 through 12) checks.

`tools/decode_music.py` compiles `tools/dtk_audio.c` into a temporary native
library using Clang, then processes streams in bounded buffers. Predictor
history is retained between buffers and reset between tracks. The temporary
library is deleted when the run completes. Python uses only standard-library
modules. macOS is verified; the Linux shared-library build path is provided
but has not been exercised here.

## Encoding evidence

The format was checked against vgmstream's [DTK reader](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ngc_adpdtk.c)
and [decoder](https://github.com/vgmstream/vgmstream/blob/master/src/coding/ngc_dtk_decoder.c),
and Dolphin's [hardware stream decoder](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/Core/HW/StreamADPCM.cpp).

A 32-byte block starts with left/right predictor-scale bytes duplicated at
offsets 2 and 3. Each of the following 28 bytes has a left sample in its low
nibble and a right sample in its high nibble. Each channel has independent
prediction history. Predictor coefficient pairs are (0,0), (60,0),
(115,52), and (98,55); the second coefficient is subtracted. Prediction is
rounded, shifted by six, and clipped to the DTK history range before adding
the scaled signed nibble. History retains precision beyond PCM16; only the
final sample is saturated to PCM16. Defined integer division handles signed
shifts without relying on C implementation-specific negative right shifts.

DTK has no sample-rate field; the output uses the nominal hardware rate of
48,000 Hz rather than a rate inferred from filenames. Each block produces
28 stereo sample frames. The files have no embedded loop points. Game DVD
streaming commands may implement loops separately; those have not been
recovered here. No lead-in or trailing samples are removed.

## Results and validation

All 19 tracks exported with zero errors: 103,104,512 stereo sample frames,
2,148.01 seconds, or 35.80 minutes. Outputs are under ignored `assets/music/`,
with a searchable browser playback gallery and JSON manifest. Original
filenames are retained without speculative titles. The manifest stores
source bytes, block count, sample count, duration, and source/PCM SHA-256.

Six tests cover left/right nibble ordering, signed samples, unclipped
history, all predictor/shift combinations against an independent Python
reference, history continuity across calls, invalid headers and truncation,
WAV metadata, preserving existing output after conversion failure, and the
first 128 blocks of every real track against the reference. Every final WAV
is separately reopened to verify its channel count, sample width, sample
rate, frame count, and PCM hash. macOS `afinfo` also checks a sampled export.

Temporary WAVs replace completed outputs only after successful decoding.
Source assets are not modified. Listening verification and comparison with
original-hardware playback have not been performed. Sound-effect DBA banks
are a separate format and remain undecoded.
