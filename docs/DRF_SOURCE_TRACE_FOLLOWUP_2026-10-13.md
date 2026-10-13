# Source-trace follow-up — four shrink-exploration assets

**Date:** 2026-10-13 (Asia/Shanghai)  
**Checkout inspected:** `C:/Users/26843/Documents/ChatGPT/redefusion`  
**Branch / HEAD:** `docs/project-status-catalog-2026-10-10` / `a74126c11d857da8514074b72282adc8d47f28a7`  
**Input audit attachment SHA-256:** `7c99ec5465c2138a2962b0c3fbe082594be0b8286d506b99fe5416a0bf4a6841`

This versioned candidate records the supplied read-only trace and a limited independent recheck. No CSV was opened or hashed in this follow-up; dataset digests below are copied from the existing registry and are not reverified here. No data-processing or experiment release is created.

## Independently rechecked

The six external receipt/manifest/acceptance/dispatch records listed in the audit exist in the local `lobster-link` staging area and their SHA-256 values match the supplied report:

| Staged evidence | SHA-256 |
|---|---|
| `geng-lobster/004-T002-receipt.md` | `4793a07be279084127e388166d8a49e807cf0fabb6a589c41c2c2f88f9a28825` |
| `geng-lobster/006-T004-receipt.md` | `8bb34108d00104870844b10f70fa767134daa5d1d2c6429763ab95a44f9da431` |
| `geng-lobster/T004-cohort/MANIFEST.csv` | `5c23a8e6717a8e5e1341bf251061b8905ab9966a20eee7c43981335cdd315927` |
| `thinkbook-lobster/047-T004-cohort-acquisition.md` | `44929363b79ff1d51d7ec9dc685c995de301cd8ec2d9c5d644f09ee4a9cc6289` |
| `thinkbook-lobster/048-to-geng-t004-accepted.md` | `63d3936b03f4f6e878d257979b3c547d7c5818ad12d8056f87e642c2275ba306` |
| `thinkbook-lobster/TASK-LEDGER.md` | `e2c80bd0f69fe891a7210b0dff0124afb8d97ca59a797892997b03eeebd96707` |

Git metadata also confirms `d89bee8c5c61717e78d56a1366ef9624781cbf1d` at 2026-09-10 11:10:16 +08:00 has a subject naming Yahoo Finance and fetch scripts, and `775a5997a053e4d6e1824adc30e024f09a23df93` at 11:11:25 adds the ten original CSV paths, including BTCUSD, ETHUSD, and GSPC. The 69-second proximity and project-authored description are useful provenance leads, but do not identify the process that wrote each file, prove execution of a particular script, or establish applicable terms or rights. The existing recollection that an unspecified agent fetched them remains unreconciled.

## Asset conclusions

| Asset | Strongest current provenance evidence | Remaining material gap |
|---|---|---|
| BTCUSD | Original-10 Yahoo project description; adjacent Git commits add the CSV. Candidate scripts include `BTC-USD`. | Actual actor, execution record, exact endpoint/date, applicable terms, and a verifiable internal research-processing basis are unresolved. |
| ETHUSD | Same project-level lead; candidate scripts include `ETH-USD`. | Same gaps as BTCUSD. |
| GSPC | Same project-level lead; candidate scripts include `^GSPC`. A separate T002 measurement reproducing a similar date/row range is not file-linkage proof. | Same gaps as BTCUSD. |
| N225 | T004 dispatch and acceptance records plus a dated geng receipt self-attest a scripted Yahoo chart API delivery; manifest digest linkage to the registry/lock is reported and was recorded in the earlier disposition. | The source and delivery chain are better documented, but no acquisition-time terms version, explicit automation permission, internal research-use basis, or derived-output basis was found. |

For all four assets, separate decisions remain necessary for (1) internal research processing, (2) public release of raw data, and (3) release of predictions, metrics, weights, or other derivatives. An unresolved public redistribution basis does **not by itself** prove that internal research is prohibited. Conversely, the project lead's delegation cannot substitute for a missing external or otherwise applicable use basis.

## Governing boundary and disposition

The checked-in management rule at `docs/management/v1_4/AUTHORIZATION.md:25` permits a verifiable basis from applicable terms, existing permission, or another source; it does not require a vendor signature in every case. It also says that an unknown use basis cannot be supplied by proxy authorization and that unresolved data-specific actions remain blocked while unrelated documentation and synthetic validation may continue.

The current Yahoo Terms of Service state that automated access or collection from Yahoo Services requires express prior permission ([official terms, §2.4.9](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)). That current page does not establish which regional/product terms governed acquisition on 2026-09-10 or 2026-09-14, whether separate permission existed, or how non-Yahoo files were acquired. It is a concrete issue to resolve, not a final legal determination.

**Disposition:** the trace narrows the original-10 lead and strengthens N225 delivery provenance, but no reviewed evidence establishes a defensible internal research-processing basis for any of the four files. Do not read price values, preprocess, fit, score, or analyze these assets until that basis is verified and a version-bound data-qualification release records the exact scope. Continue synthetic and documentation work. No active R1 protocol or gate is changed by this note.

## Evidence needed to close the gate

1. For BTCUSD, ETHUSD, and GSPC, reconcile the owner's 2026-09-10 project-session lead with the stored “unspecified agent” recollection. A command/session log that identifies a completed acquisition and exact files is useful; Git timestamps alone are insufficient.
2. For all four files, establish the acquisition-time region/product terms applicable to the actual acquisition route and whether those terms support internal non-commercial research processing. Check the dated terms and any existing permissions; do not assume a vendor signature is the only valid evidence.
3. Record internal processing separately from raw redistribution and derived-artifact release. Keep publication blocked only for the affected artifact classes whose rights remain unresolved.
4. If the evidence remains unavailable, use a replacement source only after recording a verifiable license or other basis for internal research, and treat the changed source as a new data version with a new experiment manifest.

