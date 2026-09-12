"""Every figure quoted for Lemma 1 (the congruences modulo 210).

    python3 paper/residues.py paper/quads_1e9.csv

Recomputes, from the released CSV alone:
  * the residues modulo 210 of the first members,
  * the spacings between consecutive first members,
  * the twenty residue classes of the gaps, against the ones the lemma predicts,
  * the least number of distinct chain members summing to each admissible value
    below 400000 (the largest gap below 10^9 is 395520), and
  * the classes in which a two-term sum is impossible modulo 7.
"""
import csv
import sys
from collections import Counter

LIMIT = 400000          # covers every gap below 10^9
OFFSETS = (0, 2, 6, 8)  # a member's offset inside its quadruplet
MAXK = 8                # the bound K of Conjecture 2


def load(path):
    """first members, all members below LIMIT, distinct gaps."""
    firsts, members, gaps = set(), set(), set()
    for row in csv.DictReader(open(path)):
        firsts.add(int(row["p"]))
        m = int(row["member"])
        if m <= LIMIT:
            members.add(m)
        if row["difference"]:
            gaps.add(int(row["difference"]))
    return sorted(firsts), sorted(members), sorted(gaps)


def least_terms(members, limit, maxk):
    """least[n] = fewest distinct members summing to n, or None (bitset sweep)."""
    mask = (1 << (limit + 1)) - 1
    reach = [1] + [0] * maxk
    for s in members:
        for c in range(maxk, 0, -1):
            reach[c] |= (reach[c - 1] << s) & mask
    def kmin(n):
        for c in range(1, maxk + 1):
            if reach[c] >> n & 1:
                return c
        return None
    return kmin


def main(path):
    firsts, members, gaps = load(path)
    print(f"{len(firsts)} quadruplets, {len(gaps)} distinct gaps, "
          f"largest gap {max(gaps)}")

    # (ii) the first members lie in three classes modulo 210
    print("p mod 210:", sorted(Counter(p % 210 for p in firsts).items()))
    print("p mod 7  :", sorted(Counter(p % 7 for p in firsts).items()))

    # (iii) the spacings between consecutive first members
    spacings = {(b - a) % 210 for a, b in zip(firsts, firsts[1:])}
    print("h mod 210:", sorted(spacings), "(lemma: [0, 30, 90, 120, 180])")

    # (iv) the twenty classes of the gaps
    predicted = sorted({(h + d - 8) % 210
                        for h in (0, 30, 90, 120, 180) for d in OFFSETS})
    observed = sorted({d % 210 for d in gaps})
    print(f"gap classes mod 210: {len(observed)} observed, "
          f"{len(predicted)} predicted, equal: {observed == predicted}")
    print("  ", predicted)

    # the admissible values below the limit, and how many terms each needs
    kmin = least_terms(members, LIMIT, MAXK)
    admissible = [n for n in range(2, LIMIT + 1, 2) if n % 210 in predicted]
    print(f"{len(members)} members below {LIMIT}, "
          f"{len(admissible)} admissible values")
    print(f"not a sum of at most {MAXK} distinct members:",
          [n for n in admissible if kmin(n) is None])
    for k in (4, 6):
        over = [n for n in admissible if (kmin(n) or MAXK + 1) > k]
        print(f"admissible values needing more than {k} terms: {len(over)}, "
              f"largest {max(over)}")

    # the paper excludes the base m_k as a term; it is below its own gap for
    # only a few members, so check those cases without it
    tight = sorted({(int(r["base"]), int(r["difference"])) for r in
                    csv.DictReader(open(path))
                    if r["base"] and r["difference"]
                    and int(r["base"]) < int(r["difference"])})
    worse = []
    for base, d in tight:
        pool = [m for m in members if m < d and m != base]
        if least_terms(pool, d, MAXK)(d) is None and kmin(d) is not None:
            worse.append((base, d))
    print(f"gaps whose base is below them: {len(tight)}; "
          f"representable only with the base: {worse or 'none'}")

    # the values a gap can never take, though they are equally unreachable
    blocked = [n for n in range(2, LIMIT + 1, 2)
               if n % 30 in (0, 22, 24, 28) and n % 210 not in predicted
               and kmin(n) is None]
    print("unreachable but excluded by the lemma:", blocked)

    # two distinct members are 2,3,4 mod 7, so their sum misses two classes each
    ok7 = [x for x in range(7) if all((x + d) % 7 for d in OFFSETS)]
    def two_term(m):
        """can a class m mod 210 hold a sum of two members?"""
        return any((22 + a + b) % 30 == m % 30 and (x + a + y + b) % 7 == m % 7
                   for a in OFFSETS for b in OFFSETS
                   for x in ok7 for y in ok7)
    over30 = [m for m in range(0, 210, 2) if m % 30 in (0, 22, 24, 28)]
    unreachable = [m for m in over30 if not two_term(m)]
    print(f"of the {len(over30)} classes over the four gap classes mod 30, "
          f"{len(unreachable)} admit no two-term sum:", unreachable)
    print("no gap class among them:",
          not set(unreachable) & set(predicted))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quads_1e9.csv")
