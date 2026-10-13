# 压缩试验工程实施包 v1

接续 K3 的 `compression_engineering_plan_k3_v1`，以 `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554` 为基线。原批、K3 原稿和五项此前已有用户改动保留。实施处置见 `docs/DRF_COMPRESSION_ENGINEERING_DISPOSITION_V1_2026-10-13.md`。

## 交付状态

1. 私有边界：已提供按新增/本次修改范围检查的策略与脚本；旧历史 920 个 private-like 路径另列，未删除。
2. 源码归档：三个源码文件和空 init 原字节归档；增加隔离导入加载器、manifest 与 Git 行尾封存。
3. 原压缩试验：十个文本工件和报告已纳入本次暂存包；独立科学验收状态保留原样。不是新实验结果。
4. CPU 环境：版本配方与 Windows 精确 wheel 配方；全新 venv 的实际验收见 `VALIDATION_RECEIPT_V1.json`。
5. 重签：提供新 HEAD/相对路径 bootstrap，以及独立授权门控和流程说明；不自动重签训练。真实输入重建和完整新尝试审计仍是后续任务。
6. 固定模块：已提取纯函数、配置/跨度/缓存身份；测试全部合成。
7. raw48：仅 `compression_followup_2026_10_13/PROTOCOL_V0.1-DRAFT.json`，未签发未训练。

额外修复：此前父批有 16 个 Git blob 因行尾转换不等于冻结的工作区字节。新暂存包保存实际执行字节，变量值、源码文本和冻结 hash 不改；原提交保留。

## 验收与保留事项

本轮没有新真实数据拟合、评分或测试角色读取。输入文件只读哈希核对；工程检查使用合成数据。最新代码与新环境均运行了针对性测试，另从暂存树导出仅代码/文本的源文件夹验证字节和依赖；该文件夹不是一个完整 Git checkout，不代表真实数据全链复现。

新代码还需要 K3 对新增差异的独立工程复核。暂存包是具体可审查结果，不缺用户项目提交授权；独立复核后再作集中提交/推送。已有五项用户改动不纳入本包。

标准库源码加载器采用私有 import 映射，保留原模型字节；whole-model pickle/TorchScript 不在本版本接口内，checkpoint 只保存 state_dict。新 replay 支持两旧臂，不包括 raw48；没有完整新尝试审计适配，也没有自动 CSV 重建功能，不能宣称所有 P0/复现事项都已消失。

源码/文档位置详见 `IMPLEMENTATION_MANIFEST_V1.json`；验收记录见 `VALIDATION_RECEIPT_V1.json`；K3 下一轮提示词见 `K3_REVIEW_PROMPT.md`。
