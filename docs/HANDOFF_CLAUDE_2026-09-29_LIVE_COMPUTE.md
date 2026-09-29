# Claude Code 接手提示词（2026-09-29，约 16:54 北京时间）

请接手 DeReFusion，继续正在运行的实验及实时硬件流程图网站。先验证当前状态；以下数字是交接快照，会变化。不要重启健康任务，不要重复计算。用户要求效率优先：没有资源排队和逻辑冲突就并行推进，不能让可做的工作一直等串行步骤。

## 工作区与硬约束

- 原训练工作区：`C:\Users\26843\Documents\ChatGPT\redefusion`。
- 原 `main` / `origin/main` 已推送提交：`f6093f1d85f13613dfe1a3ac0d25b554ca83ccd3`。
- 网站独立工作区：`C:\Users\26843\.codex\worktrees\live-hardware-flow\redefusion`，分支 `codex/live-hardware-flow`，网站在 `research-ops-site/`。
- 原工作区 HEAD 被 Stage C 授权精确绑定；训练期间不得提交/切换/拉取导致 HEAD 改变，也不要修改科学源码、冻结参数、数据、receipt 或授权。网站改动在独立分支提交；此分支目前尚未提交/推送。
- 动手先看 git status/log，保留用户改动和所有未跟踪产物。严禁 git add -A、force push、删除/覆盖 attempt、因硬件差异废弃已有计算。
- 先完整读取 `C:\Users\26843\.agents\skills\derefusion-experiment-governance\SKILL.md`。网站为已有 Sites 项目，遵循其技能，用户只要 localhost，不发布云端。
- 用户已批准 Stage C 全部 360 fits 与远端 B 并行；Stage D 未获启动授权。不要擅自启动 D 或追加模型队列。

## 正在执行

### 本地 RTX 5060 Ti：Stage C

- Python：`C:\Users\26843\anaconda3\envs\derefusion-5060ti\python.exe`。
- Python 3.11.15 / torch 2.7.1+cu128 / CUDA 12.8 / cuDNN 90701 / numpy 2.1.2 / pandas 2.3.3 / sklearn 1.7.2。
- 父进程 PID 30212；后台运行，不依赖可见终端，但电脑关机会中断。
- 全清单：30 assets × DLinear/DeReFusion × horizons 1/24 × seeds 2022/2023/2024 = 360，禁止按结果筛选。
- 最后快照：58/360，正在 BTCUSD / DeReFusion / h24 / s2023，状态 running。
- 输出/进度：`reproduction/results/phase1/local-5060-stage-c-v1/batch_progress.json`。
- 总日志：`reproduction/logs/phase1/stagec_5060_20260929_v1.stdout.log`、`.stderr.log`；每 attempt 有 run.log。
- 决策：`docs/PHASE1_STAGE_C_EXECUTION_DECISION_2026-09-29.md`；授权：`reproduction/results/phase1/local-5060-manifests/authorization-local-5060-stage-c-v1.json`。
- 16:35:52 开始，原预算 8h；逐 epoch atomic recovery 已实测读取成功，含 model/optimizer/early stopping/AMP/RNG/next_epoch。真正失败与预算中断必须区别处理，不覆盖旧记录。

### 云端 RTX 8000：Stage B 剩余 TimesNet

- SSH：端点不记入本文档，形如 `ssh -p PORT USER@RTX8000_HOST`。主机、端口与密码都不写入本提示词/代码/日志，必要时向用户获取；已有本机私钥需要未知口令，不能假装可用。
- repo `/data/coding/DeReFusion`，tmux `rtx8timesnet`，环境 `/data/envs/phase1-rx8000/bin/python`，源码固定 `096c68b`，不要训练中 pull。
- batch `reproduction/results/phase1/rtx8000-timesnet-remaining-v1`，55 fits，非确认性执行轨道。
- 16:53 左右 SSH 实查：4/55，BTCUSD h24，tmux 活着，GPU 100%，约 11.1GiB。进度 JSON 只在 fit 边界更新，旧时间不等于卡死。
- 开始 UTC 07:38:58；原 8h 截止约 UTC 15:38:58，另扣原 shutdown buffer，不能任意续预算。
- P4 已释放，不再尝试连接；既有 245 包全部 CPU 摄入审计通过。P4 torch 2.5.1/cu121 与 5060 2.7.1/cu128 比较包含软件栈差异，不能声称纯硬件等价。

### 回传、CPU 审计

- 隔离 receiver 环境：`C:\Users\26843\.codex\tools\redefusion-receiver\Scripts\python.exe`，Paramiko，经南大镜像安装；不要污染科学环境。
- 正在运行 SFTP receiver（Codex retained session 34036，Claude 不一定能操控此会话，先检查实际进程），每 60s 轮询，总 6.4h，自 UTC 08:38 左右起。
- 回传根：`reproduction/results/phase1/rtx8000-intake-20260929-v2`，4 包完整验证并发布；incoming 半包保留，完整包 SHA 校验后 atomic publish，不覆盖。
- 源码新增 bounded prefetch 32 requests，287MB checkpoint 回传约 17–20s。
- Stage C CPU consumer PID 26972、远端 CPU consumer PID 25200；分别写 `consumer-stagec-20260929-v1` / `consumer-rtx8000-20260929-v1`。
- 摄入检查 SHA、配置/身份、数据/键、truth、shape、finite、六指标重算，不作科学结论。

## 最新 GPU 利用率工作

用户最新要求“提高5060利用率”。实测小型 DeReFusion 训练约 0.42–0.50s/epoch，GPU 通常 16–20%；fit 间有进程冷启动、CPU 绘图和打包，不是显存不足。不要为刷利用率改变冻结 batch size/d_ff/精度、停止已有训练或做无意义 benchmark。

已在 C 继续运行时并行做完一个 RTX8000 checkpoint 的只读 GPU 推理复核，无 optimizer、无新 fit、无生产产物覆盖：

- 输入：`consumer-rtx8000-20260929-v1/pass-20260929T084403.831930Z-bdd61d205db54489892c1f7f707a51f8/intake/{selected-manifest.csv,reference-index.csv}`。
- 输出：`reproduction/results/phase1/checkpoint-forward-rtx8000-on-5060-v1/report.json`。
- BTCUSD TimesNet h1，约 13.8s，`completed_descriptive_only`，truth bitwise exact，原输入哈希不变；无预承诺等价阈值，所以不允许等价、pooling 或排名结论。
- 此 audit 进程已结束，不要当作还在运行。原桥接 fixed-checkpoint audit 68 项也已完成。
- 可继续对其余已 CPU 审计通过的远端包开展相同只读复核，逐包去重、独立输出目录、保存输入清单；与 C 并行前顾及 CPU/GPU 资源竞争。当前 C 源码/授权不要改。若要多 fit 并发、改变绘图/训练 harness，先形成前瞻修订与无重复的任务所有权方案，不要偷改活跃确认实验。

## 实时流程图网站：未验收

- 用户要 `localhost:8964` 展示各硬件任务、进度、训练/回传/审计依赖及更新时间，保留原 JP Morgan 风格。
- 网页开发服务器正在网站独立工作区运行，8964 首页目前 **HTTP 500**，未定位原因，不能宣称已完成或让用户以为可用。
- `http://127.0.0.1:8970/status` 只读后端运行；8964 `/ops-api/status` 代理已成功返回真实 JSON。
- 新前端：`research-ops-site/components/live-compute-flow.tsx`；修改 `app/page.tsx`、`app/globals.css`、`vite.config.ts`。5s 刷新、任务节点、SVG 依赖线、硬件卡片、详情；不暴露密码/授权/原始命令。
- 后端：`reproduction/analysis/serve_phase1_ops_status.py`，使用 `--repo-root C:\Users\26843\Documents\ChatGPT\redefusion`。仅 loopback status/health，5s cache，固定 bounded nvidia/CIM probes。
- 后端 14 tests / receiver 11 tests通过；最新 3 个后端 tests 已复制到网站工作区，但 root 最后联合运行是旧 22 tests 通过。
- 网站 node_modules 是指向原网站安装的 junction；ignored `build/sites-vite-plugin.ts` 已从原网站复制，不要删插件或重装全部依赖来碰运气。
- 未完成：诊断首页500、浏览器实测/响应式、修正轮询 timeout 旧状态标记和左向连线、去除侧边栏/下载交接/旧静态页面的过时“领先3提交”“B锁定”等伪实时信息（其他原型页面标历史）。
- 后端 GPU replay queue 尚未计入刚完成的1项复核；需接入真实 audit reports 去重更新，不要把待审计都标忙。
- receiver 的 `--remote-health` 固定只读 SSH probe 已写在网站工作区版本，运行中的 receiver 尚未启用。可在安全轮询边界换用该版本、绝对回传根、原剩余预算，不能延长租期；新快照 health 可显示远端 GPU/process 真状态。旧 batch JSON 与新收到 metadata 的时间须分开。
- 验证完成后显式路径提交并推送 `codex/live-hardware-flow`；活跃 C 的原 main 不动。网站启动方式/桌面快捷方式还需保证指向实际更新版本。

## 模型和节约用量

用户要求对话、定时任务使用 GPT-6 Luna。`C:\Users\26843\.codex\config.toml` 默认 model 已设 `gpt-6-luna`；当前活跃 Codex 对话模型未能确认已切换，不要宣称切换成功。仅存定时任务 `p4-stage-b-30-minute-monitor` 的 model 元数据已设 Luna，仍保持 PAUSED（P4 已结束）。工具 heartbeat 更新不支持 model 字段，所以不要重新创建/激活该过期任务。简洁输出，避免反复全仓库扫描和不必要新会话。

## 接手顺序

1. 先只读检查 C/8000/receiver/consumers 健康、时限和已完成产物，不重复启动。
2. 并行推进已获授权的 GPU 只读复核和 CPU 摄入；评价吞吐而非追求表面100%利用率。
3. 完成并验收实时网站（首页当前500是明确未完成项）。
4. 只在网站分支显式提交/推送；保留所有历史/失败产物和冻结训练源。
5. 训练齐备后再按门禁审计完整覆盖并解释，禁止现在提前宣布 Stage B/C 科学结论。
