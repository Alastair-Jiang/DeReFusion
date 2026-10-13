# Project inventory errata — 2026-10-10

This append-only erratum corrects factual statements in the 2026-10-10 project inventory and takeover status notes after an independent cross-review. It does not rewrite the original snapshot or authorize any experiment.

## Verified repository identity

- Local checkout: `C:/Users/26843/Documents/ChatGPT/redefusion`
- Branch: `docs/project-status-catalog-2026-10-10`
- HEAD at verification: `0f4f86ed83b5d927ee2c4db326c71c585a99684e`
- Remote refs at verification: `origin/main` = `001717222fb50f588ec28746e0deb2cd66bb07ef`; `origin/docs/project-status-catalog-2026-10-10` = `0f4f86ed83b5d927ee2c4db326c71c585a99684e`
- The GitHub repository page responded HTTP 200 to an unauthenticated request. The remote is therefore publicly accessible at that URL as checked on this date.

## Data tracking correction and rights review

The prior inventory and takeover correction incorrectly described both `dataset/` and `data/` as ignored and absent from the remote. In the current checkout, `git ls-tree -r` finds 61 tracked OHLC CSV files under `dataset/` and two tracked metadata files under `data/`, in both `HEAD` and `origin/main`. The local `dataset/README.md` is ignored and is not in that tree. The two tracked `data/` files are acquisition metadata, not the raw OHLC panel; a local download report contains an HTTP 403 response, not market prices. This check inspected Git paths and metadata only; it did not read OHLC values.

This means the 61 tracked OHLC files are already present in the remotely accessible repository history. Their per-file supplier, applicable terms, attribution and redistribution rights have not been established by this audit. The repository's MIT code licence does not establish those rights. The existing registry also lacks a complete per-asset rights ledger. This is a publication-rights blocker for further distribution, not a finding that any particular file is unlawful. Review the acquisition provenance and applicable vendor terms with the responsible rights holder. For Yahoo-sourced content, see the [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html?ncid=mbr_idnedulnk00000001); this link alone does not resolve which assets came from Yahoo or the terms applicable to historical acquisition.

No history rewrite, force push, deletion, or visibility change was performed. Those actions could disrupt collaborators and would not erase copies already fetched. Until the rights review is complete, do not add or republish further raw or derived data. If remediation is required, first determine the affected paths and obtain an approved repository and retention plan.

## Other corrections

- The inventory's extension histogram omitted seven untracked files across `.mdx` (2), `.scala` (1), `.rst` (1), `.adoc` (1), `.gitattributes` (1), and `.ps1` (1). The previously reported histogram total was therefore incomplete; the full observed extension list belongs in a fresh inventory pass that handles Windows long paths.
- Three files compared between the main checkout and a separate worktree differ in raw SHA-256 because of CRLF/LF bytes. After removing carriage returns, the compared text bytes match. This does not satisfy an exact-byte hash binding, but it is not evidence of a semantic content change.
- The status catalog's `bf6ba8f...` snapshot commit remains available in the local reflog/object database but is not contained in a current branch. It is a historical snapshot identifier, not the present checkout HEAD. The inventory's separate `6866dbd...` scan baseline is also historical; current repository claims must use the snapshot and scope stated for that claim.

## Scope of verification

This erratum verifies repository identity, Git tracking, remote refs, unauthenticated page reachability, prior cross-checkout byte normalization, and the extension-count omission. It does not certify data rights, inspect OHLC values, re-audit experiment payloads, change experiment authorization, or validate the scientific conclusions summarized by earlier reports. The R1 execution-gate file remains the controlling local record until formally superseded; this erratum is not an execution release.
