With **Wear strips** on (`BNE_WEAR_STRIPS=on`), the manhole covers (`bne_spot_manhole`) look like bright, near-white discs. Ours uses the same textures as Italy's stock `italy_ground_parts` decal, but it left out three of that decal's settings:
- `metallicFactor 0.5`: without it, the metallic map ran at full strength, so the cast iron read as polished metal and caught the sky
- its AO map (`t_manhole_01_decal_ao`), which darkens the grate slots and the rim
- `alphaTest` with `alphaRef 114`, which gives the cover a hard edge

This PR adds all three. The potholes and fallen leaves also get their stock AO maps (`t_asphalt_pothole_decal_ao`, `t_fallen_leaves_decal_ao`), which their stock decals use. Only `roadwear.materials.json` changes, and it doesn't depend on any other PR.

### Screenshots
Before on the left, after on the right, wear strips on. These shots were taken together with a separate change I'm preparing that makes the road wear take shadows, so the shadow edge shot also shows that change:

**Manhole, noon**
![Manhole, noon](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/spots/1_noon_mh_close_v2off.jpg)

**Manhole on a shadow edge**
![Manhole on a shadow edge](https://raw.githubusercontent.com/S-moreo/BeamNG.Earth/pr-images/tiremarks-2026-11-19/tiremarks/spots/2_afternoon_shadow_edge_mh_macro_v2off.jpg)

### Performance
Within noise: 0.00-0.03 ms per frame, A/B/A/B over 40 s samples on two still views, with the GPU 99% busy. Measured together with the shadow change.

### Testing
In game (Linux, dev build), surface v2 off and on, together with the shadow change: the cover is now a mid-grey metal, slightly lighter than the asphalt in full sun. The alpha test leaves no hard square or black edges, and there's no flicker. On its own, this PR changes the cover's colour and metal the same way, but the cover still won't darken in shadow until the shadow change lands.
