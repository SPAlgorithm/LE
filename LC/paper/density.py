"""Is Ladhe's Quad Conjecture a fact about primes, or about density?

Uses the paper's definition throughout: the base is m_k, the largest member of
the previous quadruplet, with no fallback to a smaller base.

Runs lc.py's own Deriver on the real prime-quadruplet chain and on control
chains that have the same spacing but are not prime.  Measures the paper's
Mode 1 claim: the gap is a sum of at most 8 distinct earlier members, with
exactly ten exceptional gaps (all <= 382) that need a royal expression.
"""
import bisect, json, random, sys, time
sys.path.insert(0, "/Users/pankajladhe/Pankaj/2018/AIStuff/RSAL/LC")
import lc

MAXK = 12


def pure_k(deriver, diff, avail, base, quad_of):
    """Fewest distinct earlier members summing to exactly diff (no royal part).
    Returns k, or None if diff is not a pure sum with <= MAXK terms."""
    if diff <= 0:
        return None
    cand = [p for p in avail[:bisect.bisect_right(avail, diff)] if p != base]
    if not cand:
        return None
    prefix = [0]
    for p in cand:
        prefix.append(prefix[-1] + p)
    bq = quad_of[base]
    for k in range(1, MAXK + 1):
        if deriver._fixed(diff, k, {0}, cand, prefix, quad_of, bq) is not None:
            return k
    return None


def run(chain, label, report=True):
    """chain: ascending list of 4-tuples.  Mirrors extend_chain's base choice."""
    deriver = lc.Deriver()
    avail = list(chain[0])
    quad_of = {p: 1 for p in chain[0]}
    dist, exc, n = {}, [], 0
    t0 = time.time()
    for i in range(1, len(chain)):
        quad = chain[i]
        base = chain[i - 1][-1]        # m_k, the largest member of Q_{k-1}
        for target in quad:
            diff = target - base
            k = pure_k(deriver, diff, avail, base, quad_of)
            n += 1
            if k is None:
                exc.append(diff)
            else:
                dist[k] = dist.get(k, 0) + 1
        for p in quad:
            avail.append(p)
            quad_of[p] = i + 1
    worst = max(dist) if dist else 0
    ue = sorted(set(exc))
    if report:
        print(f"{label}")
        print(f"    members {n}   worst pure-additive gap {worst} terms   "
              f"exceptional gaps {len(ue)} unique / {len(exc)} members"
              + (f"   max {max(ue)}" if ue else ""))
        print("    terms: " + "  ".join(f"{k}:{dist[k]}" for k in sorted(dist))
              + f"    [{time.time()-t0:.0f}s]")
        if ue and len(ue) <= 20:
            print(f"    exceptions: {ue}")
    return {"n": n, "worst": worst, "exc": ue, "dist": dist}


def controls(firsts, seed, kind):
    """Non-prime chains with the same spacing as the real one."""
    rnd = random.Random(seed)
    out, prev = [], 0
    for k, p in enumerate(firsts):
        lo = firsts[k - 1] if k else 0
        hi = firsts[k + 1] if k + 1 < len(firsts) else p + 30
        if kind == "jitter":            # nudge inside the local gap
            span = max(2, min(p - lo, hi - p) // 2)
            q = p + rnd.randint(-span // 2, span // 2)
        elif kind == "uniform":         # uniform in the gap to the next one
            q = rnd.randint(lo + 1, max(lo + 2, hi - 1))
        elif kind == "shift":           # rigid shift off the prime residues
            q = p + 30 * ((k % 7) + 1)
        out.append(max(q, prev + 12))
        prev = out[-1]
    return [(q, q + 2, q + 6, q + 8) for q in out]


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    d = json.load(open("/Users/pankajladhe/Pankaj/2018/AIStuff/RSAL/LC/paper/qarray_1e9.json"))
    quads = [tuple(q["primes"]) for q in d["quads"][:N]]
    firsts = [q[0] for q in quads]
    print(f"=== chains of {N} quadruplets, lc.py's own Deriver, pure additive only ===\n")
    run(quads, "REAL prime quadruplets")
    print()
    for kind in ("jitter", "uniform", "shift"):
        for seed in (1, 2):
            run(controls(firsts, seed, kind), f"CONTROL {kind} seed {seed} (not prime)")
            if kind == "shift":
                break
