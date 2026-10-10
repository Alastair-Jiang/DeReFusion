# DeReFusion 项目管理基线 v1.4

建立日期：2026-10-10。负责人：用户委托的 Codex 项目代理负责人。v1.4 基于已通过独立只读复核的公开候选 v1.3，修正包内验证器对文档发布后 HEAD 前移的处理：只要盘点 HEAD 仍是当前 HEAD 的祖先，且固定输入哈希均匹配，就不会把发布提交误报为源证据漂移。公开脱敏和 R1 阻断边界保持不变。v1.4 尚待独立复核。本文档包建立日常管理规则；它不是一次真实数据训练放行，也不改变旧实验的证据等级。v1、v1.1、v1.2 是本机历史候选，未随此包发布。

## 从这里开始

| 文件 | 用途 |
|---|---|
| [AUTHORIZATION.md](AUTHORIZATION.md) | 谁能决定什么、哪些动作可以自行放行、哪些仍需用户决定 |
| [REPOSITORY_AND_DATA.md](REPOSITORY_AND_DATA.md) | checkout、版本、数据、备份、Git 发布管理 |
| [EXPERIMENTS.md](EXPERIMENTS.md) | 实验状态、冻结、执行、失败和证据验收 |
| [PLAN_AND_GAPS.md](PLAN_AND_GAPS.md) | 按依赖排列的下一步和逐项缺失信息 |
| [baseline.json](baseline.json) | 本轮检查的路径、HEAD、范围、输入哈希和盘点结果 |
| [datasets.csv](datasets.csv) | 61 份数据的来源线索与使用边界，未知保持未知 |
| [experiments.json](experiments.json) | 实验系列目录，区分计划与历史报告陈述 |
| [COORDINATION_FINDINGS_2026-10-10.md](COORDINATION_FINDINGS_2026-10-10.md) | receipt 对账与冻结摘要写入链的本轮证据 |
| [receipt_manifest_join.json](receipt_manifest_join.json) | 729 条 receipt 元数据与 819 个计划行的关联结果 |
| [receipt_environment_artifact_index.json](receipt_environment_artifact_index.json) | 环境指纹引用与产物路径/声明哈希清单，内容哈希未重算 |
| [DSH_REVIEW_RESPONSE_V1_1.md](DSH_REVIEW_RESPONSE_V1_1.md) | v1 审查意见及逐项处置 |
| [DSH_REVIEW_REPORT_V1_1.md](DSH_REVIEW_REPORT_V1_1.md) | DSH 对 v1.1 的脱敏复核报告副本；源报告 SHA 与脱敏副本 SHA 分开记录 |
| [DSH_REVIEW_RESPONSE_V1_3.md](DSH_REVIEW_RESPONSE_V1_3.md) | v1.2 独立复核结果及公开发布脱敏说明 |
| [DSH_REVIEW_RESPONSE_V1_4.md](DSH_REVIEW_RESPONSE_V1_4.md) | v1.4 对发布后 HEAD 校验的修订说明 |
| [v1.3 独立复核记录](../V1_3_INDEPENDENT_REVIEW_2026-10-10.md) | 已发布前序候选的复核报告与哈希 |
| [DSH_REVIEW_RESPONSE_V1_2.md](DSH_REVIEW_RESPONSE_V1_2.md) | v1.1 复核剩余 P2 项的处置记录 |
| [authorization.json](authorization.json) | 授权规则的结构化记录 |
| [r1_release_candidate.json](r1_release_candidate.json) | 尚未签发的 R1 分阶段执行记录 |
| [templates.json](templates.json) | 新数据、attempt、决策和发布记录的必填字段 |
| [DSH_REVIEW_PROMPT.md](DSH_REVIEW_PROMPT.md) | 可直接转交 DSH 的复核任务 |

## 本轮查实的状态

主 checkout 为 `[local repository root withheld]`，分支 `docs/project-status-catalog-2026-10-10`，HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`。本包是新增候选，未把其他 checkout 的文件合并进来。

元数据快照统计 106,264 个文件：1,511 tracked、12,327 walk-untracked、92,426 ignored。Git 同轮列出 12,337 untracked；差额 10 是 walk 排除的输出根中此前两个快照目录的 4+6 个文件，Git 枚举时存在而本次 walk 跳过。排除 `.git`、快照输出根、链接目标和其他 checkout；不是整个电脑或远程存储的盘点。数字属于快照时点。

Phase 1 找到 729 个 receipt 文件、724 个不同 receipt 哈希；5 个额外文件是 quarantine 中与 attempt 原件字节相同的副本。699 份写着 `completed_unreviewed`。728 条 receipt 路径各自唯一映射至某个计划行，但只覆盖 675 个不同计划行：A=15/15、B=300/300、C=360/360、D=0/144。1 条资源阻断记录没有运行身份。这不是 729 个已验收实验。四份计划 manifest 共 819 行且均为 `planned`。

700 条 receipt 的环境指纹哈希在本地元数据文件中找到匹配项，3,637 个 receipt 声明产物按文件名都能找到。没有重算 payload 哈希，也没有读取日志、checkpoint、预测或真值内容。

当前 HEAD 与本地 `origin/main` 引用各有 678 个数据或二进制候选：61 CSV、48 PTH、569 NPY。`checkpoints/` 有 36 个 tracked 文件，不能再笼统描述为全部被 Git 忽略。本轮只查路径、对象及大小，未打开这些二进制内容，也未判定它们能否公开。

既有合成材料的 53 个清单条目和 R1 的 14 个源码 pin 复核匹配；这证明字节身份，不等于重新运行测试或独立科学审查。本轮没有训练、评分或改写冻结协议。

## 新的工作方式

日常工作由 Codex 自主推进；真实数据流程由负责人在满足证据条件后逐阶段签发，不再反复向用户索取同一授权。未知数据许可、缺失运行输入和不可复现的证据仍需补齐。R1 保持探索性，当前没有有效执行放行。

先补来源和运行记录关联、独立检查合成生命周期，再按数据 QA → 预处理 → 拟合 → 冻结 → 测试评分顺序推进。历史缺失信息无法凭设计补造，全部进入带负责人、验收条件和阻断范围的台账。

验证命令：`python docs/management/v1_4/verify_package.py`。该命令检查本包和已固定输入，确认盘点 HEAD 是当前 HEAD 的祖先、环境/产物索引 HEAD 与 baseline 一致、所有条目仍标注未核实内容哈希；不读取价格值、不启动实验。公开包不包含本机绝对路径或完整本地路径清单。
