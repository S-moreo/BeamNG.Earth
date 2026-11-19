With **Wear strips** (`expWearStrips` / `BNE_WEAR_STRIPS=on`) turned on, the tyre polish and crack strips in the lanes look far too bright and aren't darkened by shadows. Surface v2's overlays (`BNE_SURFACE_V2`: the variation strips, `bne_wear_tread2`, the patch strips and the gravel edge) have the same shadow problem. In a building's shadow the lane stays almost as bright as in the sun, and the strips also cover part of the road paint (half of a crosswalk was missing). I saw this on High Street in Morgantown, WV.

### Cause
The road wear materials (the strips `bne_wear_tread`, `bne_wear_sealed`, `bne_wear_cracks`, v2's `bne_wear_var_01/02`, `bne_wear_tread2`, `bne_wear_patchstrip`, `bne_edge_gravel`, and the spots and crack lines) were the only road surface materials with `translucentZWrite: false`. Every stock road decal they copy (`tread_marks_worn`, `AsphaltRoad_joint_01`, `m_asphalt_cracks_02`), and the stock road surface and line materials on our road mesh (`road_asphalt_2lane`, `line_white`), have it set to true. Without it, the strips got no sun shadow and were drawn over the paint. The old strips were also brighter than stock: the colour was full white where the stock tread marks use 0.7, and there was no AO map. v2's `bne_wear_tread2` already fixed the tint (aa9b5e43), but not the shadows.

### What it does
In `roadwear.materials.json`:
- every road wear material, old and v2 (strips, spots and crack lines), gets `translucentZWrite: true`, the same as the stock decals.
- the three old strips (`bne_wear_tread`, which v2 replaces with `bne_wear_tread2`, and the sealed and alligator crack networks) also get a tint like `bne_wear_tread2`'s and their stock AO maps: `baseColorFactor [0.7, 0.7, 0.7, 1]`, `opacityFactor 0.69` (the stock Utah / East Coast value; `bne_wear_tread2` uses the 0.505 variant). v2's materials keep their own tint and opacity.

In `roadmesh.py`, without v2, a new `_draw_rank` sets the draw order in a road mesh: dirt strips and frontage asphalt first, then the road and its paint, then the wear strips, then the wear spots and crack lines. The strips used to draw before the paint. Now they wear over crosswalks and lines the way real wheel paths do, while patches and cracks still show on top. Since the strips now write depth and sit only 0.2 mm above the paint, the draw order is what decides which one shows. With v2 on, `v2_rank` stays as upstream has it; I'll put the tyre wear over the markings there in a follow-up PR.

With the setting off (the default), the strips aren't drawn. The spots, crack lines and v2 overlays that are still drawn get the depth write, which lets them take shadows. This PR doesn't depend on any other PR.

I also tried `translucentRecvShadows: true`. It made no difference once depth writes were on, so I left it out.

### Screenshots
Same camera and frozen time, before on the left and after on the right.

**Sunset, wear strips (v2 off)**
![Sunset, wear strips (v2 off)](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/tod/3_sunset_close.jpg)

**Crosswalk, noon (v2 off)**
![Crosswalk, noon (v2 off)](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/tod/6_crosswalk_noon_xw.jpg)

**Night under a street lamp (v2 off)**
![Night under a street lamp (v2 off)](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/tod/5_night_streetlamp_lamp.jpg)

**Sunset, surface v2**
![Sunset, surface v2](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/v2/2_sunset_wide.jpg)

**Crosswalk, noon, surface v2**
![Crosswalk, noon, surface v2](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/v2/1_noon_crosswalk.jpg)

**Times Square intersection (Revamped roads off)**
![Times Square intersection (Revamped roads off)](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/perf/intersection_off_dev_vs_branch.jpg)

Brightness of a fixed patch in the close shot (0-255), afternoon sun:
| | sunlit lane | shaded lane | shaded sidewalk |
|---|---|---|---|
| before | 151 | 132 | 60 |
| after | 152 | 41 | 64 |

### Performance
No measurable cost. I lifted the fps cap and measured frame time over 40 s per state with the camera still, in A/B/A/B order. The GPU was about 99% busy, so frame time is GPU time:
- downtown wide view: 5.06 / 5.09 ms before, 5.07 / 5.07 ms after (p95 5.23-5.24 ms both)
- High Street at noon: 5.45 / 5.43 ms before, 5.48 / 5.46 ms after (p95 5.55-5.58 vs 5.58-5.61 ms)

That's at most +0.02 ms (0.4%), within the noise. With v2 on, the same test gave 5.06 / 5.05 ms before vs 5.04 / 5.06 ms after downtown, and 5.49 / 5.48 vs 5.52 / 5.50 ms on High Street (p99 about the same): at most +0.03 ms, within the noise. The draw order change adds no draw calls: it's the same primitives in a different order.

Times Square, NYC, with the full Revamped roads set (current dev, v2 on), frame time at noon with the fps cap off: street level 7.25 → 7.33 ms (5 pairs, +0.09 ms, about 1%), high wide view 7.28 → 7.24 ms, dense intersection 7.80 → 7.80 ms. GPU 99% busy. With Revamped roads off, all three views were within 0.13 ms, which is inside the drift between server swaps.

### Testing
- `test_roadwear` (with a new test for the draw order), `test_roadmesh`, `test_markings` and `test_plazas` pass.
- In game with `BNE_SURFACE_V2=on` (before: upstream dev d1122409, after: this branch, the same cameras with time frozen): at sunset the variation, tyre wear and patch strips now fall into the building shadows. Before, they stayed brightly lit and made the road look sunlit and blotchy. At noon the zebra stripes are clean where the variation strips used to dirty them. The gravel edges, patches, markings and kerb pads all show, and repeated frames show no flicker where the gravel edge (0.5 mm lower) meets a variation strip. Under a street lamp it's nearly the same, a touch darker on the strips.
- Spots (manhole, patches, crack lines), v2 off and on: the spots and crack lines darken in building shadows. There's no flicker, and the paint around them stays whole. Frame time is within 0.03 ms.
- In game (Linux, dev build) with the strips on and v2 off: shadows now land on the strips in the morning, at noon and at sunset. At night they're no longer pale streaks under a street lamp. The crosswalks are complete, the wear shows faintly over them, and patches and crack lines still draw over the strips. I saw no flicker where the paint meets a strip.
