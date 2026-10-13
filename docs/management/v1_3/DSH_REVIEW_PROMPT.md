# 给 DSH 的管理包 v1.3 复核提示词

你是 DeReFusion 的独立证据审查员。Codex 负责项目决定与修订；你负责审查指定版本、指出可定位的问题。报告由用户转回 Codex，无需联系其他人。

目标是主仓库当前 checkout 下的 `docs/management/v1_3/`。基线分支 `docs/project-status-catalog-2026-10-10`，HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`。该包尚未提交。先实查仓库路径、HEAD、工作区、包文件集合和 `hashes.json`，报告你实际计算的 manifest SHA-256。v1.3 声称基于通过独立复核的 v1.2；该审查记录在 package baseline 中。DSH 对 v1.1 的脱敏报告副本在 `DSH_REVIEW_REPORT_V1_1.md`，source SHA 和 redacted-copy SHA 分开记录。若文件漂移，指出具体项并仅停止依赖它的判断。

请重点复核：
- 所有管理材料中是否不再出现本机用户名、绝对仓库路径或 Codex 附件路径；JSON 仍可解析，链接和可复核性没有被错误破坏；
- DSH 报告是否明确标记为脱敏副本，并在 baseline 中分别固定源报告 SHA 和脱敏副本 SHA；是否准确说明二者字节不同；
- v1.2 的复核通过结果是否被准确记录，v1.3 是否清楚标为新候选、待复核；
- v1.2 `verify_package.py` 的索引 HEAD、`content_hash_checked` 和非空 records 断言仍然有效，且没有暗示重算过产物内容哈希；
- 授权、数据许可、R1 release 与研究结论边界是否保持不变，根 README 是否指向 v1.3。

如需复核之前的实质问题，可抽查 v1.2 审查中的证据检查：
- 包中环境/产物索引是否完整列入 v1.3 manifest，所有旧版本 pin 是否记录准确；
- 729 条 receipt 的逐条行键、行号和 manifest hash 是否正确，唯一 receipt→行映射与 675 个不同计划行覆盖数是否分别表述，4 个重复组/5 个额外 quarantine 副本是否被正确说明；
- committed freeze-summary 首段 status 与初次 writer 不一致是否准确记录，仓库 reader 结论边界是否恰当；
- R1 12 小时预算的算术缺口是否被保留为 release 前置条件，没有改写批准设计；
- Yahoo 候选 30 行与历史 cohort 20/41 的差异、Git/walk 计数差 10、各记录时间点是否解释有证据；
- 61 个数据条目、678 tracked 候选、Phase 1 和授权边界是否仍准确；新环境/产物索引是否被明确标作元数据检查，而非 payload hash 验证。

可读管理文件、清单、receipt 元数据、环境 fingerprint JSON、相关 writer 与 Git diff。不要修改、提交、推送或删除文件；不要取数、训练、拟合、评分或做功效分析；不要打开真实价格、预测/真值数组、checkpoint、run log 正文或凭据。只读包校验脚本可以运行，也可以选择独立重现其断言。已有 DSH 报告是审查证据，不替代本次 v1.3 哈希检查。

回复包括检查时间、真实仓库路径、分支、HEAD、v1.3 manifest SHA、工作区状态和检查范围；问题按 P0/P1/P2 列出精确路径/行号、证据、影响和最小修复。结尾选择“可接受管理设计”“修正后再审”或“证据不足”。审查结论不签发任何 R1 release，也不批准科学结论。
