#!/usr/bin/env python3
"""Every number quoted in the paper, computed from an lc.py dataset.

    python3 stats.py qarray_1e9.json

Also writes quads_1e9.csv (one row per quad member) and appendix_rows.tex
(LaTeX rows for the appendix table) next to the dataset.

Minimal term counts K are computed by iterative deepening with
lc.Deriver._fixed for three vocabularies:
    pure : distinct members of earlier quads only
    add  : members plus at most one royal value reachable by addition
           of distinct royal members (2, 3, 5, 7, 8, 9, 10, 12, 14, 15, 17)
    flat : members plus at most one royal value with a flat +/* expression
           (no product containing a sum), the vocabulary lc.py prefers
A royal value counts as one term.  K is evaluated when the difference is
first met in the chain, using only the quads available at that moment.
"""
import bisect
import csv
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lc  # noqa: E402

ROYAL = set(lc.ROYAL)
PURE = {0}
ROYAL_ADD = {v for (d, m, t), vs in lc.ROYAL_SETS.items() if d == 0 for v in vs}
ROYAL_FLAT = {v for (d, m, t), vs in lc.ROYAL_SETS.items() if d <= 1 for v in vs}
KMAX = 12
VOCAB = (("pure", None), ("add", ROYAL_ADD), ("flat", ROYAL_FLAT))


def min_terms(deriver, diff, cand, prefix, quad_of, base_quad, extra):
    for K in range(1, KMAX + 1):
        if deriver._fixed(diff, K, PURE, cand, prefix, quad_of, base_quad) is not None:
            return K
        if extra and deriver._fixed(diff, K - 1, extra, cand, prefix,
                                    quad_of, base_quad) is not None:
            return K
    return None


def a_terms(entry):
    n = len(entry["terms"])
    if entry.get("royal"):
        n += lc.top_terms(entry["royal"])
    return n


def royal_kind(text):
    if not text:
        return "none"
    return "product" if "*" in text else "addition"


def main(path):
    folder = os.path.dirname(os.path.abspath(path))
    data = json.load(open(path))
    quads, diffs = data["quads"], data["diffs"]
    deriver = lc.Deriver()
    print(f"dataset: {os.path.basename(path)}")
    print(f"quads after the royal quad: {len(quads):,}")
    print(f"largest first prime: {quads[-1]['primes'][0]:,}")
    print(f"unique differences: {len(diffs):,}")

    # ---- mod 30 facts ---------------------------------------------------
    assert all(q["primes"][0] % 30 == 11 for q in quads)
    res = Counter()
    for q in quads[1:]:
        for i, der in enumerate(q["derivations"]):
            res[(i, der["diff"] % 30)] += 1
    print("difference residues mod 30 (member index, residue) -> count:",
          dict(sorted(res.items())))
    gaps = [quads[i + 1]["primes"][0] - quads[i]["primes"][0] for i in range(len(quads) - 1)]
    print(f"gaps between consecutive quads: min {min(gaps)}, max {max(gaps):,}, "
          f"mean {statistics.mean(gaps):,.0f}; all multiples of 30: "
          f"{all(g % 30 == 0 for g in gaps)}")

    # ---- additive way: terms and royal part -----------------------------
    for scope, pick in (("first prime per quad", lambda q: q["derivations"][:1]),
                        ("all four members", lambda q: q["derivations"])):
        terms = Counter()
        kinds = Counter()
        reused = 0
        total = 0
        for q in quads[1:]:
            for der in pick(q):
                e = diffs[str(der["diff"])]
                total += 1
                terms[a_terms(e)] += 1
                kinds[royal_kind(e.get("royal"))] += 1
                reused += der["reused"]
        print(f"\nadditive way, {scope}: {total:,} equations, {reused:,} reuse an earlier difference")
        print("  terms per equation:", dict(sorted(terms.items())))
        print("  royal part:", dict(kinds))
        print(f"  max terms: {max(terms)}")

    # ---- minimal K per unique difference ---------------------------------
    avail, quad_of = [], {}
    K = {name: {} for name, _ in VOCAB}
    first_of = {}
    member_of = {}
    for q in quads:
        if q["n"] > 1:
            for i, der in enumerate(q["derivations"]):
                if der["reused"] or der.get("failed"):
                    continue
                diff, base = der["diff"], der["base"]
                cand = [p for p in avail[:bisect.bisect_right(avail, diff)] if p != base]
                prefix = [0]
                for p in cand:
                    prefix.append(prefix[-1] + p)
                for name, extra in VOCAB:
                    K[name][diff] = min_terms(deriver, diff, cand, prefix,
                                              quad_of, quad_of[base], extra)
                first_of[diff] = (q["n"], der["target"])
                member_of[diff] = i
        for p in q["primes"]:
            avail.append(p)
            quad_of[p] = q["n"]
    for name, _ in VOCAB:
        dist = Counter(K[name].values())
        exc = sorted(d for d, k in K[name].items() if k is None)
        vals = [k for k in K[name].values() if k is not None]
        print(f"\nminimal K, vocabulary '{name}': distribution "
              f"{dict(sorted((k, v) for k, v in dist.items() if k is not None))}")
        print(f"  max K {max(vals)}, mean K {statistics.mean(vals):.2f}, "
              f"no representation within {KMAX} terms: {len(exc)}")
        if exc:
            print("  exceptions (difference: first seen at quad, target):",
                  {d: first_of[d] for d in exc})
    # first-prime view of pure K per block of quads
    fp = [(q["n"], K["pure"].get(q["derivations"][0]["diff"])) for q in quads[1:]]
    block = max(1, len(fp) // 8)
    print("\npure K of the first prime per block of quads "
          "(block, mean K, share K=2, share K<=3):")
    for s in range(0, len(fp), block):
        chunk = [k for _, k in fp[s:s + block] if k is not None]
        if chunk:
            print(f"  quads {fp[s][0]:>6}-{fp[min(s + block, len(fp)) - 1][0]:>6}: "
                  f"{statistics.mean(chunk):.2f}  "
                  f"{sum(k == 2 for k in chunk) / len(chunk):.2f}  "
                  f"{sum(k <= 3 for k in chunk) / len(chunk):.2f}")

    # ---- M and E ways ------------------------------------------------------
    for way, label in (("mul", "M"), ("exp", "E1"), ("expv", "E2")):
        kinds = Counter()
        rr = 0
        fb = 0
        nterms = Counter()
        for q in quads[1:]:
            for der in q["derivations"][:1]:
                e = diffs[str(der["diff"])][way]
                fb += e.get("fallback", False)
                nterms[len(e["terms"])] += 1
                for t in e["terms"]:
                    kinds[t[0]] += 1
                    if t[0] == "*" and t[1] in ROYAL and t[2] in ROYAL:
                        rr += 1
        print(f"\n{label} way, first prime per quad: term kinds {dict(kinds)}, "
              f"royal x royal products {rr}, fallbacks {fb}")
        print("  terms per equation:", dict(sorted(nterms.items())))
    same = sum(diffs[str(q["derivations"][0]["diff"])]["exp"]["terms"]
               == diffs[str(q["derivations"][0]["diff"])]["expv"]["terms"]
               for q in quads[1:])
    print(f"E1 and E2 identical for {same:,} of {len(quads) - 1:,} first primes")

    # ---- coverage: every integer below the next quad ------------------------
    signed = set(lc.ROYAL_SIGNED)

    def contiguous(S):
        t = 0
        while t + 1 in S:
            t += 1
        return t

    print(f"\nsigned royal values 0..210 with + - *: {len(signed)} values, "
          f"contiguous 0..{contiguous(signed)}, first holes "
          f"{sorted(set(range(101)) - signed)[:6]}")
    cap = 5000
    cur = set(signed)
    T = [contiguous(cur)]
    for q in quads[:4]:
        for p in q["primes"]:
            cur |= {x + p for x in cur if x + p <= cap}
        T.append(contiguous(cur))
    print("coverage T_k after adding Q_0..Q_k (quad members added, one royal "
          f"value): {T}  (T_4 capped at {cap})")
    # S_k = T_3 + sum_{j=4..k} (4 p_j + 16); condition p_j <= S_{j-1} + 1
    S = T[3]
    worst = None
    ratio = max((quads[i]["primes"][0] / quads[i - 1]["primes"][0], quads[i]["n"])
                for i in range(2, len(quads)))
    for q in quads[3:]:                       # j = 4, 5, ...
        p = q["primes"][0]
        slack = S + 1 - p
        if worst is None or slack < worst[0]:
            worst = (slack, q["n"], p, S)
        S += 4 * p + 16
    print(f"growth condition p_j <= S_(j-1) + 1 holds for all j <= {len(quads)}: "
          f"{worst[0] >= 0}; tightest at quad {worst[1]} (p = {worst[2]:,}, "
          f"S = {worst[3]:,}); max p_j / p_(j-1) for j >= 3: {ratio[0]:.2f} "
          f"at quad {ratio[1]}")

    # ---- appendix rows and CSV --------------------------------------------
    rows_tex = []
    csv_rows = []
    for q in quads:
        for i, der in enumerate(q["derivations"]):
            if q["n"] == 1:
                eq = der["royal"]
                m, e1, e2 = (lc.ops_text(der[w]["terms"]) for w in ("mul", "exp", "expv"))
                base = diff = ""
                nt = lc.top_terms(eq)
                kp = ka = kf = ""
                src = ""
            else:
                e = diffs[str(der["diff"])]
                eq = f"{der['base']} + {lc.diff_text(e)}"
                m, e1, e2 = (f"{der['base']} + {lc.ops_text(e[w]['terms'])}"
                             for w in ("mul", "exp", "expv"))
                base, diff = der["base"], der["diff"]
                nt = a_terms(e) + 1
                kp, ka, kf = (K[n].get(der["diff"]) for n, _ in VOCAB)
                kp = "--" if kp is None else kp
                src = e["first"][0] if der["reused"] else ""
            csv_rows.append([q["n"], q["primes"][0], der["target"], base, diff,
                             eq, m, e1, e2, kp, ka, kf])
            if q["n"] <= 25:
                rows_tex.append(
                    f"{q['n']} & {der['target']} & {base} & {diff} & "
                    f"\\texttt{{{eq.replace('*', '*')}}} & {nt} & {kp} & {src} \\\\")
    with open(os.path.join(folder, "appendix_rows.tex"), "w") as fh:
        fh.write("\n".join(rows_tex) + "\n")
    with open(os.path.join(folder, "quads_1e9.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["k", "p", "member", "base", "difference", "additive",
                    "multiplicative", "exponential_E1", "exponential_E2",
                    "K_pure", "K_royal_addition", "K_royal_flat"])
        w.writerows(csv_rows)
    print(f"\nwrote appendix_rows.tex ({len(rows_tex)} rows) and quads_1e9.csv "
          f"({len(csv_rows)} rows)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qarray_1e9.json")
