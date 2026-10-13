# 压缩试验重新绑定与执行授权流程 v1

旧协议、旧执行器、准备记录和结果是历史工件。提交工程改动后 HEAD 会移动，旧命令按原设计拒绝执行，不能直接改旧 `head` 字段来绕过。新工程只提供新的两臂复现入口，不自动放行训练，不包括 raw48 新实验，也没有补齐旧 24 项矩阵的新执行器。

## 新入口

`reproduction/analysis/compression_replay.py` 生成新的 gitignored 私有尝试，绑定当前 HEAD、冻结计算执行器、隔离归档加载器、预处理模块、历史协议/结果及环境配方。三个旧模型文件保持原始字节，通过 `models/derefusion/bundle_v3_pin/loader.py` 的模块局部导入映射加载，不借助顶层 `layers` 的偶然内容。

先提交并核验工程源码；新机器检出该实际提交后再生成尝试。这里不预填未来提交 SHA，避免自引用哈希或虚构 HEAD。

```powershell
python -B reproduction/analysis/compression_replay.py --name replay-001
python -B data/compression-replay-attempts/replay-001/run_pilot_v1.py --help
python -B data/compression-replay-attempts/replay-001/run_pilot_v1.py --phase synthetic
```

上述操作不训练真实数据。生成的 `EXECUTION_AUTHORIZATION_TEMPLATE.json` 明确 `NOT_APPROVED`，不是正式授权。

## 私有输入重建与重新准备

需要两个原始 ETH f100 train/validation NPZ 及其 keys manifest，放在当前仓库的 `data/shrink-cdd-20261013-v1/packages_v1_1/ETHUSD_f100/`。旧 Windows 前缀只从冻结、已校验的历史 metadata 提取，新的准备记录使用仓库相对路径；新 worker 以当前仓库为工作目录，拒绝不匹配释放的输入。

这些 NPZ 不进入 Git。可以由有权访问的本地归档提供，先比对历史 pin；若只有原始 CDD 快照，需要依原父批窗口/缩放/键算法在新版本的准备程序重建并比对。当前入口没有自动下载或原始 CSV 重建功能，不能声称无数据归档即可完整复跑。

供应商每天更新的 CSV 全文件哈希不保证等于历史快照，不能把今天下载的不同字节直接替换旧 raw pin。即使前缀数值相同，也要记录新来源版本并重新资格核验；不能无条件重签成旧数据。没有合法、精确匹配的输入时，停在合成阶段并列为输入阻断。

```powershell
python -B data/compression-replay-attempts/replay-001/run_pilot_v1.py --phase prepare
```

准备会验证原 train/validation 包及 manifests，并要求 mixed48 的派生载荷逐字节匹配旧 pin；任何漂移立即停止、保留旧工件。不会读测试角色数组。

## 精确绑定的正式授权

由项目执行负责人审核新协议、实际 HEAD、环境、资源和输入后，在新尝试目录另写 `EXECUTION_AUTHORIZATION.json`。必需字段：

```json
{
  "decision": "APPROVED",
  "scope": "two-arm-validation-replay",
  "head": "实际当前 Git HEAD",
  "protocol_sha256": "新尝试协议文件的实际 SHA-256",
  "decision_owner": "实际作出项目授权决定的人或代理",
  "authorization_basis": "具体用户委托与审阅后的本地研究执行决定"
}
```

模板示例不是实际授权；不得使用供应商签署批准等不真实身份。已有用户项目委托允许 Codex 作出内部执行决定，无须逐项重问，但不能代表外部主体清除权利。

随后才允许新 `release`，它额外绑定授权文件哈希。授权被撤销或修改会使原释放失效。`run` 仍执行两组各 600 步与原资源限制，拒绝覆盖或静默重试；失败采用新的尝试名称并保留现场，不删除旧 runs。

## 真正复现验收，尚未在本轮执行

raw96 的张量哈希必须为 `1a438fc30394c45ac4552a14b6f1c26d8bd9b0dee1bac205259cb89611f96270`，验证 MSE(F) 必须为 `2092.513855618721`。

mixed48 的张量哈希必须为 `3166c0d126c00a10693e1d6f991e11485e29c9f116cff1f6df24ea7b709644e1`，验证 MSE(F) 必须为 `2242.5347423209273`。

这两个断言由复现验收者根据新结果重算，不是生成脚本保证的事实。只通过初始化与合成检查不能宣称训练已逐位复现。若跨平台无法逐位一致，需要另一个预先定义容差的复现协议，保留原严格结果而非追认成功。

真实复跑仍须恢复全部 checkpoint/逐键预测、验证选择、覆盖与损失核对，不能只核对一个汇总指标。原内部审计脚本依赖旧目录；新尝试的完整独立审计适配尚待实施。新入口不构成科学验收。
