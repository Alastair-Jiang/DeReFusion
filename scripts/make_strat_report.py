# -*- coding: utf-8 -*-
"""
生成 BTCUSD 相对波动率 replication 报告（6 节 + A/B/C 判定），并与 GSPC 逐项比较。
用法：python scripts/make_strat_report.py
依赖：volatility_stratification_{tag}_{mode}.json（由 analyze_volatility_regimes.py 生成）
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "..", "..", "05_research_intelligence")

TARGETS = [("GSPC", "relative"), ("BTCUSD", "relative"), ("BTCUSD", "absolute"), ("GSPC", "absolute")]


def load(tag, mode):
    p = os.path.join(REPO, f"volatility_stratification_{tag}_{mode}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verdict(btc):
    if btc is None:
        return "C", "BTCUSD 结果尚未生成"
    st = btc["horizons"]["T24"]["structure"]
    comp = btc["horizons"]["T24"]["comparison"]
    hi, lo = comp["Q4+Q5 (high)"], comp["Q1+Q2 (low)"]
    inter = comp["interaction_Q45_minus_Q12"]

    hi_adv = hi["significant"] and hi["delta_mse"] < 0
    lo_tie = not lo["significant"]
    if hi_adv and lo_tie and not st["pattern2_stable_linear_regime"]:
        return "A", ("高相对波动区间非线性优势显著、低区间打平、无稳定线性 regime、"
                     f"interaction={inter['value']:+.5f} CI[{inter['ci95'][0]:+.5f},{inter['ci95'][1]:+.5f}]")
    if hi_adv and lo["significant"] and lo["delta_mse"] < 0:
        return "A", "低波动区间也已显著偏向非线性（趋势比 GSPC 更强）"
    if (not hi["significant"]) or hi["delta_mse"] > 0:
        return "B", (f"高波动组未出现显著非线性优势（Δ={hi['delta_mse']:+.5f}, "
                     f"significant={hi['significant']}）")
    return "C", "方向一致但证据强度不足（CI 较宽或显著性边缘）"


def fmt_ci(ci):
    return f"[{ci[0]:+.5f}, {ci[1]:+.5f}]"


def main():
    R = {k: load(*k) for k in TARGETS}
    btc_rel, btc_abs = R[("BTCUSD", "relative")], R[("BTCUSD", "absolute")]
    gspc_rel = R[("GSPC", "relative")]

    v, why = verdict(btc_rel)
    L = []
    a = L.append

    a("# BTCUSD T=24 相对波动率 Replication 报告")
    a("")
    a("> 目的：检验\"非线性信息的边际贡献是否随 relative volatility 提高而增加\"在 BTCUSD 上是否复现 GSPC 的结构。")
    a("> 约束：未修改模型、未实现 NS operator、未新增训练（复用了既有 6 组实验的 pred/true）。")
    a("")

    a("## 1. 实验配置")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a("| 数据 | BTCUSD-2016-2025.csv（3,653 行，日线 OHLC，Yahoo） |")
    a("| 协议 | seq_len=96, label_len=48, pred_len=24, features=MS, target=Close |")
    a("| 模型 | DeReFusion（加法融合，非线性残差） vs revin-DLinear（线性基座） |")
    a("| 训练 | d_model=32, moving_avg=25, epochs=30, batch=32, lr=1e-4, patience=5, cosine, seed=2021, CPU |")
    a("| 波动率口径 | **RV_rel(t) = RV(t) / median(RV(t-120:t-1))**（严格因果，无未来信息）；absolute 口径仅作对照 |")
    a("| 指标口径 | 标准化尺度（与论文/utils.metrics 一致） |")
    if btc_rel:
        h = btc_rel["horizons"]["T24"]
        a(f"| 测试样本 | {h['n_samples']}（对齐校验 max|scaled−true|={h['align_maxdiff']:.2e}） |")
    a("")

    for tag, mode, title in [("BTCUSD", "relative", "2. 分层结果 — BTCUSD（relative volatility，主判定口径）"),
                             ("BTCUSD", "absolute", "2b. 备用口径 — BTCUSD（absolute volatility）")]:
        R_ = R[(tag, mode)]
        if R_ is None:
            a(f"## {title}\n\n（结果尚未生成）\n")
            continue
        h = R_["horizons"]["T24"]
        a(f"## {title}")
        a("")
        a("| 五分位 | n | RV_rel 范围 | DeReFusion MSE | DLinear MSE | rel. improvement | ΔMSE 95%CI | 配对胜率 | DeReFusion MSPE | DLinear MSPE |")
        a("|---|---|---|---|---|---|---|---|---|---|")
        for c in h["quintile_curve"]:
            sig = "显著" if (c["ci95"][0] > 0 or c["ci95"][1] < 0) else "n.s."
            a(f"| Q{c['q']} | {c['n']} | {c['rv_lo']:.3f}–{c['rv_hi']:.3f} | {c['mse_deref']:.5f} | "
              f"{c['mse_dlin']:.5f} | {c['rel']:+.1f}% | {fmt_ci(c['ci95'])} {sig} | {c['win_rate']:.1%} | "
              f"{c['mspe_deref']:.5f} | {c['mspe_dlin']:.5f} |")
        a("")
        a("**分组（任务书口径）**")
        a("")
        a("| 分组 | n | DeReFusion MSE | DLinear MSE | ΔMSE | 95%CI | 显著 | 胜率 |")
        a("|---|---|---|---|---|---|---|---|")
        for name in ("Q1+Q2 (low)", "Q4+Q5 (high)"):
            c = h["comparison"][name]
            s = h["strata"].get(name, {})
            a(f"| {name} | {c['n']} | {s.get('DeReFusion', {}).get('MSE', float('nan')):.5f} | "
              f"{s.get('revin-DLinear', {}).get('MSE', float('nan')):.5f} | {c['delta_mse']:+.5f} | "
              f"{fmt_ci(c['ci95'])} | {'是' if c['significant'] else '否'} | {c['win_rate']:.1%} |")
        a("")

    a("## 3. Interaction Effect")
    a("")
    a("| 资产 | 口径 | Δ(Q4+Q5 − Q1+Q2) | 95%CI | 显著 |")
    a("|---|---|---|---|---|")
    for tag, mode in [("BTCUSD", "relative"), ("BTCUSD", "absolute"), ("GSPC", "relative"), ("GSPC", "absolute")]:
        R_ = R[(tag, mode)]
        if R_ is None:
            continue
        c = R_["horizons"]["T24"]["comparison"]["interaction_Q45_minus_Q12"]
        a(f"| {tag} | {mode} | {c['value']:+.5f} | {fmt_ci(c['ci95'])} | {'是' if c['significant'] else '否'} |")
    a("")
    a("> 负值且 CI 不含 0 = 非线性分支的相对优势在高波动区间显著更大（regime dependence）。")
    a("")

    a("## 4. 与 GSPC 逐项比较")
    a("")
    a("| 检验项 | GSPC | BTCUSD | 是否同构 |")
    a("|---|---|---|---|")
    checks = [
        ("低波动区间接近（无显著差异）", "Q1+Q2 (low)", lambda c: not c["significant"]),
        ("高波动区间非线性优势", "Q4+Q5 (high)", lambda c: c["significant"] and c["delta_mse"] < 0),
        ("interaction 支持 regime dependence", "interaction_Q45_minus_Q12", lambda c: c["significant"] and c["value"] < 0),
    ]
    for label, key, fn in checks:
        gc = gspc_rel["horizons"]["T24"]["comparison"][key] if gspc_rel else None
        bc = btc_rel["horizons"]["T24"]["comparison"][key] if btc_rel else None
        g_ok = "✓" if (gc and fn(gc)) else ("✗" if gc else "—")
        b_ok = "✓" if (bc and fn(bc)) else ("✗" if bc else "—")
        same = "是" if (gc and bc and fn(gc) == fn(bc)) else ("待定" if not bc else "否")
        a(f"| {label} | {g_ok} | {b_ok} | {same} |")
    if btc_rel:
        bst = btc_rel["horizons"]["T24"]["structure"]
        a("")
        a(f"- BTC 五分位 improvement 序列: {', '.join(f'Q{i+1}:{v:+.1f}%' for i, v in enumerate(bst['quintile_improvement']))}")
        a(f"- Pattern 1（高波动优势扩大且低波动接近）: {'支持' if bst['pattern1_supported'] else '不支持'}")
        a(f"- Pattern 2（存在稳定 linear advantage regime）: {'存在，位于 Q' + ','.join(map(str, bst['sig_linear_quintiles'])) if bst['pattern2_stable_linear_regime'] else '不存在'}")
    a("")

    a("## 5. 是否支持继续做 NS-inspired operator prototype")
    a("")
    a(f"**判定：{v}** — {why}")
    a("")
    a({"A": "→ 可进入下一阶段：NS-inspired nonlinear operator 原型。**但不声称 NS 已有效**，其有效性须通过与同容量 MLP 的受控对比来验证。",
       "B": "→ 不支持直接进入 NS prototype。应先把\"波动率 regime\"假设降级为 asset-specific 现象，检查 BTC 与股指的机制差异（24h 交易、微观结构、波动率长记忆），或转用其他 regime 划分（如趋势/震荡）。",
       "C": "→ 证据不足，结论暂定。需扩资产（ETHUSD/EURUSD 等）或多种子复现后再判定。"}[v])
    a("")

    a("## 6. 下一步实验建议")
    a("")
    a("1. **若判定 A**：实现 NS-inspired operator（1D advection–diffusion/Burgers 类比，避免直接标 Navier–Stokes），作为 CP1 新模型接入；**判据**：在 T=24 高相对波动分位（Q4+Q5）上显著优于同参数量 MLP/TCN。")
    a("2. **多种子复核**：当前为单种子（2021）。对 T=24 补 seed∈{2020,2022} 的 3 资产 × 2 模型，以区分\"机制\"与\"单次采样波动\"。")
    a("3. **扩资产**：至少补 1 个加密资产（ETHUSD，同 24h 机制）与 1 个外汇（EURUSD），检验 regime dependence 的普适性。")
    a("4. **regime 定义对照**：以 absolute / relative / 趋势-震荡 三种划分互相验证，排除时间混淆（已发现 GSPC corr=+0.44、BTC corr=−0.67）。")
    a("5. **不推进**：adaptive gating 主线（Pattern 2 在 GSPC 上不存在，且论文 gatev1-v3 与本地 gatev2 均为负结果）。")
    a("")

    txt = "\n".join(L)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "btc-volatility-stratification.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt)
    print(f"\n[saved] {path}")
    print(f"[verdict] {v}")


if __name__ == "__main__":
    main()
