# Source and rights supplement — four shrink-exploration assets

**Date:** 2026-10-13 (Asia/Shanghai)  
**Checkout:** `C:/Users/26843/Documents/ChatGPT/redefusion`  
**Branch / HEAD observed:** `docs/project-status-catalog-2026-10-10` / `a74126c11d857da8514074b72282adc8d47f28a7`  
**Supplied audit SHA-256:** `e25b645efeA0858342ee85178a73091eb091916c8a38eb5100a53dc80cd1a432`

This supplement records a correction to the shrink-exploration source register and a limited review of Yahoo's currently published legal pages. It preserves the earlier register and source-trace note. No dataset CSV was opened, hashed, or processed; no data-source request was made; no external person was contacted.

## Correction to N225 provenance fields

The prior `SOURCE_RIGHTS_GAP_REGISTER.csv` used “no per-file acquisition receipt/license located” too broadly. The reviewed external staging area contains a dated T004 receipt and a manifest that lists N225 and a file digest. The receipt says geng ran a scripted Yahoo chart API acquisition on 2026-09-14, delivered the cohort, and independently checked the manifest digests. This establishes a delivery/custody trail and a custodian self-attestation. It is **not** a supplier-issued receipt, a provider permission, or independent verification of the download event or legal basis.

The versioned successor `SOURCE_RIGHTS_GAP_REGISTER_V0.2_2026-10-13.csv` separates those concepts. For N225 it records geng as the self-reported acquisition/delivery actor, links the receipt and manifest by path and SHA-256, and keeps automated-acquisition permission, internal processing, and derived-output rights unverified. BTCUSD, ETHUSD, and GSPC remain tied only to project Git/source-code leads; their actual downloader and per-file acquisition receipt remain unknown.

## Current Yahoo terms pages reviewed

The current Yahoo Terms of Service page contains §2.4.9, which the project has recorded as requiring express prior permission for automated access or collection. Yahoo also publishes a separate current Yahoo Developer API Terms of Use page and developer guidelines. The API terms page says API use is governed by those API terms together with the general Terms of Service, guidelines, and API-specific documentation; it describes a credentialed license with restrictions. The reviewed page does not establish that the T004 chart endpoint or the original-10 retrieval path was a Yahoo Developer API within that document's scope. The current pages also do not establish the applicable regional/product version or rights on the 2026-09-10 and 2026-09-14 acquisition dates.

Official pages checked on 2026-10-13:

- Yahoo Terms of Service: <https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html>
- Yahoo Developer API Terms of Use: <https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html>
- Yahoo Developer Network Guidelines: <https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html>

The search index exposed the current Developer API Terms text, but direct page retrieval returned an access error during this check. Treat this as a limited current-page review, not an archived or acquisition-date terms capture. No dated 2026-09-10/14 official terms snapshot or provider permission was found in the supplied report or the project records already reviewed.

## Decision

The supplied audit's main distinction remains correct: a custody receipt does not establish rights, and lack of a raw-data redistribution basis does not by itself prove that internal research is prohibited. For all four assets, no reviewed evidence presently supplies an affirmative, verifiable basis for local internal research processing. The status is **UNRESOLVED**, not a finding that internal use is legally prohibited. Automated acquisition permission, raw redistribution, and derived-output release remain separate unresolved/no-go decisions as recorded in the versioned register.

Accordingly, the real-data gate stays blocked for these four assets. No price-value inspection, preprocessing, fitting, scoring, or shrink-exploration run is released by this supplement. Documentation and synthetic-only checks may continue. This is a project evidence disposition, not legal advice.

## Evidence identity

- Supplied audit attachment SHA-256: `e25b645efeA0858342ee85178a73091eb091916c8a38eb5100a53dc80cd1a432`
- Existing source-trace note SHA-256 at review: `c6b0b746ec4a05fc80c0447dbd97c2248e736430f65a48c75811a3dbe385f0f3`
- N225 receipt SHA-256: `8bb34108d00104870844b10f70fa767134daa5d1d2c6429763ab95a44f9da431`
- N225 manifest SHA-256: `5c23a8e6717a8e5e1341bf251061b8905ab9966a20eee7c43981335cdd315927`
- Prior register SHA-256: `e1eed1f58a86bce32a87940f88feeae64b291746d000be613f83f23571066d8a`

