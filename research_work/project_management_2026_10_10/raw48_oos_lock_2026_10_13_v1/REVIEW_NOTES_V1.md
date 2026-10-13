# Raw48 一次锁定时间外推：独立静态工程审查

PASS：run_oos.py、PROTOCOL_V1.json、PLAN_V1.md、EXPOSURE_REGISTER_V1.md以及execute_bound.py已只读审阅。不读取2026价格、任何新测试数组或科学checkpoint，不运行评价/训练，不修改源码/协议。preflight的动态恢复PASS来自父执行记录，本审查不冒称独立再次恢复。

## 主检查

- 285个目标键为2026-01-01至10-12，预定子段181/104；48日上下文从2025-11-14起且每个x仅用目标日期之前48个完整日。UTC当前2026-10-13 06:41:48已晚于最后bar完成时刻10-13 00:00，目标已成熟。此为时间契约核验，不证明供应商实际发布延迟/无修订。
- collect仅数值解析2018-2022及2025-11-14至2026-10-12区间；日期、Unix秒/毫秒、UTC午夜、symbol、重复、有限正值和OHLC包络检查。连续日期全表np.stack缺日期会停止。旧2024/25测试角色包不打开，但2025末合法上下文确会从原CSV读取，不能说未接触任何2025数值。
- 训练float64均值/总体std和RMSSE分母从2018-2022重建；与父f100全部上下文覆盖区间一致，所有1730旧训练x/y重新逐位核对及Close标准差/分母精确校验。这里重建既有scaler身份而不是重新拟合候选变换；2026不进入scaler。
- 三个旧F checkpoint使用已固定validation-selected best及state hash；没有更新权重、ensemble或从2026重新选择seed/表示。模型输出标准化Close经训练std/mean反变换到USD；L沿旧float64特征中心/coef/intercept反标准化；真值为原始float64Close，P取精确前日原始Close。同键同单位，与旧float32标准化真值存在精度口径差异已声明。
- 主量是三个seed损失算术均值减L，而非先平均预测再评分；全期与两个子段全部报每seed/P/L、MAE/MSE/RMSSE，无阈值/统计裁决。
- check在评价前绑定真实HEAD、Python/torch/numpy、源码/历史/原CSV字节及全部模型包文件hash；release机械核对本review的runner/protocol身份，controller又机械比runner/protocol/controller三hash。输出限定新目录和private子树、xb拒覆盖，private写前32MiB预算。
- execute_bound.py固定只调用run_oos.py evaluate、subprocess.run timeout=300，TimeoutExpired/非零退出留失败记录并停止，无自动重试；正式入口必须是该controller。工具yield等待不能替代此硬限额。

## 限制与非阻断项

- 本审查静态验证数据流，不新增独立科学数组复核。缺值/异常数据的实际QA须由正式释放后一次执行返回PASS或失败。
- 跨用户/代理历史暴露未知，新锁定的历史时间外推不构成全球未暴露确认；仓库变体不是原论文已核实实现。
- source bar完成/UTC标签是继承供应商契约，未校验真实历史可获得时刻或修订；不声称实盘交易时点模拟。
- 子段边界与32MiB/300秒在代码固定，当前与协议一致；今后不能只改JSON继续使用本review。assert类拒绝须保持python未用-O，正式入口指定-B（不启优化）。
- runner直接evaluate不自带timeout，正式入口controller解决。本review/协议字节改变会使controller拒绝。硬超时后的日志写入是少量调度记录，不声明整调度含日志绝不超300秒。
- 外部数据范围继承限定本地非商业用途，内部项目授权不等于上游全部权利或公开原始数据许可。
