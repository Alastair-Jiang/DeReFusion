# -*- coding: utf-8 -*-
"""
容量敏感性检查：把非线性算子的隐层从 23（参数量匹配）加宽到 64 / 128，
在同一套**预先固定的**结构状态上重算 ΔMSE。
目的：判断主实验"线性占优"的结论是否只是隐层瓶颈造成的假象。
不修改分组规则、不挑选种子、不挑选状态。

输出：05_research_intelligence/operator-regime-capacity.csv
"""
import io
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import structure_routing_experiment as S  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
OUTDIR = os.path.join(S.PROJ, "05_research_intelligence")
WIDTHS = [23, 64, 128]


def run_width(width):
    class MLPw(S.MLPOp):
        def __init__(self, d_in, d_out, hidden=width):
            super().__init__(d_in, d_out, hidden=hidden)

    S.MLPOp = MLPw
    rows = []
    for tag in S.ASSETS:
        df, raw, close, num_train, border1_test = S.load_asset(tag)
        n_rows = len(df)
        n_test = n_rows - border1_test - S.SEQ_LEN - S.PRED_LEN + 1
        n_train_s = num_train - S.SEQ_LEN - S.PRED_LEN + 1
        border1_val = num_train - S.SEQ_LEN
        n_val = (n_rows - int(n_rows * S.TEST_R)) - border1_val - S.SEQ_LEN - S.PRED_LEN + 1

        scaled, mu, sd = S.standardize(raw, num_train)
        x_tr, y_tr = S.make_windows(scaled, 0, n_train_s)
        x_va, y_va = S.make_windows(scaled, border1_val, n_val)
        x_te, y_te = S.make_windows(scaled, border1_test, n_test)
        tr_f, te_f = S.all_features(close, border1_test, n_test, n_train_s)
        states, _ = S.build_regimes(tr_f, te_f)

        for seed in S.SEEDS:
            model_l, p_l, _ = S.train_operator("linear", x_tr, y_tr, x_va, y_va, seed)
            model_n, p_n, _ = S.train_operator("mlp", x_tr, y_tr, x_va, y_va, seed)
            with torch.no_grad():
                pl = model_l(torch.tensor(x_te)).numpy()
                pn = model_n(torch.tensor(x_te)).numpy()
            se_l = ((pl - y_te) ** 2).mean(1)
            se_n = ((pn - y_te) ** 2).mean(1)
            for sname, mask in states.items():
                if mask.sum() < 20:
                    continue
                d = se_n[mask] - se_l[mask]
                lo, hi = S.bootstrap_ci(d, seed=seed)
                rows.append({
                    "width": width, "asset": tag, "seed": seed, "state": sname, "n": int(mask.sum()),
                    "params_N": p_n, "MSE_L": float(se_l[mask].mean()), "MSE_N": float(se_n[mask].mean()),
                    "dMSE": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
                    "sig": "sig" if (lo > 0 or hi < 0) else "ns",
                    "winN": float((se_n[mask] < se_l[mask]).mean()),
                })
            print(f"[w={width} {tag} s{seed}] params_N={p_n} done")
    return rows


def main():
    all_rows = []
    for w in WIDTHS:
        all_rows += run_width(w)
    df = pd.DataFrame(all_rows)
    os.makedirs(OUTDIR, exist_ok=True)
    df.to_csv(os.path.join(OUTDIR, "operator-regime-capacity.csv"), index=False)

    agg = df.groupby(["width", "asset"]).agg(
        dMSE_mean=("dMSE", "mean"), dMSE_min=("dMSE", "min"), dMSE_max=("dMSE", "max"),
        sig_frac=("sig", lambda s: float((s == "sig").mean())),
        winN=("winN", "mean"), params_N=("params_N", "max")).reset_index()
    print("\n=== 容量敏感性：非线性算子胜出（dMSE<0）的状态数占比 ===")
    for w in WIDTHS:
        sub = df[df.width == w]
        frac = float((sub["dMSE"] < 0).mean())
        print(f"隐层={w:3d} 参数={sub['params_N'].max():>7d} | 偏好非线性的状态比例={frac:.1%} | "
              f"平均 dMSE={sub['dMSE'].mean():+.5f}")
    agg.to_csv(os.path.join(OUTDIR, "operator-regime-capacity-summary.csv"), index=False)
    print("[saved] operator-regime-capacity.csv / -summary.csv")


if __name__ == "__main__":
    main()
