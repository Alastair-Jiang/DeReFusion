# DSH 独立复核任务：新 CDD 来源与缩小探索执行

你是 DeReFusion 项目的独立复核员，负责检验证据、指出具体缺陷。Codex 是本轮决策与写入负责人。请只读工作，不启动训练、不改文件、不接触凭据、不联系供应商、不读取历史 Yahoo 原始 CSV。

工作区：`C:\Users\26843\Documents\ChatGPT\redefusion`；分支 `docs/project-status-catalog-2026-10-10`；预期 HEAD `a74126c11d857da8514074b72282adc8d47f28a7`。先核实实际身份和工作区状态；发现漂移，记录并停止依赖旧版本。

主审目录：`research_work/project_management_2026_10_10/shrink_exploration_2026_10_13/`。阅读 `CDD_LOCAL_RESEARCH_QUALIFICATION_RELEASE_V1.json`、`CDD_QUALIFICATION_RESULTS_V1.json`、`SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json`、`run_shrink_cdd_v1_1.py`、`CDD_MATRIX_SYNTHETIC_CHECK_V1_1.json`、`CDD_PREPARATION_MANIFEST_V1_1.json`、`CDD_MATRIX_EXECUTION_RELEASE_V1_1.json`，以及 `docs/DRF_CDD_PROJECT_STARTUP_DECISION_2026-10-13.md`。先复算本轮文件哈希，对照 release 与进度清单；不要混用 v1 与 v1.1。

请并行于 Codex 当前运行开展以下复核，无须等全部拟合结束：

1. 核对官方 CDD about/terms/Bitstamp catalog 的“研究、非商业、可自动下载 CSV”依据与保存的日期化快照。允许联网查官方当前页面，记录新增来源。明确提供方研究用途邀请支持的范围、第三方权利免责声明及未获准的商业/公开再分发范围。需要的是具体冲突或适用性证据；供应商签名并非唯一可核验依据。不要把项目授权写成外部主体批准。
2. 核对新 BTCUSD/ETHUSD 来源版本、raw 哈希、UTC 日线、USD 单位、完整性和训练/验证/测试边界。你可只读新 CDD 角色包及其元数据作复核；不读取旧 Yahoo 文件，原始值和预测不能复制到公开输出。
3. 静态核对每档训练 scaler 仅由对应训练上下文/目标拟合，测试集不影响拟合、ridge lambda、checkpoint 或资产排序；共同预测键是否完整，末批是否保留。核对 96 个上下文日被明确计入实际历史跨度。
4. 核对模型源码 pin、配置和参数量、600 步固定预算、失败保留、版本修复边界。v1 的 metadata 序列化失败已经保留；v1.1 修复不能被表述为旧 v1 成功。
5. 如结果已出现，核对 24 个 F fits、14,400 optimizer steps、731 测试键、2024/2025 分段、均方误差/RMSSE计算与 roster 冻结时间；分开计划、收到、内部一致性核对、独立复核完成的数量。不把两项问题的共用 full-history fits、seed 或年份当作独立市场样本。

首批结果及复核材料已经生成：`docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md`、`CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json`、`CDD_INTERNAL_CONSISTENCY_AUDIT_V1_2.json`、`audit_and_report_cdd_v1_2.py`。拟合/评分仍是 v1.1，内部复算器的最新版本是 v1.2。旧复算器把 CSV 中 NumPy float32 的短字符串直接当 float64 作精确比较而失败；v1.2 先恢复 float32 再以 float64 复算，原始拟合、预测、指标 JSON 均未改。请专门核查这项 codec 处置，并保持你自己的独立复核数量与 Codex 内部核对数量分开。

交付：在当前会话回复一份只读报告，列出检查时间、路径/分支/HEAD、实际复算 SHA、P0/P1/P2 问题与定位、对“有限本地研究放行”的明确结论、尚未核验项。先报告任何会影响当前运行有效性的具体重大缺陷，再给普通记录修订建议；不要自行暂停、重跑或修改实验。
