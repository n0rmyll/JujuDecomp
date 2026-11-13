# Standalone DSP audio extraction

`tools/decode_audio.py` decodes the standard mono Nintendo DSP ADPCM files
under local `assets/disc/` to 16-bit little-endian PCM WAVs under ignored
`assets/audio/`. It does not resample or normalize the sound. The generated
`index.html` searches filenames and plays WAVs with browser audio controls.

## Format evidence

All 1,005 local `.dsp` files have a 96-byte big-endian header. All declare
22,050 Hz and match both the sample-to-nibble relationship and exact file
size. Header fields contain sample count (+0), nibble count (+4), sample
rate (+8), loop/codec fields (+12/+14), initial nibble offset (+24), sixteen
signed predictor coefficients (+28), and initial history (+64/+66).

The complete pass exported 1,005 WAVs with zero errors, totaling 4,335.48
seconds (72.26 minutes). Every WAV was reopened and checked for its channel
count, sample width, sample rate, frame count, and decoded PCM SHA-256.
macOS `afinfo` independently recognized a sampled export as 22,050 Hz mono
16-bit PCM WAV.

The standard format and predictor calculation were checked against the
vgmstream project's [DSP header reader](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ngc_dsp_std.c)
and [DSP decoder](https://github.com/vgmstream/vgmstream/blob/master/src/coding/ngc_dsp_decoder.c).
An eight-byte frame has a predictor/scale byte and fourteen signed four-bit
samples, high nibble first. The predictor uses the preceding two decoded
samples; output rounds and saturates to signed 16-bit. Last partial frames
are bounded by the declared sample count.

The decoder requires the observed encoding, initial offset 2, zero gain,
consistent initial predictor, valid predictor indices, exact nibble count,
and exact file size. It rejects unsupported variants instead of silently
interpreting them. Reserved header bytes are not used to infer channels:
standard DSP headers may contain uninitialized bytes there.

## Validation and limits

Six independent fixtures verify signed nibble order and partial frames,
history across frame boundaries, second-history prediction and rounding,
scale and saturation, loop metadata, and malformed inputs. The manifest records source
and decoded PCM SHA-256 hashes, sample counts, duration, peak, saturation
count, and original loop nibble offsets.

WAV files play once; loops are retained as manifest metadata rather than
being repeated or embedded in a WAV sampler chunk. Clip names are preserved
as identifiers; character, speaker, and transcript labels are not inferred.
This pass does not decode the 19 `.adp` music streams or the 39 `.dba` sound
banks. Listening verification and original-hardware audio comparison have
not been performed.
