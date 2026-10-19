# OICD demo script (five minutes)

_Independent reconstruction from public information. Not affiliated with or endorsed by Lightmatter. Product names belong to their owners._

Start the engine and the explorer with `./scripts/dev.sh`, open http://localhost:5173 and keep the footer in view: it carries the independence line on every screen. Every number below is shown in the explorer with its class badge; the class is repeated here in brackets.

## 0:00 to 0:40, the rack and what a PASS means

The explorer opens on OICD-R64, a reference rack that OICD designed from public parts [SYNTHETIC design, not a Lightmatter configuration]: an ORv3 frame (600 × 1068 × 2286 mm [PUBLISHED_SPEC]), 16 XPU trays, 8 switch trays and two power shelves, single-tier, 8192 BiDi links [INFERENCE]. Hover a part: the Inspector shows each dimension with its class, so nobody mistakes a drawn box for a datasheet. Toggle the SCHEMATIC tint (T) to see which parts are drawn rather than measured.

## 0:40 to 1:30, the reference-plane flip

The physics overlay reports the rack's worst optical path on the draft IEEE 802.3dj 200G DR budget [PROPOSED_STANDARD, draft]: XPU engine, vClick, 0.5 m tray fiber, PRIZM TMT blind mate, 3 m rack fiber, switch-tray connector, 0.5 m, vClick, switch engine. With the vClick's 1.5 dB [VENDOR_CLAIM] counted in the channel, M_net is −1.0016 dB: EXCLUDED [INFERENCE]. At "below 1 dB" [THIRD_PARTY] it is −0.0016 dB, still EXCLUDED. Click "vClick inside the module": +1.9984 dB, NOT_EXCLUDED [INFERENCE]. The physics did not change; the reference-plane definition did. That is the rack's headline (model card §14.9).

## 1:30 to 2:00, rack yield returns to 4.7σ

Open the Physics tab. With 8192 independent links, a per-link yield of 0.9999 gives a rack yield of 0.4408, and 0.99999 gives 0.9213; a 99 % rack needs 0.99999877 per link, about 4.712σ one-sided [INFERENCE]. Statistical design at rack scale ends up close to worst-case design.

## 2:00 to 2:50, the 204.8 Tbps question and the laser count

Double-click the switch trays (semantic zoom: the breadcrumb now reads Rack › Switch tray). The Inference tab shows two readings of "204.8 Tbps": per direction (H_dir: 1024 lanes, four Guide DR modules, matching Lightmatter's Guide DR release [VENDOR_CLAIM]) or aggregate (H_agg: 512 lanes per direction, two modules, matching Counterpoint's "two" and INE's "aggregate" [THIRD_PARTY]). The support matrix shows which claims each hypothesis agrees with; the tray-height sources (1 RU against 2 RU) stay a recorded CONFLICT. At rack scale the single-tier design needs 64 Guide DR modules [INFERENCE].

## 2:50 to 3:30, the engine

Double-click a BiDi engine. The Passage L20 package is 37.5 × 27.6 × 4.55 mm on the OFC 2026 slide [VENDOR_CLAIM]; the product page says 37.5 × 26.4 mm, kept as a CONFLICT and one click away in the Inspector. Press E to explode the EIC, PIC and fiber-array unit, S for a hatched section, M to measure the outline (37.5 mm). The tour (Tour button) walks the facts: 30 W over 6.4 Tbps is 4.6875 pJ/bit [INFERENCE], consistent with the page's 5 pJ/bit; direction B at 1331 nm lies 13.5 nm above the draft DR range [INFERENCE], so "DR compatible" cannot mean DR wavelength compliance in both directions.

## 3:30 to 4:30, interleaved BiDi and the ring FSR

Open the BiDi link sub-scene: two engines on one fiber, direction A in blue and B in orange (false color; O-band light is invisible). Lower the diplexer isolation from the case's 25 dB [SYNTHETIC] to 0 dB and the ghost pulse (the engine's own reflected light) appears. Then zoom into the PIC and the ring. In the Spectrum tab, interleaving the two directions moves the nearest co-directional neighbor from 200 to 400 GHz: −15.846 dB becomes −21.781 dB for a Q 3500 ring [INFERENCE from PEER_REVIEWED inputs], 5.935 dB of isolation. With the OFC 2025 ring's 1.8 THz FSR (H_fsr18), seven of the eight receive rings have an image exactly on a local transmit channel and co-directional channels 8 or 10 slots away sit one slot from an image, so the worst receive channel (3) sees 0.3710 dB of crosstalk penalty; with a 3.2 THz FSR (H_fsr32) the worst (7) sees 0.0944 dB [INFERENCE]. A 1.8 THz ring erases most of the interleaving gain; the 16λ BiDi link wants an FSR of at least 3.2 THz.

## 4:30 to 5:00, close

Every number came from the engine, with its class; Export downloads the JSON the explorer showed. The per-product twin pages (docs/twin/), the public spec sheet and the paper (docs/paper/main.md) carry the same numbers and the open questions.
