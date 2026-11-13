# Level descriptors and DBU loading

Update: `DBU_BINARY_LAYOUT.md` records recovered binary chunk boundaries
and exact-EOF validation across Preload and Hub. The tools described here
remain useful for separate text metadata and level descriptors.

## Level-name accessor recovered

**0x801042FC** loads state +0x1B4, loads that object's word +4 as the
descriptor index, multiplies by 0x1C, and returns the first word at
**0x802CD918 + index * 0x1C**. The instruction sequence has been checked
against the original executable. `src/recovered/level_name.c` reconstructs
it using a callback for big-endian target memory reads. It preserves
32-bit arithmetic and the absence of an original bounds check. It is a
host analysis model, not a matching compiler build or host string pointer.

`tools/inspect_levels.py` decodes the table into `analysis/levels.json`.
There are 54 consecutive readable descriptors. The next row contains text
bytes instead of valid string pointers, providing an observed boundary;
an original code-level count constant has not yet been established.

Each 28-byte record begins with three string pointers: internal name,
display name, and resource path. Four remaining words are preserved as
unknowns, including a final word also represented as float without assigning
its meaning. Examples:

| Index | Internal name | Display name | Resource path |
| --- | --- | --- | --- |
| 0 | Hub | Tak's Village | Hub\\Hub |
| 1 | Lok_Training | Lok's Training | Hub\\Hub |
| 3 | Burial | Burial Ground | Burial\\burial |
| 9 | Canyon | Dryrock Canyon | Canyon\\canyon |
| 19 | TlalocBoss | Dark Temple | inbboss |
| 33 | Intro | Intro | CIsland\\chikil |

The table also contains development-looking names and FMV descriptors.
Their presence does not prove corresponding assets or playable content
exist in the retail image.

## DBU path traced

During gameplay-state initialization, **0x80101018** calls **0x800E7810**.
That routine:

1. Formats the supplied name with **`%s.dbu`** at **0x803315BC**.
2. Calls **0x80204BCC** with output pointers for two words.
3. Polls **0x80204FC0** until its low return byte equals 1.
4. Calls **0x80205040**, then resource setup helpers.
5. Passes the returned words to **0x801B7468**.

`0x801B7468` initializes the input-memory context via **0x801B8C64**,
then invokes the larger resource dispatcher **0x801B777C**. The context
initializer stores the input pointer twice at global context +0x14/+0x18
and its second argument at +0x1C. `0x801B777C` dispatches on 16-bit resource
types. Exact stream header and chunk layouts still need decoding.

Do not confuse this path with **0x80107E80**: that function uses a level
descriptor to format `level\\%sSound` and initializes sound-related
resources. It is not the level geometry DBU loader.

## First working archive inspection tool

Extracted local `Preload.dbu` and `Hub.dbu` using dtk. Both begin with an
eight-byte decimal-offset line and a readable DBLMerge build header. The
header records a build command and a `Contents:` list with original source
paths and sizes. Observed binary starts:

| Archive | Text-prefix boundary | Declared source resources |
| --- | --- | --- |
| Preload.dbu | 0xC60 (3168) | 41 |
| Hub.dbu | 0x1E80 (7808) | 91 |

`tools/inspect_dbu_header.py` validates the prefix range, producer marker,
contents syntax, and sequential indices, then exports metadata. It does
**not** extract packed resources: original source sizes do not establish
packed offsets or imply source files are concatenated unchanged. The
decimal-offset meaning is observed from these two samples; no universal
DBU format claim is made.

```sh
python3 tools/inspect_levels.py
python3 tools/inspect_dbu_header.py analysis/Preload.dbu --output analysis/preload-manifest.json
python3 tools/inspect_dbu_header.py analysis/Hub.dbu --output analysis/hub-manifest.json
```

The manifests stay local and contain metadata derived from the provided
disc. Extracted DBU binaries are ignored by Git.

## Intermediate-state progress

The 0x452C0 state's embedded object uses table **0x802C6304**:
virtual +0x194 resolves to **0x800DA524**, +0x198 to **0x800D487C**,
and +0x20 to **0x8026D9F4**. Its initialization calls the first two;
the first references **`shell\\gadgets.dbl`**. This is UI evidence, not
enough to conclusively name the entire state as title/menu/movie.

## Validation and next milestone

Function reports verify original instruction bytes for the accessor, DBU
loader, input-context initializer, resource dispatcher, and relevant UI
methods. Host Clang syntax checks pass for the C accessor. Both real DBU
samples pass the text-header inspector. No original-target rebuild has
been performed.

Next: recover **0x801B8C80** (stream/header setup) and **0x801B8E60**
(called before each resource dispatch) to establish the binary chunk
boundaries. That should permit a verified binary resource directory rather
than a text-only build manifest.
