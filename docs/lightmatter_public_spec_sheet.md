# Lightmatter public spec sheet (as reconstructed by OICD)

_Independent reconstruction from public information. Not affiliated with or endorsed by Lightmatter. Product names belong to their owners._

One reading document generated from the catalog by `scripts/make_twin_docs.py`: every public number with its class (VENDOR_CLAIM, PEER_REVIEWED, THIRD_PARTY, ...) and source. Derived values, checks and hypotheses are in the per-product pages under docs/twin/.

## 16λ BiDi link (Passage EVK50)

Single-fiber bidirectional WDM link with interleaved wavelength grids and microring transceivers (vendor descriptions).

| quantity | value | class | source |
| --- | --- | --- | --- |
| Bit error rate without FEC, 16-lambda BiDi link | ≤ 1e-09 BER | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Throughput per fiber of the 16-lambda bidirectional link (both directions combined; slide 5 shows 8 wavelengths per direction, so about 400 Gbps each way by inference) | 800 Gbps | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Center of the 16-wavelength grid | ≈ 1310 nm | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| Channel loss of the 16-lambda BiDi link demo (1 km fiber plus 6 connectors) | 3 dB | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Connectors in the 16-lambda BiDi link channel | 6 | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Photonics energy per bit, 16-lambda BiDi link (scope, PIC and/or laser, not defined on slide) | 2.6 pJ/bit | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| EVK50 bandwidth per fiber in each direction: 400 Gbps Tx + 400 Gbps Rx = 800 Gbps per fiber strand (16 wavelengths, 8 each way) | 400 Gbps | VENDOR_CLAIM | [lm_web_evk50](https://lightmatter.co/products/passage-evk50/) |
| EVK50 'Total link efficiency' including laser (photonics + Guide laser; excludes SerDes per lm_blog_seeing) | 2.6 pJ/bit | VENDOR_CLAIM | [lm_web_evk50](https://lightmatter.co/products/passage-evk50/) |
| EVK50 modulation format and lane rate (Technical Specifications table) | 56 Gbps | VENDOR_CLAIM | [lm_web_evk50](https://lightmatter.co/products/passage-evk50/) |
| EVK50 as run live at OFC 2026: 4+4 band-interleaved BiDi, 8 wavelengths per fiber at 50 Gbps each, 200 m SMF; bandwidth per fiber in each direction | 200 Gbps | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| Fiber length of the 16-lambda BiDi link demo (single-mode fiber spool) | 1 km | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Wavelengths on one single-mode fiber in the 16-wavelength BiDi link (8 per direction; odd λ1..λ15 one way, even λ2..λ16 the other) | 16 | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| Per-direction wavelength assignment: side A transmits even-indexed λ0-λ14 (WDM Laser Module A) and side B transmits odd-indexed λ1-λ15 (WDM Laser Module B), interleaved on one fiber. That is 8 per direction, a count inferred from the listed indices. | text | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Microring modulators on the Passage chip for the 16-wavelength BiDi link | 8 | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| Data rate per wavelength (8 x 50 Gbps = 400 Gbps per direction; 800 Gbps per fiber over 1 km) | 50 Gbps | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| Spacing between channels travelling in the same direction | 400 GHz | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| XSR SerDes energy per bit, 16-lambda BiDi link | 2 pJ/bit | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| Spacing between adjacent transmit and receive (opposite-direction) channels | 200 GHz | VENDOR_CLAIM | [lm_blog_doubling](https://lightmatter.co/blog/doubling-down-worlds-first-16-%CE%BB-single-fiber-bidirectional-link-for-ai/) |
| Wall-plug energy per bit of the HOTI 2025 16-wavelength BiDi Passage link = 2.6 pJ/bit photonics + Guide laser + ~2 pJ/bit off-the-shelf XSR SerDes | 4.6 pJ/bit | VENDOR_CLAIM | [lm_blog_seeing](https://lightmatter.co/blog/seeing-is-believing-a-technical-deep-dive-into-lightmatters-hardware/) |
| Wavelengths on the bidirectional fiber (both directions together) | 16 | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |

Details: [docs/twin/bidi_16lambda.md](twin/bidi_16lambda.md).

## Guide, Guide 1 and Guide DR

External multi-wavelength laser engines: Guide (VLSP), Guide 1 (DWDM for microring transmitters) and Guide DR (liquid-cooled laser NIC for 200G DR lanes).

| quantity | value | class | source |
| --- | --- | --- | --- |
| bandwidth supported per laser module (NPO and CPO applications) | ≤ 51.2 Tbps | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| Guide data bandwidth supported per module | 51.2 Tbps | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| failure-free device hours cited for Guide lasers in Lightmatter validation systems (analyst relaying a vendor claim) | ≈ 2000000 h | THIRD_PARTY | [futurum_ocp26](https://futurumgroup.com/insights/lightmatter-and-flex-bring-2048-tbps-co-packaged-optics-into-open-racks/) |
| discrete ELSFP modules for 100 Tbps of laser supply in 4RU | 18 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| conventional ELSFP modules that the same 100 Tbps would require | ≈ 18 | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| rack space occupied by the ~18 ELSFP modules | 4 RU | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| discrete ELSFP laser modules needed for 100 Tbps (HOTI26) | 16 | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| Guide fiber outputs per module | 32 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| Guide VLSP reliability (FIT), with self-healing | 0.1 FIT | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| Guide VLSP frequency accuracy | 3 GHz | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| Guide wavelength (frequency) accuracy window shown in OFC 2026 data | 15 GHz | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| offset between the two interleaved 400 GHz grids | 200 GHz | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| spacing of each of the two interleaved wavelength grids (bidirectional links) | 400 GHz | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| lasers per Guide VLSP chip | ≥ 128 | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| Guide modules for 100 Tbps of laser supply in 1RU | 4 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| Guide design target: microring modulator transmitters | text | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| Guide VLSP optical power accuracy | 0.25 dB | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| optical output power per fiber (power kind, average or OMA, not stated; CW source) | ≥ 100 mW | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| Guide optical power per output fiber | ≥ 100 mW | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| optical power uniformity across the channels in fiber | ≤ 0.1 dB | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| switch bandwidth enabled by the first-generation Guide validation platform in a 1RU chassis | 100 Tbps | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| accuracy of the 200 GHz interleave offset (± tolerance magnitude) | ≤ 20 GHz | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| laser roadmap wavelength count ('and beyond' after 64) | 32.5 | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| wavelengths generated with multiplexing by the Guide light engine (validation platform) | 16 | VENDOR_CLAIM | [lightmatter_guide_2026](https://lightmatter.co/press-release/lightmatter-introduces-guide-light-engine-for-ai-featuring-vlsp-technology/) |
| Guide VLSP wavelengths (multi-color) | ≥ 64 | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| O-band wavelength grid center | 1310 nm | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| supported I/O per Guide 1 module | 51.2 Tbps | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| channel spacing (spec table) | 200 GHz | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| control interface: CMIS 5.3 over I2C / I3C | text | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| ELSFP light sources whose output one Guide 1 replaces | 9 | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| output fibers, single package | 16 | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| output fibers, stacked configuration | 32 | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| function: continuous-wave (CW) laser source for DWDM | text | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| scalable output from a single package (low end) to a stacked configuration (high end) | 2.55 W | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| optical output power, single package | 1.6 W | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| optical output power, stacked | ≤ 3.5 W | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| optical output power per fiber | ≥ 100 mW | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| optical output power per wavelength | 13 mW | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| optical output power per module | 3.35 W | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| wavelength precision maintained by the integrated controller ('sub-GHz', i.e. below 1 GHz) | ≤ 1 GHz | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| wavelength stability (± tolerance magnitude) | ≤ 20 GHz | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| multiplexed wavelengths per fiber (spec table; 'scales to 16') | 8 | VENDOR_CLAIM | [lm_web_guide1](https://lightmatter.co/products/guide-1/) |
| thermal environment: ASHRAE A2 | text | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| supported band plans: 1311 nm UniDi, 1311/1331 nm BiDi, 8λ CWDM; custom up to 16λ DWDM | ≤ 16 | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| total bandwidth powered by one Guide DR LNIC | 51.2 Tbps | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| optical output connectors per module (SNMT-8) | 8 | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| rack density relative to conventional ELSFPs | ≈ 4 | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| output fibers per module | ≤ 64 | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| form factor: Laser Network Interface Card (LNIC) built to OCP NIC 3.0 dimensions | text | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| wavelength range A | 1311 nm | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| wavelength range B | 1331 nm | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| lane rate driven by the module ('200G') | 200 Gbps | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| lanes driven per module | 256 | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| lasers on the Guide DR chip (Counterpoint) | 128 | THIRD_PARTY | [counterpoint_nvlinkfusion](https://counterpointresearch.com/en/insights/lightmatter-joins-nvlink-fusion-club) |
| lasers per Guide DR LNIC module | 64 | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| cooling: liquid-cooled cold plate package | text | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| maximum Guide DR LNICs in one 1RU switch tray (product page) | ≤ 8 | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| Guide DR modules used for a 204.8 Tbps 1RU switch tray (May 2026 release) | 4 | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| total optical output power per module | 12.8 W | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| optical power supplied per fiber | 200 mW | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| availability: sampling start | text | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| 1RU switch tray bandwidth with four Guide DR modules | ≤ 204.8 Tbps | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| 1RU switch tray bandwidth with eight Guide DR LNICs (product page) | ≤ 409.6 Tbps | VENDOR_CLAIM | [lm_web_guidedr](https://lightmatter.co/products/guide-dr/) |
| Guide DR units needed to power a 100T switch (Counterpoint) | 2 | THIRD_PARTY | [counterpoint_nvlinkfusion](https://counterpointresearch.com/en/insights/lightmatter-joins-nvlink-fusion-club) |

Details: [docs/twin/guide_family.md](twin/guide_family.md).

## Microring transmitter and receiver (OFC 2025)

Monolithic O-band microring modulator and receiver with integrated driver and front end (peer-reviewed paper; talk slides are vendor claims).

| quantity | value | class | source |
| --- | --- | --- | --- |
| Total die area of the Tx+Rx circuits (MRM + driver 2.8e-3 mm2; MRR + PD + AFE 3.2e-3 mm2) | 0.006 mm2 | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Operating band of the MRMs and MRRs (design); measured spectra in Fig. 1(e) span about 1302-1316 nm | text | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Tx+Rx energy per bit excluding laser at 56 Gbps (talk rounds to 1.5 pJ/bit) | 1.51 pJ/bit | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Free spectral range of the MRMs and MRRs (design value) | 1.8 THz | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Integrated heater tuning efficiency (MRM) | 0.44 nm/mW | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Max NRZ rate of the monolithic microring Tx+Rx with integrated driver and analog front end; 64 Gbps needed 3-tap software Rx FFE with BER < 10^-12 only inferred on the sampling scope; open eye without equalization up to 56 Gbps | ≤ 64 Gbps | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| MRM modulation insertion loss in the Tx+Rx test (input optical power to the MRM about 4 dBm) | ≈ 4.9 dB | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| MRM electro-optic 3 dB bandwidth at -1 V bias (spread ±2 GHz) | ≈ 30.9 GHz | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| MRM extinction ratio, stated as voltage-dependent, read from the Fig. 1(e) spectra (no modulated ER at the 1.3 Vpp drive is given) | ≥ 18 dB | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| MRM quality factor (loaded or intrinsic not stated; same table: tuning efficiency 50 pm/V, EO bandwidth > 30 GHz) | 3500 | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Receiver microring (MRR) insertion loss (talk table; which path is not specified) | 0.1 dB | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Minimum received OMA (receiver sensitivity) at 56 Gbps NRZ, PRBS9, BER < 10^-12, with 4-tap FFE on the BERT (OMA, not average power) | −9 dBm | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Minimum received OMA at 32 Gbps NRZ, PRBS9, BER < 10^-12, no equalization | −11 dBm | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Ge photodetector 3 dB bandwidth at -1 V bias | 56 GHz | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| PD electro-optic bandwidth per the OFC talk (bias not stated) | ≥ 46 GHz | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Ge PD responsivity (table value; the slide's responsivity histogram spans about 0.88 to 1.04 A/W, so not every device exceeds 0.9; wavelength not stated) | ≥ 0.9 A/W | VENDOR_CLAIM | [lm_ofc25_talk](https://lightmatter.co/wp-content/uploads/2025/04/OFC-talk_Reza.pdf) |
| Tx+Rx power consumption excluding the laser (one wavelength, 56 Gbps) | 84.4 mW | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| Fabrication platform: GF 45SPCLO (45 nm CMOS silicon photonics, monolithic) | text | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |
| WDM plan the FSR is designed for: 8 wavelengths at 200 GHz spacing | 200 GHz | PEER_REVIEWED | [lm_ofc25_paper](https://lightmatter.co/wp-content/uploads/2025/04/OFC-2025-submission.pdf) |

Details: [docs/twin/microring_ofc25.md](twin/microring_ofc25.md).

## OCP 2026 CPO switch and XPU trays

An ORv3 CPO switch tray built with Flex and an XPU scale-up tray, both with Passage BiDi engines and Guide DR lasers.

| quantity | value | class | source |
| --- | --- | --- | --- |
| rack faceplate density gain vs conventional ELSFP lasers and unidirectional fiber harnesses | 3 | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| optical fibers to route (cited as a CPO challenge; not tied to a specific tray) | 1925 | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| NOT DISCLOSED (absence confirmed by full-text search): fibers per Passage engine in the trays | text | VENDOR_CLAIM (not verified) | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| NOT DISCLOSED (absence confirmed by full-text search): per-lane data rate in the OCP 2026 switch and XPU trays | text | VENDOR_CLAIM (not verified) | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| NOT DISCLOSED (absence confirmed by full-text search): tray, engine or laser power | text | VENDOR_CLAIM (not verified) | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| NOT DISCLOSED (absence confirmed by full-text search): switch ASIC in the 204.8 Tbps tray | text | VENDOR_CLAIM (not verified) | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| NOT DISCLOSED (absence confirmed by full-text search): wavelengths or wavelength count used in the trays | text | VENDOR_CLAIM (not verified) | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| both trays based on ORv3 and MHS | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| XPU tray uses Corning expanded-beam PRIZM TMT connector technology | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| vClick incorporates SENKO SEAT detachable interface and Metallic Pic Coupler (MPC) | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| CPO switch tray bandwidth (developed with Flex as a production validation system) | 204.8 Tbps | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| switch tray bandwidth described as aggregate (IN Electronics) | 204.8 Tbps | THIRD_PARTY | [ine_ocp26](https://www.inelectronics.co.uk/lightmatter-integrates-optical-engines-into-open-rack-hardware/) |
| Passage CPO BiDi engines in the switch tray | 8 | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| switch tray laser source: Guide DR laser modules (count not stated in the release) | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| Guide DR modules in the 1RU switch tray (Counterpoint) | 2 | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| Guide DR modules for a 204.8 Tbps 1RU switch tray (Lightmatter, May 2026) | 4 | VENDOR_CLAIM | [lm_pr_guidedr](https://lightmatter.co/press-release/lightmatter-unveils-guide-dr-industry-first-liquid-cooled-laser-nic-that-quadruples-rack-density/) |
| CPO switch tray height | 1 RU | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| switch tray cooling: liquid-cooled chassis | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| accelerator ASICs in the XPU tray | 4 | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| XPU tray: engines and Guide DR modules blind mate as they slide into the rack | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| XPU tray combined scale-up bandwidth | 102.4 Tbps | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| CPUs in the XPU tray | 2 | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| XPU tray uses DC-MHS infrastructure from an unnamed major ODM | text | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| BiDi Passage CPO engines in the XPU tray | 4 | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |
| Guide DR modules in the 2RU XPU server (Counterpoint) | 2 | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| XPU server height (Counterpoint) | 2 RU | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| XPU tray height (Futurum) | 1 RU | THIRD_PARTY | [futurum_ocp26](https://futurumgroup.com/insights/lightmatter-and-flex-bring-2048-tbps-co-packaged-optics-into-open-racks/) |
| XPU (compute) tray height (IN Electronics) | 2 RU | THIRD_PARTY | [ine_ocp26](https://www.inelectronics.co.uk/lightmatter-integrates-optical-engines-into-open-rack-hardware/) |
| XPU tray height (lightmatter.com copy of the release) | 2 RU | VENDOR_CLAIM | [lm_pr_openrack](https://lightmatter.com/press-release/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners/) |
| both trays in 1 RU height (lightmatter.com copy, paragraph 2) | 1 RU | VENDOR_CLAIM | [lm_pr_openrack](https://lightmatter.com/press-release/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners/) |
| XPU tray height (PR Newswire copy) | 1 RU | VENDOR_CLAIM | [lightmatter_openrack_2026](http://www.prnewswire.com/news-releases/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners-302906361.html) |

Details: [docs/twin/ocp_trays.md](twin/ocp_trays.md).

## Passage L20

Unified optical engine for near-package and on-board optics with two-wavelength BiDi on 200G lanes, and the bidirectional CPX engine (vendor descriptions).

| quantity | value | class | source |
| --- | --- | --- | --- |
| Passage L20 CPX total bandwidth (6.4 Tbps transmit + 6.4 Tbps receive) | 12.8 Tbps | VENDOR_CLAIM | [lm_pr_cpx](https://lightmatter.com/press-release/lightmatter-joins-open-cpx-msa-introduces-the-industrys-first-bidirectional-cpx-optical-engine/) |
| Passage L20 CPX evaluation kit shipping date | text | VENDOR_CLAIM | [lm_pr_cpx](https://lightmatter.com/press-release/lightmatter-joins-open-cpx-msa-introduces-the-industrys-first-bidirectional-cpx-optical-engine/) |
| Passage L20 CPX optical lanes per direction | 32 | VENDOR_CLAIM | [lm_pr_cpx](https://lightmatter.com/press-release/lightmatter-joins-open-cpx-msa-introduces-the-industrys-first-bidirectional-cpx-optical-engine/) |
| Passage L20 CPX lane line rate (PAM4) | 212.5 Gbps | VENDOR_CLAIM | [lm_pr_cpx](https://lightmatter.com/press-release/lightmatter-joins-open-cpx-msa-introduces-the-industrys-first-bidirectional-cpx-optical-engine/) |
| Passage L20 CPX reach over single-mode fiber | ≥ 500 m | VENDOR_CLAIM | [lm_pr_cpx](https://lightmatter.com/press-release/lightmatter-joins-open-cpx-msa-introduces-the-industrys-first-bidirectional-cpx-optical-engine/) |
| L20 availability date shown on HOTI26 slide | text | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| L20 form factor: BGA ball count (product page) | 1827 | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 two-wavelength bidirectional transmission, as reported by DCD | text | THIRD_PARTY | [lightmatter_l20_2026](https://www.datacenterdynamics.com/en/news/lightmatter-unveils-passage-l20-photonic-interconnect-announces-vclick-optics-offering-for-high-volume-cpo-manufacturing/) |
| L20 transmission: 2 BiDi wavelengths, 1311 nm and 1331 nm; IEEE 802.3dj, DR compatible | text | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 aggregate bandwidth (Tx + Rx) | 12.8 Tbps | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| L20 optical bandwidth as reported by DCD | 6.4 Tbps | THIRD_PARTY | [lightmatter_l20_2026](https://www.datacenterdynamics.com/en/news/lightmatter-unveils-passage-l20-photonic-interconnect-announces-vclick-optics-offering-for-high-volume-cpo-manufacturing/) |
| L20 total bandwidth, each direction | 6.4 Tbps | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 cooling: cold plate, A2 ASHRAE compliant | text | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 data fibers (Corning CPO Flexconnect) | 32 | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 energy per bit stated beside max TDP (Business Wire copy) | 3 pJ/bit | VENDOR_CLAIM | [lm_pr_l20_bw](https://www.businesswire.com/news/home/20260311102347/en) |
| L20 power efficiency (product page) | 5 pJ/bit | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 (NPO/OBO) power efficiency (OFC 2026 Yole slides) | 5 pJ/bit | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| reduction in fiber management requirements vs unidirectional DR optics | 50 % | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 BiDi data fibers (each carries TX and RX) | 32 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 form factor: BGA pin count (BiDi variant) | 2000 | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 form factor height (H of L x W x H) | 4.55 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| BiDi wavelength A | 1311 nm | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| BiDi wavelength B | 1331 nm | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 optical data rate per lane (DR) | 200 Gbps | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| external laser feed per L20: 1 ELSFP with 8 laser fibers | 8 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 package length (product page) | 37.5 mm | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 form factor length (L of L x W x H) | 37.5 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 optical ports per module | 32 | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| pluggable energy per bit, high end | 20 pJ/bit | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| pluggable energy per bit, low end | 17 pJ/bit | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| pluggable optics power efficiency (comparison) | 18.5 pJ/bit | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| comparison pluggable optics height (H of L x W x H) | 15.5 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| comparison pluggable optics length (L of L x W x H) | 108.8 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| comparison pluggable optics width (W of L x W x H) | 22.93 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 optical ports at 200 Gbps per lane DR, as reported by DCD | 32 | THIRD_PARTY | [lightmatter_l20_2026](https://www.datacenterdynamics.com/en/news/lightmatter-unveils-passage-l20-photonic-interconnect-announces-vclick-optics-offering-for-high-volume-cpo-manufacturing/) |
| power savings of L20 vs pluggable optics | ≤ 75 % | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 sampling start | text | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 SerDes line rate as reported by DCD | 212.5 Gbps | THIRD_PARTY | [lightmatter_l20_2026](https://www.datacenterdynamics.com/en/news/lightmatter-unveils-passage-l20-photonic-interconnect-announces-vclick-optics-offering-for-high-volume-cpo-manufacturing/) |
| L20 SerDes line rate (PAM4) | 212.5 Gbps | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 SerDes rate as stated on HOTI26 slide | 200 Gbps | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| switch application bandwidth per direction with 18 x L20 | ≤ 115.2 Tbps | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 engines in the switch example | 18 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 thermal design power, maximum | ≤ 30 W | VENDOR_CLAIM | [lm_pr_l20](https://lightmatter.co/press-release/lightmatter-expands-photonic-interconnect-roadmap-with-passage-l20-unified-optical-engine-for-npo-and-obo-applications/) |
| L20 maximum TDP as reported by DCD | ≤ 30 W | THIRD_PARTY | [lightmatter_l20_2026](https://www.datacenterdynamics.com/en/news/lightmatter-unveils-passage-l20-photonic-interconnect-announces-vclick-optics-offering-for-high-volume-cpo-manufacturing/) |
| L20 thermal design power, maximum (HOTI26 slide) | ≤ 30 W | VENDOR_CLAIM | [lm_hoti26](https://lightmatter.com/wp-content/uploads/2026/08/Nick-Harris_Lightmatter_The-Interconnect-Foundation-for-High-Performance-AI-Training-and-Inference_HotI2026.pdf) |
| L20 volume reduction vs pluggable optics | ≈ 88 % | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 volume reduction vs OSFP (product page) | 88 % | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 package width (product page) | 26.4 mm | VENDOR_CLAIM | [lm_web_l20](https://lightmatter.co/products/passage-l20/) |
| L20 form factor width (W of L x W x H) | 27.6 mm | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| XPU application bandwidth per direction with 6 x L20 | 38 Tbps | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |
| L20 engines in the XPU example | 6 | VENDOR_CLAIM | [lm_yole_ofc26](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-Yole-Nikhil-Kumar.pdf) |

Details: [docs/twin/passage_l20.md](twin/passage_l20.md).

## Passage L200 and L200X

Co-packaged optics chiplet with 3D-integrated SerDes for edgeless I/O beside an XPU die, and the Passage EVK100 16-wavelength link (vendor descriptions).

| quantity | value | class | source |
| --- | --- | --- | --- |
| EVK100 pre-FEC BER target | ≤ 1e-05 BER | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| EVK100 aggregate bandwidth (spec table: 'Port count 2 fibers', 'Throughput modes 1.6 Tbps UniDi') | 3.2 Tbps | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| EVK100 throughput per fiber, unidirectional (separate Tx and Rx fibers) | 1.6 Tbps | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| EVK100 link energy efficiency at 112G PAM4, including laser (hero tile calls it a target) | 3.2 pJ/bit | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| Laser energy per bit, PASSAGE 100 EVK (EVK100) 16-lambda 106G PAM4 unidirectional link (slide does not name L200/L200X) | 1.1 pJ/bit | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| PIC energy per bit, PASSAGE 100 EVK (EVK100) 16-lambda 106G PAM4 unidirectional link, 1600 Gbps per fiber (slide does not name L200/L200X) | 1.8 pJ/bit | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| PASSAGE 100 EVK energy per bit, PIC + laser (OFC 2026 talk) | 3 pJ/bit | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| EVK100 DWDM grid centre wavelength | 1310 nm | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| EVK100 DWDM channel spacing | 200 GHz | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| EVK100 lane rate per wavelength (PAM4), product page | 112 Gbps | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| PASSAGE 100 EVK lane rate per wavelength, 16-lambda unidirectional PAM4 link (OFC 2026 talk) | 106 Gbps | VENDOR_CLAIM | [lm_ofc26_kumar](https://lightmatter.co/wp-content/uploads/2026/04/OFC-2026-16-lambda-Bidi_PAM4-Nikhil-Kumar.pdf) |
| EVK100 DWDM wavelengths per fiber | 16 | VENDOR_CLAIM | [lm_web_evk100](https://lightmatter.co/products/passage-evk100/) |
| Availability year of L200 and L200X | 2026 year | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| Bandwidth per fiber: 800 Gbps / 1.6 Tbps (by list order presumably L200 / L200X; direction not stated) | 1200 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| bandwidth per fiber, first figure | 800 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| bandwidth per fiber, second figure | 1600 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| I/O topology: edgeless I/O (area-array I/O across the die, enabled by 3D stacking) | text | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| EIC (UCIe and SerDes chiplet) supplier: Alphawave Semi; EIC 3D-integrated on the Passage PIC (chip-on-wafer) | text | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| Ownership of the L200 EIC/SerDes partner: Alphawave Semi is now part of Qualcomm Technologies (stated 2026-03-11) | text | VENDOR_CLAIM | [lm_pr_1p6t](https://lightmatter.com/press-release/lightmatter-achieves-record-1-6-tbps-per-fiber-to-accelerate-ai-optical-interconnect/) |
| L200 total optical bandwidth per engine (Tx+Rx) | 32 Tbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| L200 lane rate and modulation (56 Gbps NRZ) | 56 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| L200X total optical bandwidth per engine (Tx+Rx) | 64 Tbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| L200X lane rate, PAM4: two supported rates, 106 and 112 Gbps (not a continuous range) | 109 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| Total I/O bandwidth per chip package (multiple L200s per package) | ≥ 200 Tbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| Per-package total I/O target for Passage L-Series, stated in 2026 ('clear path to'; Qualcomm EVP quote; release body: 'on track to deliver 100 Tbps and beyond') | 100 Tbps | VENDOR_CLAIM | [lm_pr_1p6t](https://lightmatter.com/press-release/lightmatter-achieves-record-1-6-tbps-per-fiber-to-accelerate-ai-optical-interconnect/) |
| Equivalent number of pluggable optical transceivers (bandwidth) per L200 | 40 | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| SerDes per engine ('Optically-optimized multi-rate/multi-protocol'), listed for both L200 and L200X | 320 | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| UCIe die-to-die interface rate (per-lane basis not stated) | 32 Gbps | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| WDM wavelengths per waveguide/fiber (L200 and L200X) | 16 | VENDOR_CLAIM | [lm_pr_l200](https://lightmatter.co/press-release/lightmatter-announces-passage-l200-the-fastest-co-packaged-optics-for-ai/) |
| Energy efficiency, '(Optical)' (scope, e.g. laser or SerDes included, not defined) | ≤ 5 pJ/bit | VENDOR_CLAIM | [lm_web_l200](https://lightmatter.co/products/l200/) |
| Modulation and lane rates per product page: PAM4 at 56G and 112G | 84 Gbps | VENDOR_CLAIM | [lm_web_l200](https://lightmatter.co/products/l200/) |
| Total bandwidth per package (Tx+Rx), product page metadata | 256 Tbps | VENDOR_CLAIM | [lm_web_l200](https://lightmatter.co/products/l200/) |
| Total I/O per chip, visible body of the L200 product page | ≥ 200 Tbps | VENDOR_CLAIM | [lm_web_l200](https://lightmatter.co/products/l200/) |
| Direct drive reach (DR/FR) | 1005 m | VENDOR_CLAIM | [lm_web_l200](https://lightmatter.co/products/l200/) |

Details: [docs/twin/passage_l200.md](twin/passage_l200.md).

## Passage M1000

3D photonic superchip: a multi-tile active photonic interposer under a large package, with edge-attached fibers carrying WDM microring links (vendor description).

| quantity | value | class | source |
| --- | --- | --- | --- |
| chip-to-interposer bump pitch | ≈ 120 um | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| horizontal optical buses per tile | 16 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| bandwidth per fiber (direction counting not stated) | 448 Gbps | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| bandwidth per fiber counting Tx + Rx, M-series (ISES slide) | 800 Gbps | VENDOR_CLAIM | [lm_ises25](https://lightmatter.co/wp-content/uploads/2025/08/ISES-Korea-08-2025_Ritesh-Jain.pdf) |
| total bi-directional bandwidth (EVK technical specifications) | 114.6 Tbps | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| bandwidth counting Tx + Rx (Specifications table) | ≤ 114 Tbps | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| total optical bandwidth (press release; Tx/Rx counting not stated) | 114 Tbps | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| chiplets stacked on the interposer | 34 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| PIC + laser energy efficiency of 'current Passage products' (SerDes excluded) | 2.3 pJ/bit | PEER_REVIEWED | [lm_hoti25_paper](https://arxiv.org/abs/2510.15893) |
| SerDes energy efficiency (EVK) | 2 pJ/bit | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| authors' split of the 2.3 pJ/bit: laser (off-package) 1.1, PIC (in-package) 1.2 (value = laser share) | 1.1 pJ/bit | PEER_REVIEWED | [lm_hoti25_paper](https://arxiv.org/abs/2510.15893) |
| system-level energy efficiency including laser (EVK) | 2.3 pJ/bit | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| EVK server form factor | 3 RU | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| fiber array described as bi-directional, pluggable, high-density | text | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| optical fibers, edge attached | 256 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| multi-reticle active photonic interposer area | ≥ 4000 mm2 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| I/O chiplets 3D stacked on the interposer (EVK) | 32 | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| per-wavelength lane rate, NRZ | 56 Gbps | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| per-link configuration: 8 wavelengths at 56 Gbps each (value = Gbps per wavelength) | 56 Gbps | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| full-duplex TX-RX links per bus (capacity) | ≤ 2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| microring modulator measured EO S21 bandwidth at -1 V bias (35.4 GHz at -2 V) | 31.8 GHz | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| microring diameter | ≈ 15 um | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| microring tuning element: resistive heater | text | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| microring modulation mechanism: depletion PN junction | text | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| integrated advanced package area | 7735 mm2 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| package outline, 91 mm x 85 mm (two values; icon labelled '3D photonic chip-on-wafer package') | text | VENDOR_CLAIM | [lm_web_m1000](https://lightmatter.co/products/m1000/) |
| package length | 91 mm | VENDOR_CLAIM | [lm_web_m1000](https://lightmatter.co/products/m1000/) |
| package width | 85 mm | VENDOR_CLAIM | [lm_web_m1000](https://lightmatter.co/products/m1000/) |
| TDECQ of the 112 Gbps PAM4 eye ('PAM4 also enabled') | 0.83 dB | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| foundry and assembly partners named for M1000 production readiness | text | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| silicon photonics platform of the PIC | text | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| power delivery in the integrated advanced package | 1.5 kW | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| power delivery for XPUs and switches (EVK page) | ≥ 1 kW | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| power delivery density | ≥ 1.4 W/mm2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| number of reticles in the multi-reticle interposer (Appendix: not disclosed) | text | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| electrical SerDes count | 1024 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| SerDes per tile | 128 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| SerDes rate options on the product page (56 and 112 Gbps) | text | VENDOR_CLAIM | [lm_web_m1000](https://lightmatter.co/products/m1000/) |
| Passage supply chain on HC25 slide: EIC fab, PIC fabs, packaging | text | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| thermal load chips 3D stacked on the interposer (EVK) | 2 | VENDOR_CLAIM | [lm_web_m1000evk](https://lightmatter.co/products/passage-m1000-evk/) |
| power density of a 369 mm2 thermal test chip on Passage | 1.47 W/mm2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| tile arrangement, 2 rows x 4 columns | text | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| number of tiles in the active interposer | 8 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |
| Passage TSV current density capability | ≥ 2.5 A/mm2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| area for an optical transmitter/receiver | 0.015 mm2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| Tx + Rx area with microrings, inductorless driver and analog front end | 0.006 mm2 | VENDOR_CLAIM | [lm_hc25_m1000](https://www.hc2025.hotchips.org/assets/program/conference/day2/57-lightmatter_hotchips_2025_final.pdf) |
| WDM wavelengths per waveguide and fiber | 8 | VENDOR_CLAIM | [lm_pr_m1000](https://lightmatter.co/press-release/lightmatter-unveils-passage-m1000-photonic-superchip-worlds-fastest-ai-interconnect/) |

Details: [docs/twin/passage_m1000.md](twin/passage_m1000.md).

## Photonic processor (Nature 2025)

Six-chip photonic processor: four photonic tensor cores under two control dies, running neural networks in adaptive block floating point (peer-reviewed, vendor-authored).

| quantity | value | class | source |
| --- | --- | --- | --- |
| ABFP activation scale: one bfloat16 scale per input vector | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| ABFP block: one bfloat16 scale per vector; vector length N = 128 (PTC width) | 128 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| ABFP output equation with gain G (gain inside Q_11, divided out in the NCE) | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| ABFP output equation without gain | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| output (ADC) quantizer for an n-term dot product: bin n*delta_Y, clamp +-n | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| ADC output rescaled by the bfloat16 scales (in the NCE) | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| QAT: forward pass in ABFP, straight-through estimator for Q7, Q10, Q11 | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| symmetric DAC quantizer Q_n (n = 7 weights, 10 activations; Q_11 at the ADC) | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| basumallik2022_abfp authors' affiliation | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| what ABFP means in basumallik2022_abfp: a length-n vector (tile width) shares one BFLOAT16 scale | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| basumallik2022_abfp title and authors | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| rounding rule of the ABFP quantizer | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| ABFP scale choice (max-abs) and normalization to [-1, 1] | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| DAC quantization symmetric around zero, one level forgone | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| accumulation of partial outputs across tiles when the matrix is wider than n | text | VENDOR_CLAIM | [basumallik2022_abfp](https://arxiv.org/abs/2205.06287) |
| ABFP weight scale: one bfloat16 scale per weight-matrix row | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| activation (input vector) precision | 10 bits | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| output ADC resolution | 11 bits | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| output ADC effective number of bits | 9.8 bits | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| output ADC power | 66 mW | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| output ADC sample rate | ≤ 2 GS/s | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| bumps per control die (top side of the interposer) | 25000 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| bumps per PTC (bottom side of the interposer) | 6000 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vendor llms.txt: Envise operations per watt (exact Appendix phrase) | 262 TOPS/W | VENDOR_CLAIM | [lm_llms_txt](https://lightmatter.co/llms.txt) |
| paper: throughput at the 2 GHz peak clock (operations per second) | 262 TOPS | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vendor web: Envise efficiency, operations per watt | 262 TOPS/W | VENDOR_CLAIM | [lm_web_ptc](https://lightmatter.co/vision/) |
| chips in the photonic processor package | 6 | VENDOR_CLAIM | [lm_blog_newcomputer](https://lightmatter.com/blog/a-new-kind-of-computer/) |
| clements2016 claim: half the footprint of the Reck design, more loss tolerant | text | PEER_REVIEWED | [clements2016](https://arxiv.org/abs/1603.08788) |
| clements2016: optical depth N vs 2N-3 (Reck), same N(N-1)/2 beam splitters | text | PEER_REVIEWED | [clements2016](https://arxiv.org/abs/1603.08788) |
| clements2016 title and authors | text | PEER_REVIEWED | [clements2016](https://arxiv.org/abs/1603.08788) |
| PTC clock frequency, peak | 2 GHz | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC clock frequency, sustained | 500 MHz | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| photonic components in the processor (vendor blog) | ≈ 1000000 | VENDOR_CLAIM | [lm_blog_newcomputer](https://lightmatter.com/blog/a-new-kind-of-computer/) |
| optical components in the processor (vendor web) | ≥ 200000 | VENDOR_CLAIM | [lm_web_ptc](https://lightmatter.co/vision/) |
| control chiplet (DCI) area | ≈ 780 mm2 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| control dies (digital control interface, DCI) per processor | 2 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| control die dimensions (Appendix: 31.4 x 25.0 mm) | text | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| control die length | 31.4 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| control die width | 25 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| control die process node | 12 nm | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| power of the two control dies (Appendix: 65 W) | 65 W | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| optical fan-out tree from each input fibre | 16 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| effect of gain: ADC reads lower bits, upper bits may saturate | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| ADC 11-bit window within the 24-bit output word versus gain | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| position of gain G in the signal chain: after the PTC, before the ADC | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vendor wording: analog signal amplified by G before the ADC, G divided out digitally | text | VENDOR_CLAIM | [lm_blog_newcomputer](https://lightmatter.com/blog/a-new-kind-of-computer/) |
| how G = 1.86 was measured | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| design target for the gain factor G | 4 | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| achieved overamplification (gain) factor G | 1.86 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| how gain G > 1 is realized: TIA gain and laser power both raised | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| organic interposer dimensions (Appendix: 54 x 56 mm) | text | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| interposer length | 56 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| interposer width | 54 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| number of DFB lasers | 8 | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| laser wavelength grid: CWDM4 in the 1310 nm band | text | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| optical power in fibre per laser | 200 mW | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| electrical power per laser including TEC | 1.25 W | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| time-of-flight latency through the PTC (vector modulator to weights to TIA) | ≈ 200 ps | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| silicon ridge waveguide propagation loss | 1.35 dB/cm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| silicon nitride waveguide propagation loss | 0.68 dB/cm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| analog noise model used in QAT | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| full-precision bits of one 128-term dot product (7-bit x 10-bit) | 24 bits | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| processor package dimensions (80 x 65 mm) | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| package length (SI) | 80 mm | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| package width (SI) | 65 mm | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| weight-cell photodetector bandwidth | 10.6 GHz | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| electrical power of the processor while running | 78 W | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| optical (laser) power delivered to the processor | 1.6 W | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| photonic chiplet (PTC) area | 349 mm2 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| photonic tensor cores (PTCs) per processor | 4 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC die dimensions (Appendix: 14.00 x 24.96 mm) | text | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC die length | 24.96 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC die width | 14 mm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC power for vector and weight encoding only (per PTC per Table S3) | 250 mW | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC weight-array dimension N (N x N = 128 x 128) | 128 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| PTC-only computational efficiency (vector and weight encoding energy only) | 262 TOPS/W | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| power per photonic tensor core (Appendix: 3.2 W each) | 3.2 W | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| photonic tensor core process node | 90 nm | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| weighted products summed as current on row lines | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| shen2017 authors (Harris is a co-author) | text | PEER_REVIEWED | [shen2017](https://arxiv.org/abs/1610.02365) |
| shen2017 processor: MZI mesh size | 56 | PEER_REVIEWED | [shen2017](https://arxiv.org/abs/1610.02365) |
| shen2017 affiliations (no Lightmatter) | text | PEER_REVIEWED | [shen2017](https://arxiv.org/abs/1610.02365) |
| PTCs under the control dies: DCIs on the top side of the interposer, PTCs on the bottom side | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 BERT-Tiny IMDb, FP32 reference | 86.2 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 BERT-Tiny IMDb, on the photonic processor | 83.2 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 BERT-Tiny SQuAD (F1 score), FP32 reference | 43.5 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 BERT-Tiny SQuAD (F1 score), on the photonic processor | 12 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 ResNet18 CIFAR-10, FP32 reference | 88.3 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 ResNet18 CIFAR-10, on the photonic processor | 86.4 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 ResNet18 MNIST, FP32 reference | 99.4 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 ResNet18 MNIST, on the photonic processor | 99.3 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 SegNet Oxford-IIIT Pet, FP32 reference | 82.3 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| Table 1 SegNet Oxford-IIIT Pet, on the photonic processor | 63.7 % | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| SI Table S1 emulation, BERT-Large SQuADv1.1 F1 (%): FP32, ABFP G=1, ABFP G=4, after QAT G=4 | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| SI Table S1 emulation, ResNet50 ImageNet accuracy (%): FP32, ABFP G=1, ABFP G=4, after QAT G=4 | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| processor TDP at the 2 GHz peak (average 78 W) | 150 W | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| throughput at the 2 GHz peak clock, ABFP16 operations per second | 262 TOPS | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| throughput at the 500 MHz sustained clock, ABFP16 operations per second | 65.5 TOPS | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| TIA bandwidth | 0.8 GHz | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| TIA transimpedance gain | 2.8 kOhm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| TIA input-referred noise current | 0.4 uA rms | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| whole-processor efficiency, average (SI Table S4; peak 1.75) | 0.81 TOPS/W | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vector (activation) DAC resolution | 10 bits | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vector DAC effective number of bits | 8.3 bits | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vector DAC power | 72 mW | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| fibre V-grooves per PTC | 12 | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| V-groove fibre-to-chip coupling loss | 1.56 dB | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| fibre V-groove pitch | 250 um | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| MZI vector modulator bandwidth | 3.8 GHz | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| MZI vector modulator insertion loss | 1.1 dB | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| vector modulator (vector encoder) type: MZI | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| MZI vector modulator VpiL | 0.92 V cm | PEER_REVIEWED (not verified) | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| weight precision (weight DAC) | 7 bits | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |
| weight applied on photocurrent inside each weight unit cell | text | PEER_REVIEWED | [ahmed2025_nature](https://doi.org/10.1038/s41586-025-08854-x) |

Details: [docs/twin/photonic_processor.md](twin/photonic_processor.md).

## vClick optics

Detachable fiber-array unit with vertical expanded-beam coupling to the PIC, built with SENKO (vendor and partner descriptions).

| quantity | value | class | source |
| --- | --- | --- | --- |
| SENKO MPC20 Metallic PIC Coupler fiber count | 20 | PUBLISHED_SPEC | [senko_mpc20](https://senko.com/product/mpc-20) |
| SENKO MPC20 fiber pitch | 127 um | PUBLISHED_SPEC | [senko_mpc20](https://senko.com/product/mpc-20) |
| SENKO MPC20 profile height | ≤ 1.2 mm | PUBLISHED_SPEC | [senko_mpc20](https://senko.com/product/mpc-20) |
| vClick detachable fiber connectors in the OCP 2026 1RU 204.8T CPO switch tray built with Flex (same tray: eight Passage CPO engines) | 8 | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| Passage engines with vClick in the OCP 2026 102.4T XPU tray ('four Passage and vClick units'; engine and connector counts not separated) | 4 | THIRD_PARTY | [counterpoint_ocp26](https://counterpointresearch.com/en/insights/lightmatter-links-with-odms-to-pave-a-glide-path-for-cpo-co-packaged-optics) |
| vClick insertion loss as relayed by Futurum from Lightmatter (analyst report of a verbal company claim) | ≤ 1 dB | THIRD_PARTY | [futurum_ocp26](https://futurumgroup.com/insights/lightmatter-and-flex-bring-2048-tbps-co-packaged-optics-into-open-racks/) |
| vClick detachable FAU insertion and re-insertion loss, demonstrated (no wavelength, mating-cycle count or measurement conditions stated) | ≤ 1.5 dB | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| Compatible with mold-and-grind advanced packaging flows (Lightmatter: 'as demonstrated in ASE’s advanced packaging flows') | text | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| No active fiber alignment needed in assembly (SENKO: 'passive expanded‑beam interface') | text | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| Uses SENKO SEAT optical interface and SENKO MPC (Metallic PIC Coupler) connector; MPC variant not named | text | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| Optical interface: Lightmatter vertically expanded-beam coupling between fiber array and PIC | text | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| Spectral span over which vClick supports CWDM and DWDM (Lightmatter wording) | ≥ 80 nm | VENDOR_CLAIM | [lm_pr_vclick](https://lightmatter.co/press-release/lightmatter-unveils-vclick-optics-industry-first-detachable-fiber-array-unit-for-cpo-advanced-packaging-and-high-volume-production) |
| Spectral span over which vClick supports CWDM and DWDM (SENKO wording) | ≥ 80 nm | VENDOR_CLAIM | [senko_pr_vclick](https://www.senko.com/senko-collaborates-with-lightmatter-on-detachable-connectivity-to-the-pic-for-3d-co-packaged-optics/) |

Details: [docs/twin/vclick.md](twin/vclick.md).
