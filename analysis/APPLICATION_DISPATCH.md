# Recovered application dispatch: GJUE78 rev 0

All addresses below come from the original DOL and generated disassembly.
Descriptive names are analysis labels, not recovered original class names.
Run `python3 tools/verify_application_map.py` to verify the executable hash,
table words, singleton pointers, constructor stores, and stop-flag setter.
The machine-readable result is `application-map.json`.

## Application object

The `.ctors` entry at **0x802A201C** points to **0x8021378C**. That static
initializer constructs the BSS object at **0x803276F8**, first calls the base
constructor `0x8020F964`, then installs **0x802EF344** as its vtable. It
constructs embedded objects at +0x478, +0x4D8, and +0x6B4 and registers a
destructor. The automatic BSS region is 0x7D0 bytes; an exact original C++
class declaration has not been recovered.

| Vtable byte offset | Target | Observed role |
| --- | --- | --- |
| +0x08 | 0x80213214 | Destructor path |
| +0x0C | 0x802132AC | Application initialization, receives command line |
| +0x10 | 0x802134C8 | Shutdown |
| +0x14 | 0x80213584 | One application iteration |

`main` uses the table base including its two leading zero words. Offsets
above are literal byte offsets from that base, not C++ slot numbers after
skipping metadata.

One iteration, recovered from **0x80213584..0x80213600**:

1. Call member at application +0x478, vtable +0x0C → **0x80211ED4**.
2. Call **0x80283F7C** on member at application +0x4D8.
3. Call singleton loaded from **0x803312F8**, vtable +0x1C → **0x80212A80**.
4. If the low return byte is zero, call **0x8020F9C8**, setting application
   byte +0x04 to 1. `main` tests that byte to stop iterating.
5. Call member at application +0x478, vtable +0x10 → **0x80211F54**, even
   when the stop flag was just set.

The +0x478 member's constructor **0x80211CEC** installs table **0x802EF2A0**.
Its paired methods loop over four pointer slots and invoke device methods
at +0x28 / +0x2C, respectively. This supports an input/controller role,
but exact SDK callees and original class names remain to be identified.
The +0x4D8 member's subsystem role is still unknown.

`src/recovered/application_iteration.c` records this sequencing as a host C
model with callbacks for virtual dispatch. It preserves the low-byte result
test and final member call. It is not ABI-compatible with the original
32-bit executable and is not yet linked into a port.

## Game-specific singleton and state dispatcher

Global **0x803312F8** initially points to BSS **0x802F71EC**. Its static
initializer **0x800E53D4** calls base constructor **0x802129A8**, then
installs table **0x802CE4D8**. The table address is formed by loading
0x802C7780 and adding 0x6D58. This derived table retains a base iteration
implementation rather than overriding it.

| Vtable byte offset | Target | Observed role |
| --- | --- | --- |
| +0x08 | 0x800E3FB0 | Destructor path |
| +0x0C | 0x800E4060 | Writes application configuration defaults |
| +0x10 | 0x800E53C4 | Reads global byte at 0x803312FC |
| +0x14 | 0x800E53CC | Writes that global byte |
| +0x18 | 0x800E414C | Game initialization |
| +0x1C | 0x80212A80 | State/timing iteration dispatcher |
| +0x20 | 0x800E45C4 | Called by application shutdown |
| +0x24 | 0x800E4608 | Called after an active state finishes |

**0x80212A80** handles timing data at **0x80322D28**, multiple mode branches,
and buffers copied in 0x70-byte increments. A replay/input-recording role for
those buffers is a hypothesis, not yet verified.

The confirmed active-state path at **0x80212EF4** loads the pointer from
game object **+0x04**, then calls its vtable **+0x10** at **0x80212F04**.
A false low-byte result, or game byte +0x10 being set, takes the path through
**0x802131A0**. That function calls the active state's vtable +0x14, clears
the active pointer, and calls game vtable +0x24 with the result (or -1).

When no active state exists and a pending pointer at game +0x08 is present,
**0x80213140** installs it as the active state and calls state vtable +0x0C.
The dispatcher returns false if activation fails, otherwise ultimately
returns whether an active pointer remains. This explains how state lifetime
reaches the application's stop flag.

## What is still unresolved

The top-level loop and two singleton tables are recovered. Update and
rendering are not yet separately identified: the next dispatch boundary is
the active state object's +0x10 method. Recover the concrete state vtables
created during **0x800E414C** and state transitions in **0x800E4608**, then
trace those methods to simulation and graphics calls. Do not label the
initializer 0x800E414C as the per-frame update; the table selects
0x80212A80 for iteration.

Validation so far is static original-byte verification plus host Clang
syntax checks for the reconstructed C. No matching CodeWarrior rebuild,
patched-ROM run, or native-renderer validation has been performed.
