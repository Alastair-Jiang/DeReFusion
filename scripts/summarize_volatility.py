# -*- coding: utf-8 -*-
"""基于 volatility_stratification.json 生成汇总报告（含相对改善幅度）。"""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = r"C:\Users\26843\Desktop\project\repos\DeReFusion"
with open(os.path.join(REPO, "volatility_stratification.json"), encoding="utf-8") as f:
    R = json.load(f)

lines = ["# DeReFusion 工况分层评估报告（GSPC, seed 2021）", ""]
lines.append("指标口径：pred/true 为标准化尺度（与论文一致）；波动率 = 输入窗口对数收益标准差（ex-ante，预测时可得）。")
lines.append("")

for T in ("T1", "T24"):
    if T not in R["strata"]:
        continue
    s = R["strata"][T]
    sp = R["splits"][T]
    lines.append(f"## {T.replace('T','T=')} （n={sp['n']}，RV 中位数 {sp['rv_median']:.5f}）")
    lines.append("")
    lines.append("| 分层 | n | DeReFusion MSE | DLinear MSE | 相对改善 | gatev2 MSE |")
    lines.append("|---|---|---|---|---|---|")
    for name in ("low20%", "low(<=median)", "high(>median)", "high20%"):
        if name not in s:
            continue
        row = s[name]
        d, b, g = row["DeReFusion"]["MSE"], row["revin-DLinear"]["MSE"], row["DeReFusion-gatev2-learnable"]["MSE"]
        rel = (b - d) / b * 100
        n = s["_comparison"].get(name, {}).get("n", "")
        lines.append(f"| {name} | {n} | {d:.5f} | {b:.5f} | {rel:+.1f}% | {g:.5f} |")
    c = s["_comparison"]
    lines.append("")
    lines.append("**逐样本配对检验（DeReFusion − DLinear，负值 = DeReFusion 更好）**")
    for name in ("low(<=median)", "high(>median)", "high20%"):
        if name in c:
            v = c[name]
            lines.append(f"- {name}: ΔMSE={v['delta_mse']:+.5f}, 95%CI[{v['ci95'][0]:+.5f},{v['ci95'][1]:+.5f}], "
                         f"胜率 {v['win_rate']:.1%}, n={v['n']}")
    it = c.get("interaction")
    if it:
        lines.append(f"- **交互效应 (高波动Δ − 低波动Δ) = {it['value']:+.5f}, 95%CI[{it['ci95'][0]:+.5f},{it['ci95'][1]:+.5f}]**")
    lines.append("")

out = "\n".join(lines)
print(out)
with open(r"C:\Users\26843\Desktop\project\05_research_intelligence\derefusion-volatility-stratification.md", "w", encoding="utf-8") as f:
    f.write(out + "\n")
print("\n[saved] 05_research_intelligence/derefusion-volatility-stratification.md")
