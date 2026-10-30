# DeReFusion 仓库整合基线复核 V2 — 2026-10-30

**状态：** 内部核查记录。不是发布许可，不是科学结论，不替换 `RECONCILIATION_2026-10-30.md`。本文件只记录该文件之后发生的变化，以及 2026-10-30 晚间重新实测的结果。

## 1. 远程实测

使用 `git ls-remote --heads origin` 直连远程读取（不是只看本地跟踪引用）：

| ref | 对象 | 与早期记录比较 |
|---|---|---|
| `refs/heads/main` | `87bc113d892320a343d61893b1c849ce4391dca5` | 未变 |
| `refs/heads/docs/project-status-catalog-2026-10-10` | `6a65204be0489d403d4564aa4c6d14fc0af89432` | **已变** |
| `refs/heads/codex/live-hardware-flow` | `07368fef65988020dc9c1c984b7a40aeae02794c` | 未变 |
| `refs/heads/codex/chinese-project-report` | `001717222fb50f588ec28746e0deb2cd66bb07ef` | 未变 |
| `refs/heads/draft/ns-benchmark-runner` | `ac40f380cc45630cef339c9a6cd5873034315a16` | 未变 |

变化的具体内容：早期记录把另一父提交写作 `ae6507423a6f78354735bedc1c786432f9f3edd1`。远程 `docs/project-status-catalog-2026-10-10` 随后前移 2 个提交（`710666a`、`6a65204`，提交时间 2026-10-30 15:05:35 +0800）。

**这项变化不改变既有候选的评审对象。** 候选树仍是对 `ae650742` 的合并结果；若改用新 tip 重新合并，会得到不同的树，必须重新评审，不能把旧评审平移到新树上。

## 2. 候选树重算

在隔离工作区 `<用户主目录>\.codex\worktrees\derefusion-reconcile-20261030` 实测（其余路径同样以主目录相对形式记录，正文不写绝对路径）：

```
git merge-tree --write-tree 87bc113 ae650742
→ 852065887fb5a80122f39102daa8afba2508d94f
git write-tree
→ 852065887fb5a80122f39102daa8afba2508d94f
```

暂存路径 177 条。两项独立计算一致，说明该 index 今天仍然等于"主线 × ae650742"的无冲突合并树。它**不是提交，也未发布**。

同时注意：index 与工作树不同。`README.md` 在该工作区有未暂存修订（见 `DRF_RELEASE_SCOPE_AND_RIGHTS_V1_2026-10-30.md` 第 3 节）。

## 3. 主检出状态（未改动）

- 路径：`<工作区>\Documents\ChatGPT\redefusion`（主检出）
- HEAD：`6a65204be0489d403d4564aa4c6d14fc0af89432`，分支 `stru_paln_test`（不在 `main` 上）
- 已跟踪文件修改 5 项、未跟踪条目 12,451 项（`git status --porcelain=v1 -uall` 共 12,456 条）
- 本次未对该检出执行暂存、提交、删除或移动

已跟踪的 5 项修改及其 SHA-256：

| 路径 | 工作树 SHA-256 |
|---|---|
| `docs/DRF_TAKEOVER_STATUS_CORRECTION_V1_2026-10-10.md` | `4229535b50648fe3179b45e1b62a5ffaace61ef5fc80578a967a8d9a6efcd6a9` |
| `docs/PROJECT_STATUS_AND_EXPERIMENT_CATALOG_V1_2026-10-10.md` | `6a2d0388fc816d8a0b89145cd601c17d7cb50daefe27944a64d61bd863c5f8a3` |
| `reproduction/analysis/receive_phase1_completed.py` | `7e824f9f1f8fac27f903cc21c8efda8cc9c53302163c7e68651b6a0002c3d39a` |
| `reproduction/results/phase1/local-5060-manifests/freeze-summary.json` | `a571c80576040e3e01db7dbd2356c119e015b3abe00f3333b11959e18dfb9fbd` |
| `tests/test_phase1_completed_receiver.py` | `89ee34db2828d8564fc5651a0d7e237e128bc31b7c55d9589b9dbdf25baff4dc` |

**需要单独标记的一项：** `freeze-summary.json` 的本地修改把 `status` 从 `frozen_pre_authorization` 改成 `authorized_nonconfirmatory_execution`，并加入两项 `authorization_sha256`。该修改未经过本轮审阅，未纳入本次交付，也没有被任何新记录引用。冻结清单的状态不能因为一次未审阅的本地编辑而视为已改变。

## 4. 工作区与分支

| 工作区 | 分支 | HEAD | 说明 |
|---|---|---|---|
| `<工作区>\Documents\ChatGPT\redefusion` | `stru_paln_test` | `6a65204` | 主检出，脏工作树，保留原样 |
| `.codex\worktrees\derefusion-reconcile-20261030` | `codex/reconcile-main-20261030` | `87bc113` | 177 路径候选在 index，未提交 |
| `.codex\worktrees\derefusion-remediation-20261030` | `codex/remediation-20261030` | `907a9b8` | 早前本地尝试，2 个未推送提交，保留 |
| `.codex\worktrees\derefusion-delivery-20261030` | `codex/remediation-delivery-20261030` | `87bc113` | **本次交付**，从 `origin/main` 新建 |
| `.codex\worktrees\live-hardware-flow\redefusion` | `codex/live-hardware-flow` | `07368fe` | 保留，未整分支合并 |
| `.codex\worktrees\40a7\redefusion` | `codex/chinese-project-report` | `0017172` | 保留 |
| 其他 2 个 | detached | — | 保留 |

早前的 `codex/remediation-20261030` 分支含两个实现草稿（`compression_replay_gate_v2.py` 与其测试、接收器整合提交）。本次交付**没有**改写或删除该分支；新分支从 `origin/main` 重新开始，只采用经本轮测试与审阅的内容，因此不会把已弃用的草稿当作已接受实现发布。

## 5. 与历史快照的差异汇总

1. 远程 `docs/project-status-catalog-2026-10-10` 前移 2 个提交；候选树仍绑定 `ae650742`。
2. 主检出 HEAD 位于 `stru_paln_test`，其两个提交现在也存在于远程 docs 分支上。
3. `freeze-summary.json` 存在未审阅的本地状态改写（见第 3 节）。
4. 外部 PR #2 的状态本轮未查询（需要外部 API）；本文件不对其合并状态作任何判断。
5. 截至本复核时点，没有修改任何既有远程分支；此后是否推送新分支，见交付报告。

## 6. 仍然成立的边界

- 候选树 `85206588` 未获独立批准，未合并进 `main`。
- 历史已跟踪的 `results/`（705 个文件）、`checkpoints/`（36 个文件）、`dataset/`（61 个 CSV）、`data/raw/yahoo/`（2 个文件）是既有暴露，不是新的发布授权。
- 哈希一致只证明字节身份，不证明来源、权利、独立性或科学有效性。
