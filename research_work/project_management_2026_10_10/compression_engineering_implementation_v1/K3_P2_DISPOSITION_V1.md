# K3 独立工程复核接收及 P2 补记

主仓库 `C:/Users/26843/Documents/ChatGPT/redefusion`，分支 `docs/project-status-catalog-2026-10-10`；接收时 HEAD `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554`。K3 交付摘要与 24 项输入摘要复核匹配，原 62 个暂存文件保持审查时字节。K3 判定工程包适合提交：P0=0、P1=0、P2=6。具体绑定与完整行尾修复清单见同目录 `K3_ACCEPTANCE_RECEIPT_V1.json`。

本补记新增说明，不覆盖已审查源码、manifest、验收回执或 K3 原稿。用户已有项目负责人委托和 Git 提交/推送授权仍有效，不需要重复索取。

| 项 | 接收处置 |
|---|---|
| P2-1 行尾修复计数 | 完整逐文件核对为 **18** 处，仅 CRLF/LF 不同：16 个 shrink 文件加 `docs/DRF_CDD_DSH_REVIEW_DISPOSITION_2026-10-13.md`、`docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md`。旧回执的 16 只覆盖 shrink 扫描范围，不代表整个提交；补充回执保存全部 18 项 old/new blob SHA。 |
| P2-2 Torch wheel 未留本地 wheelhouse | 接受为非阻断的离线能力限制。Torch 已安装，官方 URL 与 SHA 见 `requirements/torch-cpu-win311-wheel.txt`；wheelhouse 仅存九个 PyPI 依赖。当前不能声称完全离线可重建 Torch；如需完全离线重建，应先取得并核验该 wheel，保存在私有软件缓存，不进入 Git。 |
| P2-3 runner_sha256 含义 | 新 replay 的 `runner_sha256` 指向新尝试的 `run_pilot_v1.py` **wrapper**。实际计算引擎、适配器、预处理与加载器等由 `replay.code_sha256` 分别绑定。审核时须检查 wrapper 和该字典，不能将 wrapper SHA 当作唯一计算代码身份。该说明是重签流程 v1 的补充契约。 |
| P2-4 loader 名称匹配前提 | 私有映射只匹配 `layers.RevIN` 与 `layers.derefusion_components` 的精确 from-import。归档源码的这两行已固定在硬编码 source pins 中；`verify_archive` 在每次加载前拒绝任何字节漂移。该加载器不是适用于任意 import 风格的通用隔离器；改变源码/import 风格需要新归档版本、加载器审查与测试。此说明补充 bundle manifest 的使用前提，不改变已复核 manifest。 |
| P2-5 合成留档与 fixture 计数 | bootstrap/drift 两项测试每轮会各保留一个 gitignored 合成 attempt，记录生成及故意漂移的门控实证，不含真实输入。回执 source_export_files=62 指导出后、测试前的源码文件数；复核时 fixture=68 为额外六个测试 metadata 文件。两种口径不同且自洽，不能把测试后的 fixture 当作原导出快照；原 zip SHA 仍绑定导出快照。 |
| P2-6 反斜杠契约 | 新清单路径限定仓库相对 POSIX 分隔形式，拒绝全部反斜杠属于接口约束。不能将 resolve_relative 宣称为支持所有合法 Linux 文件名的通用工具。历史 Windows 路径仅在冻结元数据的专用 ETH f100 rebinding 入口处理。 |

## 当前验收边界与下一步

工程验收已接收，13 项合成检查由 Codex 与 K3 分别通过；提交不构成科学验收。真实两臂复跑仍 NOT_RUN，压缩批全面独立科学验收仍 PENDING，raw48 正式协议未签发。新的 HEAD 必须生成新尝试、准备匹配私有输入、签发精确绑定的正式执行授权，不能直接运行旧释放。

后续优先顺序：先补新 replay 的完整审计适配；再在新 HEAD 上执行旧两臂复现并逐键核对张量、checkpoint、覆盖和损失；通过后才推进 raw48 新协议。上游历史快照可得性、跨平台逐位一致性、920 条历史 private-like 路径的独立处置保持待核实。

本次集中提交范围包括工程代码与文档、原压缩试验文本记录、K3 两轮规划/复核及 18 处字节封存。源数据、角色数组、逐键预测、checkpoint、venv 和 wheelhouse 不进入提交；五项用户已有改动保留在工作区。
