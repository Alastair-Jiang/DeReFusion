# 给 Claude Code 中 Kimi K3：新增工程差异独立复核

你继续担任 DeReFusion 独立工程审查者。Codex 已按你的计划落实第一批工程包，并修正部分原计划表述。请只读审查实际新增差异与暂存 Git tree，不修改、不清理、不训练、不评分、不提交推送。

主仓库：`C:/Users/26843/Documents/ChatGPT/redefusion`。基线分支 `docs/project-status-catalog-2026-10-10`，基线 HEAD `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554`；先核对当前状态，任何实际变化单独记录。

先读本目录 README、IMPLEMENTATION_MANIFEST_V1.json、VALIDATION_RECEIPT_V1.json，以及 `docs/DRF_COMPRESSION_ENGINEERING_DISPOSITION_V1_2026-10-13.md`。核对清单哈希后阅读所有新增源文件与针对性测试。

重点检查：

1. 三份 archive 源码与旧 pin 的字节一致性、init pin、私有 import 映射是否加载正确依赖且不污染全局 layers；source drift 是否拒绝。
2. 聚合模块是否对完整定义域保持固定函数语义、输入不变/目标不接触、错误拒绝、配置/跨度/缓存身份足够；测试是否含真正的独立参照。
3. 新 replay bootstrap 是否绑定真实 HEAD、所有实际实现依赖、历史 metadata 和 CPU 环境；是否保持旧计算逻辑、使用新尝试和仓库相对路径；未授权的 release/run 是否 fail-closed。关注可变全局/相对路径、输入 manifest 验证、错误记录、输出与预算。
4. 逐字节封存：原父批 16 文件仅 CRLF/LF 差异是否成立，stage blob 是否等于冻结工作区文件；没有变更协议/数据/结果含义。新包的 -text 规则和 hash 清单是否自洽。
5. 机器边界策略是否准确限制新增提交、保留历史存量，未将 920 条历史存量当作新增数据发布许可；任何 raw/NPZ/逐键预测/checkpoint/环境是否进入 stage。
6. 环境验收是否确实使用全新 venv、匹配依赖、无真实训练；暂存源夹只是源依赖/字节验证，不是完整 Git checkout 或真实复跑。
7. raw48 草案是否明确“等容量联合表示对照”，没有声称完全分离覆盖和分辨率；没有把 25 个混合位置写成 100 天真实信息；接受界不能按新分数事后补设。

允许用新验证环境运行两个合成 unittest 文件和 `check_artifact_boundary.py`，不运行任何旧/新 prepare/release/run 真实阶段、不读测试数组、不重放真实训练。已生成的私有工程 fixture/软件 wheel 可以只读核对元数据；不得外传数据和凭据。原压缩批全面独立科学验收仍 PENDING，不因本轮工程复核改成完成。

请输出新目录 `compression_engineering_review_k3_v1/`，包括 REVIEW.md、FINDINGS.json、INPUT_HASHES.json、DELIVERABLE_HASHES.json；目录存在则升版。明确 P0/P1/P2、具体代码位置、可复现实证、工程提交是否可接受，以及剩余真实复现/审计缺项。不要以只读静态检查声称训练已复现。
