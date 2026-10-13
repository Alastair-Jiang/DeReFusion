# 管理包 v1.4 独立只读复核记录

复核时间：2026-10-10 11:26 UTC。复核者：Codex 子 agent（独立只读复核）。仓库 branch `docs/project-status-catalog-2026-10-10`，HEAD `eacb644e3db7c4f4b1d8bd5d1096959165f430f8`。

v1.4 README 中“尚待独立复核”是包冻结时状态；本记录是随后完成的复核结论。目标包 `docs/management/v1_4/` 的 `hashes.json` SHA-256 为 `bf095a4c19d67b1da1cc9d7e94253e8a2dcc5671acc01cf782b3917bdb418fb8`。清单覆盖 24 个文件，全部匹配；目录共 25 个文件（含清单）。只读验证命令 `python docs/management/v1_4/verify_package.py` 通过，`passed=true`、`errors=[]`，并报告 `baseline_head_is_ancestor=true`。

| 检查项 | 结果 | 证据摘要 |
|---|---|---|
| 发布后 HEAD 处理 | PASS | 校验器使用 `git merge-base --is-ancestor baseline.head HEAD`；当前 HEAD 在基线之后且通过校验。若基线不在当前历史中，校验失败。 |
| 固定输入与状态检查 | PASS | 31 个输入 pin、53 个证据项、14 个模型源码 pin、61 个数据条目、18 个缺口均通过；R1 保持阻断。 |
| 历史包完整性 | PASS | v1、v1.1、v1.2、v1.3 的文件均匹配各自 manifest；manifest SHA 分别为 `4a0601afe97b5700d0836e3b4bdeab28bed278bc06430d2160cfc0a038dccde8`、`ec414113e75e0068b96fe85e76b3b20c43c3ae6f9417493d05ed2f206cea71b4`、`476c7f533f8a5e8ca8deed1b9cf5f1fdb0db85a50f2fbc83e720fdbc971d809d`、`5e1e049333a3a9f359d1f478ba86e5a6f4b3b2839b506ed92286424b8b99c251`。 |
| 公开路径与证据边界 | PASS | 包内无本机绝对仓库路径、用户名路径、UNC 用户路径或 Codex 附件路径；未读取价格、预测/真值、checkpoint、运行日志或凭据。 |

结论：v1.4 管理候选通过独立只读复核。此结论不签发 R1 release，也不批准科学结论。
