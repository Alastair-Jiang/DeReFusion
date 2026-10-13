# 交给 DSH 的独立复核提示词

你继续担任 DeReFusion 的只读独立证据审查员。请在开始时核实主仓库路径、分支、HEAD、工作区状态；输入只读，不覆盖任何既有文件。当前待审结论及初始检查版本见：

- `research_work/project_management_2026_10_10/author_code_fidelity_2026_10_13/AUTHOR_CODE_DISPOSITION_V1.md`
- `SOURCE_IDENTITY_V1.json` 和 `SOURCE_BEHAVIOR_CHECK_V1.json`
- `research_work/project_management_2026_10_10/paper_fidelity_kimi_v2/SOURCE_REPORT.md` 与 `PAPER_VS_REPO_TABLE.md`
- 本地论文PDF仅在 `C:\Users\26843\Desktop\project\02_papers\DeReFusion_ASOC_2026.pdf`，SHA-256 `69b1dfcb6f4566917037ff50d5b28c8a32af385db40857e244bfc7345340cba7`；不要复制全文或页面入仓。
- 作者公开源码固定commit `d4824f0036001204152e5180776ffc01f5ea4edb` 位于忽略目录 `data/author-reference-20261013/`。

独立核实这三个具体问题：

1. 论文Table 3的16维/2头与Table 10的26.108k参数量分别写了什么；对项目报告所称32维平均参数量26,108的可比性作独立计算或指出其前提。
2. 固定作者commit的模型构造是否实际使用4头、README示例和命令行默认值分别是什么、公开仓库历史记录能否证明论文发表实验配置；不要以当前HEAD替代历史运行记录。
3. 训练循环每epoch评估测试集且早停基于验证集的描述是否准确；Close/MS损失通道描述是否准确；区分“存在测试集暴露路径”与“用测试集选择模型”。

只读查看公开代码与论文，不读取本地训练数组、预测、checkpoint或2026原始价格，不运行训练/评分，不联系作者，不改源码。输出一个新版本化只读复核目录（不得覆盖现有记录），含简明结论、逐条证据路径/行号或论文页码、输入哈希、交付哈希。明确列出已证实、无法判断及如何解决；不要给科学结果做背书，也不要依据结果推荐模型。完成后把目录路径和文件哈希发回给用户。
