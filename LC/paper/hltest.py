#!/usr/bin/env python3
"""A numerical test of the Hardy--Littlewood prediction for two-term forms.

    python3 paper/hltest.py                       # admissible n below 10^7, gaps of the 10^9 chain
    python3 paper/hltest.py --upto 10000000 --gaps 10Billion/qarray_1e10.json

For an even integer n write r(n) for the number of first members p < n of
prime quadruplets such that n - p is also a first member (Section 8 of the
paper; p and n - p are counted in both orders).  For fixed n this asks when
the eight linear forms

    p, p+2, p+6, p+8,   n-p, n-p+2, n-p+6, n-p+8

are simultaneously prime.  The generalised Hardy--Littlewood conjecture
(Conjecture 1.2 of Green and Tao, "Linear equations in primes") predicts

    r(n)  ~  S(n) * I(n),
    S(n)  =  prod over primes l of (1 - nu_n(l)/l) / (1 - 1/l)^8,
    I(n)  =  integral from 11 to n-11 of dt / ((log t)^4 (log(n-t))^4),

where nu_n(l) is the number of residues p mod l at which one of the eight
forms vanishes.  The system contains the pattern (0, 2, 6, 8) and therefore
has infinite complexity in the sense of Green and Tao, so the prediction is
not covered by their theorem; this script checks it against the chain.

For l >= 11 at most eight residues are excluded, and exactly eight unless
l divides n + a + b for some offsets a, b in {0, 2, 6, 8}; so

    S(n) = L(n mod 210) * G * prod_{l >= 11, l | n+a+b} (l - nu_n(l)) / (l - 8),

with L the exact factor at 2, 3, 5, 7 and G the convergent generic product
over l >= 11 of (1 - 8/l) / (1 - 1/l)^8.  No library beyond the standard
one is needed.

Output: the sum of r(n) over the admissible n (n = 22, 82, 112, 172, 202
mod 210) of each decade against the sum of the prediction, the share of
admissible n with no two-term form against the Poisson value exp(-R/2),
and the same comparison for the gaps of the chain, where a two-term form
with distinct summands is what the paper's K_pure = 2 means.
"""
import argparse
import bisect
import json
import math
import os
import sys
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
OFFSETS = (0, 2, 6, 8)
SUMS = sorted({a + b for a in OFFSETS for b in OFFSETS})      # 0..16 even
ADMISSIBLE = (22, 82, 112, 172, 202)                           # mod 210


def spf_table(limit):
    """Smallest prime factor of every integer up to limit (0 = prime or < 2)."""
    spf = array("i", bytes(4 * (limit + 1)))
    root = int(limit ** 0.5) + 1
    small = [p for p in range(2, root + 1) if all(p % q for q in range(2, int(p ** 0.5) + 1))]
    for p in reversed(small):                 # smallest prime written last
        n = (limit - p * p) // p + 1
        if n > 0:
            spf[p * p::p] = array("i", [p]) * n
    return spf


def primes_from(spf, lo, hi):
    return [x for x in range(lo, hi + 1) if spf[x] == 0]


def nu(n, l):
    """Residues p mod l at which one of the eight forms vanishes."""
    return len({(-a) % l for a in OFFSETS} | {(n + b) % l for b in OFFSETS})


def local_factor(n):
    f = 1.0
    for l in (2, 3, 5, 7):
        f *= (1 - nu(n, l) / l) / (1 - 1 / l) ** 8
    return f


def prime_divisors(m, spf):
    out = set()
    while m > 1:
        p = spf[m] or m
        out.add(p)
        while m % p == 0:
            m //= p
    return out


def singular(n, spf, local, generic):
    """S(n) for even n."""
    f = local[n % 210] * generic
    if f == 0.0:
        return 0.0
    seen = set()
    for s in SUMS:
        for l in prime_divisors(n + s, spf):
            if l >= 11 and l not in seen:
                seen.add(l)
                f *= (l - nu(n, l)) / (l - 8)
    return f


def integral(n, steps=2000):
    """I(n) = int_11^{n-11} dt / ((log t)^4 (log(n-t))^4), Simpson in u = log t
    over [11, n/2], doubled by symmetry."""
    if n < 24:
        return 0.0
    a, b = math.log(11), math.log(n / 2)
    h = (b - a) / steps
    total = 0.0
    for i in range(steps + 1):
        u = a + i * h
        t = math.exp(u)
        w = 1 if i in (0, steps) else (4 if i % 2 else 2)
        total += w * t / (u ** 4 * math.log(n - t) ** 4)
    return 2 * total * h / 3


class Interp:
    """log I(n) interpolated linearly in log n on a geometric grid."""

    def __init__(self, lo, hi, points=600):
        self.xs = [math.log(lo) + i * (math.log(hi) - math.log(lo)) / points for i in range(points + 1)]
        self.ys = [math.log(integral(math.exp(x))) for x in self.xs]

    def __call__(self, n):
        x = math.log(n)
        i = min(max(bisect.bisect_right(self.xs, x) - 1, 0), len(self.xs) - 2)
        x0, x1 = self.xs[i], self.xs[i + 1]
        y = self.ys[i] + (self.ys[i + 1] - self.ys[i]) * (x - x0) / (x1 - x0)
        return math.exp(y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", default=os.path.join(HERE, "qarray_1e9.json"),
                    help="chain cache that supplies the first members (default paper/qarray_1e9.json)")
    ap.add_argument("--upto", type=int, default=10 ** 7, help="largest n tested (default 10^7)")
    ap.add_argument("--gaps", action="append", default=[],
                    help="further caches whose gaps are tested (may repeat)")
    ap.add_argument("--out", default=None, help="write the report here as well")
    args = ap.parse_args()
    N = args.upto

    with open(args.cache) as fh:
        data = json.load(fh)
    firsts = [q["primes"][0] for q in data["quads"]]
    if firsts[-1] < N:
        sys.exit(f"the cache stops at {firsts[-1]}, below --upto {N}")
    members = firsts[:bisect.bisect_left(firsts, N)]
    lines = []

    def say(s=""):
        lines.append(s)
        print(s, flush=True)

    say(f"Two-term forms by first members: Hardy--Littlewood prediction against the chain, n <= {N:,}")
    say(f"first members below {N:,}: {len(members):,}")

    # observed r(n), both orders
    r = array("i", bytes(4 * (N + 1)))
    for i, p in enumerate(members):
        for q in members[i:]:
            n = p + q
            if n > N:
                break
            r[n] += 1 if p == q else 2

    say("building the smallest-prime-factor table ...")
    spf = spf_table(N + 20)
    local = [local_factor(c) if c % 2 == 0 else 0.0 for c in range(210)]
    generic = math.exp(sum(math.log((1 - 8 / l) / (1 - 1 / l) ** 8) for l in primes_from(spf, 11, N + 20)))
    tail = -28 / ((N + 20) * math.log(N + 20))           # sum_{l > L} log(1 - 28/l^2 ...) ~ -28/(L log L)
    say(f"generic product over 11 <= l <= {N + 20:,}: {generic:.6f} (tail beyond it ~ {tail:+.1e} in the log)")
    say(f"local factors at 2,3,5,7 on the admissible classes: "
        + ", ".join(f"{c}: {local[c]:.4f}" for c in ADMISSIBLE))
    interp = Interp(1000, N)

    # the constant C4 of a single quadruplet, from the same local and generic factors
    c4 = 1.0
    for l in (2, 3, 5, 7):
        c4 *= (1 - len({(-a) % l for a in OFFSETS}) / l) / (1 - 1 / l) ** 4
    c4 *= math.exp(sum(math.log((1 - 4 / l) / (1 - 1 / l) ** 4) for l in primes_from(spf, 11, N + 20)))
    say(f"C4 from the same factors: {c4:.4f}")
    say("first members below x against C4 * int_11^x dt/(log t)^4:")
    for x in (10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7):
        if x <= N:
            cnt = bisect.bisect_left(members, x)
            a, b, steps = math.log(11), math.log(x), 4000
            h = (b - a) / steps
            li4 = sum((1 if i in (0, steps) else (4 if i % 2 else 2)) * math.exp(a + i * h) / (a + i * h) ** 4
                      for i in range(steps + 1)) * h / 3
            say(f"   x = {x:>12,}: {cnt:>5,} observed, {c4 * li4:8.1f} predicted, ratio {cnt / (c4 * li4):.3f}")
    log4 = [math.log(p) ** 4 for p in members]

    # every admissible n up to N
    pred, semi = {}, {}
    for c in ADMISSIBLE:
        for n in range(c, N + 1, 210):
            if n >= 1000:
                S = singular(n, spf, local, generic)
                pred[n] = S * interp(n)
                # the same singular series, but the density C4 dt/(log t)^4 of one factor
                # replaced by the first members themselves: (S/C4) * sum_p 1/(log(n-p))^4
                hi = bisect.bisect_left(members, n - 10)
                semi[n] = S / c4 * sum(1 / math.log(n - p) ** 4 for p in members[:hi])

    say()
    say("decade        admissible n   sum r(n) observed   sum predicted   ratio   semi-empirical   ratio   share r=0 observed   Poisson exp(-R/2)")
    rows = []
    lo = 1000
    while lo < N:
        hi = min(lo * 10, N)
        ns = [n for n in pred if lo <= n < hi] if hi < N else [n for n in pred if lo <= n <= hi]
        obs = sum(r[n] for n in ns)
        exp_ = sum(pred[n] for n in ns)
        sem = sum(semi[n] for n in ns)
        zero_obs = sum(1 for n in ns if r[n] == 0) / len(ns)
        zero_pred = sum(math.exp(-pred[n] / 2) for n in ns) / len(ns)
        rows.append((lo, hi, len(ns), obs, exp_, sem, zero_obs, zero_pred))
        say(f"[{lo:>9,}, {hi:>10,})  {len(ns):>8,}   {obs:>12,}   {exp_:>14,.1f}   {obs / exp_:5.3f}   {sem:>14,.1f}   {obs / sem:5.3f}   {zero_obs:8.4f}             {zero_pred:8.4f}")
        lo = hi
    say()
    say("LaTeX rows:")
    for lo, hi, cnt, obs, exp_, sem, z0, zp in rows:
        say(f"$[10^{{{round(math.log10(lo))}}},10^{{{round(math.log10(hi))}}})$ & {cnt:,} & {obs:,} & {exp_:,.0f} & {obs / exp_:.2f} & {sem:,.0f} & {obs / sem:.2f} & {z0:.3f} & {zp:.3f} \\\\")

    # the gaps of each chain
    for path in [args.cache] + args.gaps:
        with open(path) as fh:
            quads = json.load(fh)["quads"]
        f = [q["primes"][0] for q in quads]
        gaps = [f[i] - (f[i - 1] + 8) for i in range(1, len(f))]
        if max(gaps) > N:
            say(f"\n{os.path.basename(path)}: largest gap {max(gaps):,} exceeds --upto, skipped")
            continue
        fs = set(members)
        say()
        say(f"gaps of {os.path.basename(path)}: {len(gaps):,} gaps, {len(set(gaps)):,} distinct, largest {max(gaps):,}")
        two = 0
        expect = 0.0
        small = []
        for D in gaps:
            has = any((D - p) in fs and D - p != p for p in members if p < D)  # distinct first members
            two += has
            R = pred.get(D)
            if R is None:                      # below 1000: direct evaluation
                R = singular(D, spf, local, generic) * integral(D) if D >= 24 else 0.0
            expect += 1 - math.exp(-R / 2)
            if D < 1000:
                small.append((D, has, R))
        say(f"gaps with a two-term pure form (distinct first members): observed {two:,}, "
            f"predicted sum(1 - exp(-R/2)) = {expect:,.0f}, ratio {two / expect:.3f}")
        dist = sorted(set(gaps))
        two_d = sum(1 for D in dist if any((D - p) in fs and D - p != p for p in members if p < D))
        say(f"distinct gaps with a two-term pure form: {two_d:,} of {len(dist):,}")
        seen = set()
        say("gaps below 1000 (value, two-term form?, predicted R):")
        for D, has, R in sorted(small):
            if D not in seen:
                seen.add(D)
                say(f"   {D:>4}  {'yes' if has else 'no '}  R = {R:.4f}" + ("   <- royal gap" if D in (22, 82, 172, 382) else ""))
        royal = sum(1 for D in gaps if D in (22, 82, 172, 382))
        say(f"royal gaps among them: {royal:,}")

    # four-term pure forms by any members, for the small gaps
    M4 = 20000
    allm = sorted(p + o for p in members if p < M4 for o in OFFSETS)
    r4 = {}
    L = len(allm)
    for i in range(L):
        a = allm[i]
        for j in range(i + 1, L):
            ab = a + allm[j]
            if ab >= M4:
                break
            for k in range(j + 1, L):
                abc = ab + allm[k]
                if abc >= M4:
                    break
                for m in range(k + 1, L):
                    t = abc + allm[m]
                    if t > M4:
                        break
                    r4[t] = r4.get(t, 0) + 1
    say()
    say(f"four-term pure forms (any members, distinct) of the admissible integers below {M4:,}:")
    say("   admissible D with none: " + ", ".join(str(D) for D in range(22, M4, 2) if D % 210 in ADMISSIBLE and r4.get(D, 0) == 0))
    for lo, hi in ((1000, 2000), (2000, 5000), (5000, 10000), (10000, 20000)):
        vals = [r4.get(D, 0) for D in range(lo, hi, 2) if D % 210 in ADMISSIBLE]
        say(f"   [{lo:>6,}, {hi:>6,}): min {min(vals):>5}, median {sorted(vals)[len(vals) // 2]:>6}, max {max(vals):>7}")
    for D in (382, 412, 442, 622, 652, 1552, 1762, 2182, 5242, 11542):
        if D % 210 in ADMISSIBLE:
            say(f"   r4({D}) = {r4.get(D, 0)}")

    if args.out:
        with open(args.out, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"written {args.out}")


if __name__ == "__main__":
    main()
