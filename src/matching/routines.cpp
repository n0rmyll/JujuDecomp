/* GJUE78 rev 0 target-layout candidates. Compile one TAK_FN per object.
 * These replace the host models' callbacks with the observed PPC ABI and
 * memory offsets. Names and field types are provisional. Matching status is
 * measured by tools/check_matching.py, never inferred from this source.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;
typedef u32 (*Method)(void *);
typedef void (*Method2)(void *, s32);
#define FIELD(type, p, offset) (*(type *)((u8 *)(p) + (offset)))
/* CodeWarrior virtual tables reserve the first two words. */
class VObject {
public:
    virtual u32 slot0x08();
    virtual u32 slot0x0c();
    virtual u32 slot0x10();
    virtual u32 slot0x14();
    virtual u32 slot0x18();
    virtual u32 slot0x1c();
    virtual u32 slot0x20();
    virtual void slot0x24(s32);
    virtual u32 slot0x28();
    virtual u32 slot0x2c();
};
struct Application {
    u8 pad[0x478];
    VObject input;
    u8 pad47c[0x5c];
    u8 subsystem[1];
};
#define VCALL(p, offset) (((VObject *)(p))->slot##offset())

extern "C" {

typedef struct Header { u16 count, flags; u32 size; } Header;
typedef struct Context {
    u32 flags;
    u8 pad04[0x10];
    u8 *allocation, *cursor;
    u32 remaining;
    u8 pad20[0x2e];
    u16 payload_flags;
    u32 payload_value;
} Context;
extern Context lbl_80322E00;
extern u8 lbl_803312FC;
extern void *lbl_803312F8, *lbl_803320E0, *lbl_8033267C, *lbl_80332CA0;
extern u8 lbl_802CD918[0x1c * 64], lbl_802EF19C[0x20];
extern s32 lbl_802F58A0[16];
extern void fn_80260A80(void), fn_801B9014(u32), fn_801B90D0(u32);
extern void fn_802061B8(void *), fn_80205F64(void *, u32);
extern void fn_801B91FC(Header *), fn_801C5D28(void *), fn_801C5F1C(void *);
extern void *fn_801B92FC(Header *, u32);
extern void fn_802131A0(void *);
extern u8 fn_80213710(void *), fn_80213744(void *);
extern u8 fn_80211DD8(void *), fn_80282250(void *, u32);
extern void fn_80283F7C(void *), fn_8020F9C8(void *);
extern void *memcpy(void *, const void *, u32);
extern void fn_8011DCAC(void *), fn_8011D5E8(void *);
extern void *fn_802062A8(u32), *fn_8017FD08(void *);
extern u32 fn_80280BB4(void *, void *);

#if TAK_FN == 0x80213584
void fn_80213584(Application *app)
{
    app->input.slot0x0c();
    fn_80283F7C(app->subsystem);
    if (!(u8)VCALL(lbl_803312F8, 0x1c)) fn_8020F9C8(app);
    app->input.slot0x10();
}
#elif TAK_FN == 0x801042FC
void *fn_801042FC(void *state)
{
    void *config = FIELD(void *, state, 0x1b4);
    return FIELD(void *, lbl_802CD918, FIELD(u32, config, 4) * 0x1c);
}
#elif TAK_FN == 0x800CEB2C
s32 fn_800CEB2C(void)
{
    fn_80260A80();
    if (lbl_802F58A0[1] == -1) { lbl_802F58A0[1] = 0x37; return 1; }
    if (lbl_802F58A0[1] == 0x37) { FIELD(s32, lbl_8033267C, 0xec) = 1; return 2; }
    return 3;
}
#elif TAK_FN == 0x80213140
u32 fn_80213140(void *owner, void *next)
{
    fn_802131A0(owner);
    FIELD(void *, owner, 4) = next;
    if (FIELD(void *, owner, 4)) return VCALL(FIELD(void *, owner, 4), 0x0c);
    return 1;
}
#elif TAK_FN == 0x802131A0
void fn_802131A0(void *owner)
{
    if (FIELD(void *, owner, 4)) {
        s32 result = VCALL(FIELD(void *, owner, 4), 0x14);
        FIELD(void *, owner, 4) = 0;
        if (FIELD(u8, owner, 0x10)) result = -1;
        ((VObject *)owner)->slot0x24(result);
    }
}
#elif TAK_FN == 0x801B91FC
void fn_801B91FC(Header *p)
{
    u32 i;
    if (!(p->flags & 1)) return;
    p->flags |= 4;
    for (i = 0; (u16)i < p->count; ++i) {
        u32 offset = 4 + (u16)i * 4;
        FIELD(u32, p, offset) = (u32)p + FIELD(u32, p, offset);
    }
}
#elif TAK_FN == 0x801B92FC
void *fn_801B92FC(Header *p, u32 index)
{
    u32 offset;
    if (!p) return 0;
    switch (p->flags & 3) {
    case 1: return FIELD(void *, p, 4 + (index & 0xffffff) * 4);
    case 2:
        offset = 8;
        if (p->flags & 8) offset = 16;
        return (u8 *)p + (offset + (index & 0xffffff) * p->size);
    default: return 0;
    }
}
#elif TAK_FN == 0x801B8FD0
void fn_801B8FD0(void)
{
    if (lbl_80322E00.payload_flags & 1) fn_801B9014(lbl_80322E00.payload_value);
    else fn_801B90D0(lbl_80322E00.payload_value);
}
#elif TAK_FN == 0x801C5944 || TAK_FN == 0x801C59A4 || TAK_FN == 0x801C5A04
#if TAK_FN == 0x801C5944
#define NAME fn_801C5944
#elif TAK_FN == 0x801C59A4
#define NAME fn_801C59A4
#else
#define NAME fn_801C5A04
#endif
u32 NAME(Header *p, Header *h, void **out, u32 *size)
{
    fn_801B91FC(p);
    *out = p;
    *size = h->size;
    return 1;
}
#elif TAK_FN == 0x801C5BAC || TAK_FN == 0x801C5C34
#if TAK_FN == 0x801C5BAC
#define NAME fn_801C5BAC
#define PROCESS fn_801C5D28
#else
#define NAME fn_801C5C34
#define PROCESS fn_801C5F1C
#endif
u32 NAME(Header *p, Header *h, void **out, u32 *size)
{
    u32 i;
    fn_801B91FC(p);
    for (i = 0; (u16)i < p->count; ++i) PROCESS(fn_801B92FC(p, (u16)i));
    h->flags &= ~1;
    *out = p;
    *size = h->size;
    return 1;
}
#elif TAK_FN == 0x801B90D0
void fn_801B90D0(u32 amount)
{
    u8 *cursor = lbl_80322E00.cursor;
    u32 remaining = lbl_80322E00.remaining;
    lbl_80322E00.cursor = cursor + amount;
    lbl_80322E00.remaining = remaining - amount;
}
#elif TAK_FN == 0x801B90F4
u32 fn_801B90F4(u32 mode, u32 reset)
{
    if ((u8)reset) { lbl_80322E00.allocation = 0; return 1; }
    if ((u8)mode == 1) {
        if (lbl_80322E00.allocation) fn_802061B8(lbl_80322E00.allocation);
        lbl_80322E00.allocation = 0;
    } else if (!(lbl_80322E00.flags & 8)) {
        fn_80205F64(lbl_80322E00.allocation,
                   (u32)lbl_80322E00.cursor - (u32)lbl_80322E00.allocation);
    }
    return 1;
}
#elif TAK_FN == 0x801B9190 || TAK_FN == 0x801C5A64
#if TAK_FN == 0x801B9190
#define NAME fn_801B9190
#else
#define NAME fn_801C5A64
#endif
u32 NAME(Header *p, Header *h, void **out, u32 *size)
{
#if TAK_FN == 0x801B9190
    fn_801B91FC(p);
#endif
    h->flags &= ~1;
    *out = p;
    *size = h->size;
    return 1;
}
#elif TAK_FN == 0x801B9244
static inline u16 swap16(u16 x) {
    u16 out;
    ((u8 *)&out)[0] = ((u8 *)&x)[1];
    ((u8 *)&out)[1] = ((u8 *)&x)[0];
    return out;
}
static inline u32 swap32(u32 x) {
    u32 out;
    ((u8 *)&out)[0] = ((u8 *)&x)[3];
    ((u8 *)&out)[1] = ((u8 *)&x)[2];
    ((u8 *)&out)[2] = ((u8 *)&x)[1];
    ((u8 *)&out)[3] = ((u8 *)&x)[0];
    return out;
}
void fn_801B9244(Header *p)
{
    u32 i;
    p->count = swap16(p->count);
    p->flags = swap16(p->flags);
    if (!(p->flags & 1)) return;
    p->flags |= 4;
    for (i = 0; (u16)i < p->count; ++i) {
        u32 *entry = &FIELD(u32, p, 4 + (u16)i * 4);
        *entry = swap32(*entry) + (u32)p;
    }
}
#elif TAK_FN == 0x8021311C
u32 fn_8021311C(void *owner, void *next) { fn_802131A0(owner); return 1; }
#elif TAK_FN == 0x80213710
u8 fn_80213710(void *app) { return fn_80211DD8((u8 *)app + 0x478) != 0; }
#elif TAK_FN == 0x80213744
u8 fn_80213744(void *app) { return fn_80282250((u8 *)app + 0x4d8, 0) != 0; }
#elif TAK_FN == 0x80213480
u8 fn_80213480(void *app)
{
    if (!fn_80213710(app)) return 0;
    fn_80213744(app);
    return 1;
}
#elif TAK_FN == 0x800E53C4
u8 fn_800E53C4(void *object) { return lbl_803312FC; }
#elif TAK_FN == 0x800E53CC
void fn_800E53CC(void *object, u8 value) { lbl_803312FC = value; }
#elif TAK_FN == 0x80211ED4
void fn_80211ED4(void *object)
{
    u32 i;
    u8 *walk = (u8 *)object;
    memcpy((u8 *)object + 0x18, (u8 *)lbl_803320E0 + 0x334, 0x30);
    FIELD(u32, object, 0x5c) = 0;
    for (i = 0; i < 4; ++i) {
        void *device = FIELD(void *, walk, 8);
        if (device) VCALL(device, 0x28);
        walk += 4;
    }
}
#elif TAK_FN == 0x80211F54
void fn_80211F54(void *object)
{
    u32 i;
    u8 *walk = (u8 *)object;
    if (FIELD(u8, object, 0x58)) fn_8011DCAC((u8 *)object + 0x48);
    if (FIELD(void *, object, 0x5c)) fn_8011D5E8(FIELD(void *, object, 0x5c));
    for (i = 0; i < 4; ++i) {
        void *device = FIELD(void *, walk, 8);
        if (device) VCALL(device, 0x2c);
        walk += 4;
    }
}
#elif TAK_FN == 0x8020F964
void *fn_8020F964(void *object)
{
    void *allocation;
    FIELD(void *, object, 0) = lbl_802EF19C;
    FIELD(u8, object, 4) = 0;
    allocation = fn_802062A8(0x6c);
    if (allocation) allocation = fn_8017FD08(allocation);
    lbl_80332CA0 = allocation;
    FIELD(u8, object, 0xc) = 0;
    return object;
}
#elif TAK_FN == 0x80213708
u32 fn_80213708(void) { return 1; }
#elif TAK_FN == 0x80280928
u8 fn_80280928(void *object, void *record) { return fn_80280BB4(object, record) != 0; }
#else
#error Select a modeled routine with TAK_FN
#endif
} /* extern "C" */
