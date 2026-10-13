# V2 diagnostic 工程独立只读审查

结论 PASS（有非阻断记录项）。本轮静态读取新协议、执行器、历史模型/预测/worker辅助代码以及已生成的合成/恢复摘要；未运行训练、评分或读取任何私有数组，未独立重跑合成测试，未改源码/旧协议。现有合成/恢复PASS是所读工件，不冒称本审查亲自完成。

## 通过项

- 代码/历史16项hash、实际HEAD和环境检查在准备与worker入口执行；新产物仅新目录/私有data子目录，xb和exists拒绝覆盖，旧目录仅read/load。
- 新输入只从ETH f100 train/validation固定路径取得；按源manifest两重hash绑定，经历史read_role检查role、shape、key、finite；prepare核验1730/365日期全集、全部相邻窗口/目标与训练-验证交界。没有test路径或CLI参数，属于T0程序纪律而非OS访问隔离。
- raw48为末48位置拷贝，mixed48为固定OHLC聚合；目标、最后Close和标尺相同。合成稿记录raw96=21743、raw48/mixed48=21599；对每个seed两48形状初始化hash相等。
- 9条轨迹连续1800步；前600循环与旧worker在模型、Adam、独立seed洗牌、batch32、drop_last=False、50步完整验证和严格小于更新上对应。seed17 raw96/mixed48在600处必须逐位复现旧beststate与旧MSE，否则停止。
- 600/1200/1800截面各保存该预算前缀最早严格最低和terminal；快照推理走eval/no_grad，load_state_dict恢复terminal后继续，训练循环下次显式train；不会从beststate继续训练。最早最低依严格<累计实现，不是从未来1800结果反向选600点。三个预算仍9条拟合非27独立实验。
- ridge目标与特征float64中心化、未惩罚截距，alpha>0解Gram+alphaI；alpha=0用np.linalg.lstsq(rcond=1e-12)最小范数/SVD阈值规则，十lambda一次流水生成wide和legacy；按网格顺序min保留最早tie，三表示各一次、共30解。
- run预先轮转三seed/三表示，全员1800固定预算，不按分数扩充；启动子进程前以剩余整批时间限制300s超时，失败留记录零自动重试；所有私有写入按当前总字节+payload检查128MiB。

## P2与报告限制

1. 1200/1800记录的neural_elapsed_seconds累积包含此前600/1200快照的额外验证推理、序列化和写盘；600计时在本截面保存前结束。应如实写“轨迹累计耗时（含先前快照开销）”，不能解释成同口径纯训练/常规验证耗时。
2. peak_working_set为Windows进程生涯高水位，包括读取输入、构建模型、旧快照等，不能声称每预算段独立内存或纯模型占用。
3. 硬timeout在run父进程执行；直接worker/ridge命令没有内置时间上限。正式执行使用run，不能将直接worker的限制写成已实现。run在最后子进程结束后到最终JSON写入没有额外整批截止检查；固定小量输出，属于边界记录缺项，非已知本批超限。
4. release读取review.result==PASS但未另机械比reviewed_code_sha256/protocol_sha256；当前审查精确hash记录且协议pin了执行器，准备完成后立即释放可绑定本次正确review。以后改版须重新审查，不能仅复用PASS。
5. svm/ridge含零正则高条件数候选；固定lstsq rcond控制解定义，未记录返回rank或奇异值谱。不是无限自由选择，但若零正则出现异常应保留诊断，不删除候选或临时改rcond求好分数。报告L_wide为新增验证调参敏感性，不替换旧L。
6. 执行器部分数值hardcoded与当前协议一致（1800/50/32/300/Adam/rcond），今后改协议不能只修改JSON。当前hash冻结成立，未来需成对更新并审查。
7. 未独立重验1800训练prefix的实际张量、数据来源数组或解的数值正确性；这些由运行后的独立审计适配关闭。合成PASS不证明科学优越、收敛或未暴露确认。
