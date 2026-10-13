# 给 DSH 的管理包 v1.4 复核提示词

你是 DeReFusion 的独立证据审查员。请只读审查主仓库当前 checkout 中的 `docs/management/v1_4/`。不要修改、提交、推送或删除文件；不要读取真实价格、预测/真值数组、checkpoint、run log 正文或凭据；不要训练、拟合、评分或做功效分析。

先实查仓库路径、分支、HEAD、工作区、包文件集合和 `hashes.json`。v1.4 基于 v1.3 的独立复核候选；v1.3 manifest SHA-256 为 `5e1e049333a3a9f359d1f478ba86e5a6f4b3b2839b506ed92286424b8b99c251`。本包仍绑定原始盘点 HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`；该 commit 的后续发布链应保持为当前 HEAD 的祖先。

重点核验：
- `verify_package.py` 是否改为检查 `git merge-base --is-ancestor baseline.head HEAD`，并在结果中报告当前 HEAD、baseline HEAD 和祖先检查结果；对正常的文档提交是否可通过；基线不在当前历史时是否失败；
- 31 个输入 pin、53 个证据项、14 个模型源码 pin、数据/缺口计数、R1 `DRAFT_BLOCKED` 检查是否保留；
- v1.4 与 v1.3 新版本 manifest 是否自洽，v1/v1.1/v1.2/v1.3 历史 hash 是否与记录相符；
- 公开路径脱敏、报告源哈希与脱敏副本哈希、数据权利和 R1 授权边界是否未退化。

可运行只读校验命令 `python docs/management/v1_4/verify_package.py`。报告检查时间、真实仓库路径、分支、HEAD、v1.4 manifest SHA、工作区状态和检查范围；问题按 P0/P1/P2 给出路径、证据和最小修复，结尾选择“可接受管理设计”“修正后再审”或“证据不足”。本次审查不签发 R1 release，也不批准科学结论。
