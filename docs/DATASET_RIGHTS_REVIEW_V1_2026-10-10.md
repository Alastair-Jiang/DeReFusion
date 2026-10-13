# Dataset source and redistribution review — 2026-10-10

## Decision status

**No per-asset redistribution clearance has been located.** The 61 OHLC CSV paths are already tracked on public upstream branches, and all 61 are present in a public fork's `main`. Do not add another copy or publish derived bundles until source and rights are established. This report is a provenance review, not a legal determination or permission to use the data.

## Repository and evidence inspected

- Checkout: `C:/Users/26843/Documents/ChatGPT/redefusion`
- Branch/HEAD at review: `docs/project-status-catalog-2026-10-10` / `8ae1aea5448260e45d4abc3189b6de46621395ff`
- `origin/main`: `001717222fb50f588ec28746e0deb2cd66bb07ef`
- Evidence inspected: `reproduction/results/dataset_registry.csv` (metadata only), `dataset/README.md`, `data/raw/yahoo/DOWNLOAD_LINKS.md`, `data/raw/yahoo/download_report.csv` (HTTP/error metadata only), Git path trees and history, GitHub repository/fork metadata, current Yahoo terms.
- No OHLC CSV values were opened or parsed. The registry's existing paths, cohort labels and SHA-256 values were used to build the [61-row rights review ledger](DATASET_RIGHTS_REVIEW_LEDGER_V1_2026-10-10.csv).

## Per-file source and rights assessment

The registered cohort counts are 20 `c1-20`, 10 `original-10`, 4 `gate-a-4`, and 27 `supporting-unregistered`.

| Files | Evidence located | Assessment |
|---|---|---|
| 20 `c1-20` files | `dataset/README.md` describes this cohort as the independent Yahoo cohort. The acquisition note lists Yahoo URLs and Stooq alternatives for several matching symbols, but describes a proposed/manual retrieval workflow and is not a per-file receipt. | Yahoo is supported only as a cohort-level source label; actual file-by-file acquisition route, account/permission, applicable terms, attribution, and redistribution right are not documented. Rights unverified. |
| 41 files in the other three cohorts | Registry identifies assets and research-use cohorts, not suppliers. The reviewed records do not connect each file to a provider receipt, licence, or acquisition record. | Supplier and applicable rights unverified for every file. Do not infer a source from a ticker, exchange, or asset class. |

The current [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html?ncid=mbr_idnedulnk00000001) prohibit automated collection without express prior permission and, absent explicit written permission, restrict reproduction/distribution of service content. This makes the 20-file cohort a priority for rights review; it does **not** prove that these files were collected automatically, establish which regional/product terms governed acquisition, or decide whether any legal exception or separate permission applies. No authoritative Stooq licence/permission record was located in the project. No provider terms were located for the other 41 files.

`LICENSE` covers project code; it does not grant rights in third-party OHLC data. Hashes establish byte identity only. The data registry currently lacks supplier, acquisition date/method, governing terms/version, attribution, and redistribution-permission fields.

## Remote exposure confirmed

GitHub reports the upstream repository as public. The following upstream branch tips contain `dataset/` paths:

| Remote branch | Tracked paths |
|---|---:|
| `main` | 61 |
| `docs/project-status-catalog-2026-10-10` | 61 |
| `codex/chinese-project-report` | 61 |
| `codex/live-hardware-flow` | 61 |
| `draft/ns-benchmark-runner` | 41 |
| Five Dependabot branches | 0 each |

The public fork `Washington5533/DeReFusion` also has all 61 paths on its `main`. No open pull requests were returned by the authenticated GitHub query. The relevant upstream data-history commits include `775a599` (initial 10 files), `9535393` (31 additional files), `95abfce` (C1 cohort additions), and later byte-preservation commits `780b77b` and `f21de75`.

Changing the upstream repository to private would not make the public fork private. Rewriting upstream history would not delete copies already fetched or remove the fork's independent history. A purge would require a separate, owner-approved plan for the public fork and any GitHub cached views; no third-party owner or GitHub support request was contacted.

## Required evidence and remediation choices

For each of the 61 rows, obtain (or explicitly mark unavailable): provider and instrument identifier; acquisition date and method; applicable terms/licence version; proof of permission for research storage and public Git redistribution; attribution requirement; derivative-data and result restrictions; and rights-holder contact/evidence location. Preserve the current hashes and research record while resolving this.

Then choose one of two publication states per file:

1. **Cleared:** retain or republish only with documented terms that permit the actual public distribution and required attribution.
2. **Not cleared:** keep the file out of future public bundles; if rights cannot be established, plan a history rewrite for the upstream branches containing it, replace raw values with schema/acquisition instructions and stable non-content metadata where permitted, and separately address the existing public fork.

Do not run an in-place history rewrite from this checkout. It contains unrelated user modifications/untracked work, and `git count-objects -vH` reported 59 garbage temporary objects totaling 1.66 GiB. Any rewrite should use a clean isolated mirror, verified backup, explicit ref list, a tested redaction result, and a coordinated force-push/fork plan.

## Gate table

| Check | Input | Status | Evidence | Next permitted action |
|---|---|---|---|---|
| Asset inventory | Registry + Git path trees | PASS, 61/61 mapped | Ledger records the registry digest and branch presence | Continue rights reconciliation without reading price values |
| Yahoo source trace | C1 cohort label + acquisition note | PARTIAL | Cohort-level label only; no file receipts | Find original download receipts/permission |
| Other 41 source trace | Registry + reviewed project docs | NOT READY | No per-file supplier evidence located | Search historical acquisition records; preserve unknown status |
| Public redistribution clearance | All 61 files | NOT VERIFIED | No per-asset permission evidence located | Do not publish additional raw/derived copies pending evidence |
| Upstream remediation coverage | Public branch tips | KNOWN | Five upstream branches contain 41–61 paths | Prepare clean-mirror rewrite plan only after a per-file decision |
| Fork remediation | Public fork main | NOT CONTROLLED BY UPSTREAM | Fork independently contains all 61 | Owner decision and authorized contact/removal path required |
