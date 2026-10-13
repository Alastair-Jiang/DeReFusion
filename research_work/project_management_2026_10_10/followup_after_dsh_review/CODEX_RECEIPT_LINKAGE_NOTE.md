# Codex 后续元数据关联记录

记录时间：2026-10-10。仓库主路径 `[local repository root withheld]`，分支 `docs/project-status-catalog-2026-10-10`，HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`。这些材料在 DSH 已收到的管理包 v1 之外，避免改变当前审查对象。

## Receipt 到计划行

`docs/management/v1/receipt_manifest_join.json` SHA-256 `61a1adadbff4ad2bd5e4f78685d42460ee902fdc5cdefd0be7c11adb79d389ea`：729 条 receipt 元数据关联 4 个 Phase 1 manifest 共 819 行。728 条唯一映射，1 条 `resource_blocked` 无运行身份。状态陈述为 `calibration_pass` 28、`completed_unreviewed` 699、`interrupted` 1、`resource_blocked` 1。completed 仍未经审查。

## 环境与产物身份

`receipt_environment_artifact_index.json` SHA-256 `0889418329440115121d557e99aa60a7c1ff25e3ae178ebf1c84af41609699e3`。在 Phase 1 结果目录内找到 651 份命名为 `environment_fingerprint.json` 的元数据文件；700 条含环境指纹哈希的 receipt 都能匹配至少一份本地文件字节哈希。29 条 calibration/resource-blocked 没有环境指纹引用。相同环境文件在多条 attempt 和多个快照中重复是预期情况；匹配仅表示哈希相等。

Receipt 声明了 3,637 个产物条目；按文件名核对，3,637 项都存在，0 项缺文件。索引记录了实际字节数，但没有与任何声明大小比较。此项没有重新计算 checkpoint、metrics/pred/true 数组或 run log 的内容哈希，也没有打开这些文件内容。因此只确认路径级完整性，不能确认声明 hash 正确、数值正确或实验有效。

## 边界与后续

这是 Codex 自己生成的元数据检查，尚无独立复核。原始管理包 v1 的 `hashes.json` 保持不变，SHA-256 `4a0601afe97b5700d0836e3b4bdeab28bed278bc06430d2160cfc0a038dccde8`。待 DSH 完成该固定版本审查后，可以把本记录作为追加材料交他复核；如需引用为正式目录，建立 v1.1 或 v2，并新增该 JSON 哈希，不改已送审版本。
