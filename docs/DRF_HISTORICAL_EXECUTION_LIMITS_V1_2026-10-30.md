# 历史执行入口的限制记录 V1 — 2026-10-30

**状态：** 历史限制说明。这些文件是冻结的历史证据，本轮**没有修改其中任何一个字节**。本文件不授权任何执行，也不把历史入口表述为已修复。

## 1. 为什么单独记录

以下入口把"是否允许产生执行释放"或"角色包是否匹配"绑在 Python `assert` 上，或在协调器之外直接暴露 worker。用 `python -O` 运行（或直接调用 worker）时，这些检查会被移除或绕过。历史记录里已有的结果仍然有效为历史记录，但**这些入口不能作为当前的授权机制**。

## 2. 逐文件

字节绑定取自候选 index（`852065887fb5a80122f39102daa8afba2508d94f`）。

| 路径 | Git blob | SHA-256 | 门禁问题位置 |
|---|---|---|---|
| `reproduction/analysis/compression_replay.py` | `bc22f06690470d033479a9d4c7ad64c10569774e` | `12789496d303dfa71c54e682b985685f0914ca558ad81f9070beeba3ef4f511f` | `assert` 行 176、196、197、198 |
| `research_work/project_management_2026_10_10/compression_pilot_2026_10_13/run_pilot_v1.py` | `5b7047368283e47d4f5b6ff44a07de6e9394e60c` | `e478878ba7896cb527e7f1ae593e9277685375e5ac62af9a587e6e584c6ede30` | `assert` 行 158、159、161、163、169、172、174、208、209、228、229、230、345、346、347 |
| `research_work/project_management_2026_10_10/raw48_oos_lock_2026_10_13_v1_1/run_oos.py` | `a2e78793b155d02e3aacdf352ae206b0d41fabaa` | `82a25c6e73ece90190c3e3782904e0f93b6b69871c43216d1fa54bb3659e2a6e` | `assert` 行 47、48、49、53、54、70、73、76、81、82、92、93、95、106、111、116、124 |
| `.../shrink_exploration_2026_10_13/run_shrink_cdd_v1.py` | `ce3499cc0648339da43abf875776e581d84eac94` | `52081c0fd15d27a54fd8c28c056891bae8ba07678d3a31364da1514382c18000` | 无 `assert`；直接 worker 入口在 353–370 |
| `.../shrink_exploration_2026_10_13/run_shrink_cdd_v1_1.py` | `0273732f6fe47941af50e108a7d4f8cad607e250` | `2a4b2e9081e5ef7517bc3f297159914c5bdfd84bee7122a121c1ff213c122442` | 无 `assert`；直接 worker 入口在 353–370 |
| `.../shrink_exploration_2026_10_13/synthetic_preflight_20261013/run_synthetic_lifecycle_v2.py` | `b981bc86b69e8691c98f263f39aebf8ee90bc966` | `74c8383f1e01ad58c98fdfc307de08c4fc9e85325262709945008d96f3816943` | `assert` 行 44、234、235、271、272、273、274、283、284、304；直接 worker 入口在 324–353 |

## 3. 逐项说明

### 3.1 `compression_replay.py`（新入口的生成器）

- `release()`（187–204 行）先显式检查 authorization 的 decision / head / protocol_sha256 / scope / owner / basis，这部分用 `raise`，`-O` 下仍然有效。
- 然后 196–198 行用 `assert` 检查 synthetic 与 prepared 的 `result == 'PASS'`，以及二者的 protocol/runner 哈希一致。**这三行在 `-O` 下消失**，于是可以在 synthetic 或 preparation 未通过、或绑定不一致时写出 `EXECUTION_RELEASE_V1.json`。
- 176 行用 `assert` 检查派生 `mixed48` 载荷是否复现历史 pin。该断言消失时，prepare 会继续写出一份与历史不一致却被标为 PASS 的 preparation。
- 117–133 行的 `verify_sources()` 用的是显式 `raise`，包含 HEAD、`replay.code_sha256`、父协议哈希、源码归档与环境版本；这部分不受 `-O` 影响。问题集中在上述 `assert`。

### 3.2 `run_pilot_v1.py`（历史 pilot 引擎）

- `release()`（224–238 行）在 228–230 行用 `assert` 检查 synthetic/prepared PASS 与绑定；同样是 `-O` 可移除。
- 158–174 行与 208–209 行的 `assert` 覆盖 preparation 的角色包自洽（`np.array_equal`、键序、末列收盘价）。
- `worker()`（240 行起）在 345–347 行用 `assert` 校验传入路径必须等于已释放的 preparation 路径。**该检查消失后，worker 接受调用方给出的任意路径**。

### 3.3 `run_oos.py`（raw48 历史评估）

- 17 处 `assert` 分布在输入路径限制（47–54）、历史准备复原（70–76）、固定 checkpoint 选择与评分输入校验（81–116、124）。
- `release()`（79–84 行）直接写出 `decision='APPROVED'` 的释放记录，其依据是历史授权文本，不是可验证的授权对象。
- 结论：该文件只能作为历史执行记录阅读。任何重跑都需要新协议、新实现与独立审阅；**不能**把它当作当前授权机制。

### 3.4 CDD 两版 worker 入口

- `run_shrink_cdd_v1.py` 与 `run_shrink_cdd_v1_1.py` 本身不使用 `assert`；协调器路径（prepare → release → 冻结 roster → 评分）有显式检查。
- 但两者都在 `main()` 暴露 `--worker fit|evaluate`（353–370 行），参数可以绕过协调器直接进入 `fit()` / `evaluate()`。两者的"角色隔离"只是 `argparse` 的互斥参数检查（361、365 行），属于流程纪律，不是访问控制：调用方可以自己拼出 train/validation/test 路径。
- 结论：两版都保留为历史快照。未来设计必须把 worker 调用绑定到确切的 release、角色与冻结 roster，并配负例测试。

### 3.5 `run_synthetic_lifecycle_v2.py`

- `main()`（324–353 行）直接接受调用方的 `--train/--val/--out/--test/--checkpoint` 路径进入 train/eval worker。
- "只接受合成输入"是**假设，不是强制**：`read_role()` 只校验角色标签字符串，标签由调用方写入。因此合成入口不能仅靠角色标签声称隔离。
- 271–274、283–284、304 行的 `assert` 用于拒绝用例；`-O` 下这些拒绝不再成立。

## 4. 本轮交付的新入口

`reproduction/analysis/compression_replay_release_v2.py`（`compression-replay-release/v2`）：

- 全文件无 `assert`；所有先决条件失败都抛 `GateError`，CLI 以退出码 2 输出 `BLOCKED`。
- 检查：协议对 gate 版本与本文件哈希的绑定、协议 head 与实际 HEAD、`replay.code_sha256` 的**逐项落盘校验**、**runner 由 `replay.runner_sha256` 钉住**、authorization 的 decision/scope/head/protocol 哈希/owner/basis、synthetic 与 preparation 的 PASS 与 protocol/runner 绑定、preparation 各 arm/role 的 pin 与**被协议钉住的历史 preparation**一致。
- 历史 preparation 不是调用方可自由指定的参数：它必须是 `replay.code_sha256` 中被钉住的固定仓库相对路径；载入后再次哈希并与钉住值比较，释放记录写这个钉住值。
- 释放目录被限制在 `data/compression-replay-attempts/<安全名称>`；协议、授权、synthetic、preparation、runner 五个文件都必须是普通文件（拒绝符号链接）。
- 非 git 根目录必须显式传 `--allow-non-git-fixture` 并给 `--current-head`；真实使用时该分支不可达，除非有人主动开启。
- **互操作要求：** 因为 runner 现在必须被协议钉住，未来的 attempt 生成器必须先写出 wrapper（`run_pilot_v1.py`）、再计算其哈希写入 `replay.runner_sha256`、最后才写协议；否则协议生成后无法再改而不破坏授权绑定。冻结的 `generate()` 是先写协议后写 wrapper，因此不能直接复用。
- 只有 `--write` 且全部检查通过后才写 `EXECUTION_RELEASE_V1.json`，且不覆盖已有记录。
- 测试覆盖正常模式、`-O` 模式、缺失/篡改授权、错误哈希、未通过 preparation、未钉 runner、游离目录、符号链接记录、缺失 pin 字段等负例（47 项，见交付报告）。

**历史文件不在 main 基线内：** 本入口要替换的 `compression_replay.py`、`run_pilot_v1.py` 及其 `PREPARATION_V1.json` 只存在于 `docs/project-status-catalog-2026-10-10` 候选，不在 `main` 基线上。因此在 main 基线的树上调用本入口无法通过：已有历史协议没有 `replay` 对象，会停在"protocol has no replay object"；按新 schema 写、但钉了缺失路径的协议会停在"protocol code entry is missing on disk"。这是预期行为，不是缺陷；同时也意味着本轮**无法**在 main 基线上对真实历史记录做端到端演练，只能用合成 fixture 验证门禁逻辑。另外 `replay.runner_sha256` 现在是必填，任何既有协议都不满足本入口。

**这个入口不能做什么：** 它不修改、也不保护上述历史入口；历史入口在 `-O` 下仍然不安全。它不能让一份伪造的协议变得可信——协议与命名其哈希的授权都是仓库文件，attempt 内的 preparation/synthetic 也是本地文件，协同伪造这三者仍可通过一致性检查；最终锚点是 `decision_owner` 的人工决定。它只验证一致性，不验证该决定是否正当，也不证明 synthetic/preparation 真的运行过。

## 5. 本轮未做

- 未修改任何历史执行器的字节。
- 未创建任何真实实验释放，未运行训练、拟合或评分。
- 未删除或重命名历史协议、结果、审阅记录。
- 未把"外层包装"当作历史入口已修复的证据。
