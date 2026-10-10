# Codex / DSH 同步工作分配（v1.1）

## 共同基线

目标仓库 `[local repository root withheld]`，分支 `docs/project-status-catalog-2026-10-10`，HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`。v1 是 DSH 已审版本，manifest SHA-256 `4a0601afe97b5700d0836e3b4bdeab28bed278bc06430d2160cfc0a038dccde8`；原样副本保留在本地 followup 目录。v1.1 是按审查意见修订的新候选，不与其他 checkout 合并。

| 负责人 | 工作 | 当前状态 / 产物 | 完成条件 |
|---|---|---|---|
| Codex | 建立管理规则和逐项缺口计划 | v1 完成；v1.1 已修订 | DSH 对 v1.1 exact manifest 独立复核，问题闭环 |
| Codex | receipt→planned row 身份关联 | 729 路径、728 条逐条唯一映射、675 个不同计划行覆盖；每条记录含行键/行号/manifest hash | 不将 receipt 行数误作不同计划覆盖或科学验收 |
| Codex | receipt→environment/产物路径元数据关联 | 700 个 environment hash 命中；3,637 个声明产物按名字存在；hash 未重算 | 记录保留边界，不声称 payload 验证 |
| Codex | freeze-summary 来源/消费者追查 | 确认已提交 writer 状态不一致；仓库无 reader；仓库外 UNKNOWN | 保留历史文件，执行不依赖来源不明摘要 |
| Codex | 接着推进来源、权利和预算证据 | G01–G03、G08–G11 | 关闭项绑定输入、证据哈希与阻断范围；未知如实保留 |
| DSH | v1.1 管理包独立复核 | 通过 `DSH_REVIEW_PROMPT.md` 转交；manifest SHA 在转交时给出 | 对 v1 各问题复核关闭情况和新问题，给精确证据 |

## 交接

1. Codex 固定 v1.1 manifest 并发出复核提示词。
2. DSH 返回报告后，Codex 逐条处置、形成差异表。任何新文件都放入新修订版本，不改 DSH 正在检查的包。
3. 如有争议或修复影响管理边界，Codex 发单独的差异复核提示词；DSH 只审指定 diff，不改文件、不作执行放行。
4. 包复核闭环后，继续限定范围的数据 QA 资格准备。真实数据各阶段须由负责人满足条件后签发 release；工作分配不是一次运行授权。

冻结摘要是既有 tracked diff。本轮只读检查，不把它当作本轮写入，也不覆盖原件。工作区其他既有改动全部保留；跨 checkout 必须先比哈希、来源和差异。
