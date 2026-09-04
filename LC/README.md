# LC - quad chain builder

`lc.py` grows a q-array of prime "quads" from the royal quad and shows how
every prime in every quad is derived from earlier ones.

## Run it

```
python3 lc.py                  # asks: how many quads?
python3 lc.py 25               # first 25 quads after the royal quad
python3 lc.py --upto 35551421  # every quad whose first prime is <= value
python3 lc.py 25 -v            # also show which quad each term came from
python3 lc.py 25 -M            # multiplicative ways M and M1 (see "Three ways")
python3 lc.py 25 -E            # exponential ways E1, E2 and E3
python3 lc.py 25 -AME          # every way, labeled A:, M:, M1:, E1:, E2:, E3: (-AM, -ME also work)
python3 lc.py 25 -aem          # lowercase works too, alone or combined (-a -e -m, -aeM)
python3 lc.py 2000 -o          # only the 2000th quad (-one and --only do the same)
python3 lc.py --upto 35551421 -o   # only the last quad at or below the value
python3 lc.py 25 --all         # equations for all four primes, not just the first
python3 lc.py -d 53            # derive any integer from the quad members below it
python3 lc.py -d 53 83         # every integer from 53 to 83, one line each
python3 lc.py 25 --recompute   # ignore qarray.json and rebuild
python3 lc.py 25 --one-per-quad   # stricter rule, see below
```

At the prompt you can type a count (`25`) or `upto 35551421`.

## The rules

1. The q-array starts with the royal / initial quad `2, 3, 5, 7`.
2. Every later quad is the next four primes ending in 1, 3, 7, 9 that sit
   together: `p, p+2, p+6, p+8` (a prime quadruplet). Quad 1 is
   `11, 13, 17, 19`, quad 2 is `101, 103, 107, 109`, and so on.
3. Quad 1 is written with `+` and `*` over royal members only, e.g.
   `11 = (2*3) + 5`. Alternatives, including the ones that use `-`, are
   listed under it. Minus is not used anywhere else.
   Layout: products are wrapped in parentheses and larger terms come first,
   so `101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)`.
4. Every prime of quad k (k >= 2) is written as

   ```
   one member of the last quad (quad k-1)
   + members of earlier non-royal quads, each prime used at most once
   + optionally an expression in royal members using only + and *
   ```

   Quad members are exhausted with addition before any multiplication
   among royal members is used. Candidates are ranked by:

   1. depth of the royal part: plain addition (none, or royal members
      added) first, then flat products such as `(5*7) + 3`, and products
      that contain sums (nested parentheses) only as a last resort;
   2. fewer multiplications in the royal part: addition takes precedence,
      multiply only when addition is not possible;
   3. fewer terms, but no matter how long, an addition-only equation beats
      one with a product;
   4. larger primes first, compared term by term, so a quad's 9-member is
      used before its 7, 3 and 1 members.

   ```
   13001 = 9439 + 3461 + 101                       plain addition, 2 terms
   3461  = 3259 + 199 + 3                          9-member first (not 191 + 11)
   1871  = 1489 + 109 + 107 + 103 + 19 + 17 + 13 + 11 + 3
                                                   addition only, 8 terms
   101   = 19 + 17 + 13 + 11 + (5*7) + (2*3)       products only because
                                                   addition cannot reach 82
   not     19 + 17 + (5*(7 + (2*3)))               nested, rejected
   ```

5. Storage in `qarray.json` beside the script: each quad records, per
   prime, only the base (the last-quad member) and the difference, e.g.
   `191 = 109 + 82` is stored as base 109, diff 82. A separate `diffs`
   table holds one equation per unique difference
   (`82 = 17 + 13 + 11 + (5*7) + (2*3)`). When a later quad produces a
   difference already in the table, its equation is reused and the output
   says so; only a new difference triggers a new search. The next run loads
   the file and computes only quads that are not there yet.
6. The display shows one line per quad, the prime ending in 1 with its full
   equation (base first, then the difference written out):

   ```
   Quad 7: 2081
     2081 = 1879 + 199 + 3
   ```

   All four primes are still derived and saved; pass `--all` to print them.
   Pass `-v` to also see the difference, whether its equation was reused,
   and which quad each term came from.

   `-o` (also `-one` or `--only`) narrows the output to a single quad: with a
   count it is the count-th quad, with `--upto` the last quad at or below the
   value. It combines with the other switches, so `./lc 2000 -o -AME --all`
   prints every way of all four primes of quad 2000 and nothing else:

   ```
   Quad 2000: 31252931
     31252931 = 31210849 + 34849 + 5651 + 1481 + 101
   ```

## Three ways

Every difference is stored with an additive, a multiplicative and two
exponential equations, and every prime additionally gets a multiplicative
and an exponential equation that do not use the base at all. `-A` (default),
`-M` and `-E` pick which to print; combine them (`-AME`, `-ME`) to see
several, labeled `A:`, `M:`, `M1:`, `E1:`, `E2:`, `E3:`.

- **A, additive**: the rules above; quad primes are added, royal members
  only when addition cannot reach the difference.
- **M, multiplicative**: any members, quad primes and royal members alike,
  may be multiplied in pairs, and multiplication is preferred over addition.
  Greedy: take the largest unused member, multiply it by the largest member
  that still fits, repeat; add plain members only when nothing can be
  multiplied; backtrack on a dead end.
  `101 = 19 + (17*3) + (13*2) + 5`
- **E, exponential**: members may also be raised to a member power (base and
  exponent are both members). Powers first, then products, then addition.
  Two options are printed, since the order in which powers are tried
  changes the result:
  - `E1` largest base first (then largest exponent that fits):
    `5651 = 3469 + (19^2) + (11^3) + (17*7) + (13*5) + 199 + 107`
  - `E2` largest power value first:
    `5651 = 3469 + (2^11) + (19*5) + (13*3)`

  When both orders give the same equation only the `E1` line is printed,
  e.g. `E1: 101 = 19 + (7^2) + (11*3)`.
- **M1, without the base**: the multiplicative search applied to the whole
  prime instead of the difference. No base term is required; the pool is
  every quad prime below the target plus the royal members, so the largest
  products carry the number.
- **E3, powers first**: the largest power `b^e` below the prime, with base
  and exponent distinct members, then again the largest power below what is
  left as long as it covers at least half of it, and then the remainder
  written the additive way: quad primes added, largest first, closed by a
  flat royal `+`/`*` expression. If no choice of primes closes the
  remainder, the chain loses its last power, and finally the next largest
  first power is tried (11, 17 and 19, written from the royal quad alone, have
  no such form and fall back to the power-first search).

  ```
  A:  854921 = 845989 + 5659 + 3259 + 11 + 3
  M:  854921 = 845989 + (3469*2) + (199*7) + (193*3) + 17 + 5
  M1: 854921 = (427249*2) + (109*3) + (17*5) + 11
  E1: 854921 = 845989 + (19^3) + (17^2) + (199*5) + (11*7) + 197 + 191 + 107 + 103 + 101 + 13
  E2: 854921 = 845989 + (2^13) + (7^3) + (19*11) + (17*5) + 103
  E3: 854921 = (829^2) + (11^5) + (17^3) + 1489 + 107 + 101 + 19
  E3: 19497221 = (11^7) + (2^13) + 829 + 827 + 199 + 3
  E3: 31204931 = (11^7) + (3259^2) + (103^3) + 3467 + 193 + 191 + 101
  ```

  (7^7 = 823543 is closer to 854921 than 829^2, but it would use 7 twice.)
  A line that repeats an earlier line of the same prime (quad 1, where
  there is no base anyway) is not printed twice.

Every member is used at most once in an equation, and in A, M, E1 and E2
the base is always the last quad's 9-member. Term lists are stored in
`qarray.json` under `mul`, `exp` (E1) and `expv` (E2) of each difference,
and under `mul_nb` (M1) and `exp_nb` (E3) of each prime, as `["p", 5]`,
`["*", 17, 3]`, `["^", 7, 2]`. If a search ever gives up, the entry copies a
simpler way and is marked `fallback`; `-v` mentions it.

## Derive any number

`-d N` writes any integer N as a sum of quad primes below N plus one
expression in the royal members. Quad primes are only added; `-`, and `*`
appear only among 2, 3, 5, 7. The largest quad prime that fits is taken
first, then the next, and the remainder is closed with a flat royal
expression (never a product containing a sum, so `(3*7) - 5` rather than
`(2*(5 + 3))`), choosing the one with the fewest multiplications, then the
fewest minus signs. Primes are re-chosen if that is what it takes to keep
the closing flat.

```
python3 lc.py -d 16     16 = 13 + 3
python3 lc.py -d 53     53 = 19 + 17 + 13 + 7 - 3
python3 lc.py -d 55     55 = 19 + 17 + 13 + 5 + 3 - 2
python3 lc.py -d 76     76 = 19 + 17 + 13 + 11 + (3*7) - 5
python3 lc.py -d 101    101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)
python3 lc.py -d 0      0 = 5 - (3 + 2)
```

Every integer from 0 up to the next quad's first prime has such a
derivation (with 2, 3, 5, 7, 11, 13, 17, 19 every integer up to 156, so in
particular up to 101); the paper proves this for the whole chain. `-v` adds
which quad each prime came from. Two numbers give a range: `-d 53 83`
prints one line for every integer from 53 to 83. If N lies beyond the cached chain, the
chain is extended first, which for N near 10^9 takes about three minutes
once.

## About "each quad can be used only once"

The tool applies this as "each prime is used at most once in an equation";
several members of one quad may appear together (the reference equation
above uses both 19 and 17 from quad 1). The stricter reading, at most one
member per quad, is available with `--one-per-quad` and keeps its own cache
file `qarray_one_per_quad.json`. Under that reading quad 2 has no valid
equation: every `101..109` minus a single member of `11..19` leaves a
remainder (82 to 98) that no `+`/`*` expression in `2, 3, 5, 7` produces.

## How far it can go

Output ends with a plain `N quads shown`; `-v` adds cache and reuse
statistics. Measured on this Mac (Intel, Python 3.13):

| upper bound | digits | quads | time to build | cache size |
| --- | --- | --- | --- | --- |
| 35,551,421 | 8 | 2,209 | 14 s | 5.7 MB |
| 200,000,000 | 9 | 8,096 | 54 s | 16.8 MB |
| 1,000,000,000 | 10 | 28,387 | 165 s | 48 MB |
| 10,000,000,000 | 11 | ~180,000 | ~25 min (est.) | ~330 MB |

Recommended limit: 10 digits (`--upto 9999999999`) is comfortable in one
run. 11 digits works but the JSON cache gets large and slow to load; past
that the cache would need a database and the sieve a compiled helper. Most
of the cache size comes from the base-free M1 and E3 equations, which are
stored per prime rather than per unique difference.
Progress is checkpointed to the cache every 15 seconds, so an interrupted
run resumes where it stopped.

## Videos and app

Two explainer videos, narrated and captioned:

- Ladhe's Quad Conjecture: A New Pattern in Prime Quadruplets (28 min): https://youtu.be/_XSOJ0Yj77Q
- Build Any Number From Prime Quadruplets, Part 2 (11 min): https://youtu.be/JNWvt3hS540

Companion iOS app (the authors' free LE-Games app; the Quad Conjecture feature is being added): https://apps.apple.com/app/id6767880385

## Paper

`paper/` holds the Zenodo preprint *Ladhe's Quad Conjecture* (DOI
https://doi.org/10.5281/zenodo.22286847) and everything needed to reproduce its
figures:

| File | Purpose |
| --- | --- |
| `ladhe_quad_conjecture.tex`, `.pdf` | the paper (`pdflatex ladhe_quad_conjecture.tex`, run twice) |
| `qarray_1e9.json` | the chain up to 10^9 (28,387 quads, 48 MB), built with `python3 lc.py --upto 999999999 --cache paper/qarray_1e9.json`; in the repository it is shipped as `qarray_1e9.json.gz`, run `gunzip` before using it |
| `quads_1e9.csv` | one row per quad member: base, gap, the A/M/E1/E2 equations, minimal lengths (M1/E3 are in the JSON) |
| `check.py` | independent re-verification of every stored equation, prints the dataset SHA-256 |
| `stats.py` | every number quoted in the paper, plus `appendix_rows.tex` and the CSV |

## Executable

`lc.py` already runs directly (`./lc.py 10`). A standalone binary `lc` that
needs no Python install is built with PyInstaller:

```
cd /Users/pankajladhe/Pankaj/2018/AIStuff/RSAL/LC
python3 -m PyInstaller --onefile --name lc --distpath ./dist \
        --workpath ./build --specpath ./build lc.py
mv dist/lc ./lc && rm -rf build dist
./lc 10
```

Keep `lc` next to `qarray.json`: the binary reads and writes the cache in
its own folder. Rebuild it after editing `lc.py`.

## Files

| File | Purpose |
| --- | --- |
| `lc.py` | the program, no dependencies beyond Python 3 |
| `lc` | standalone macOS binary built from `lc.py` with PyInstaller |
| `qarray.json` | saved q-array: quads with base + difference, plus the `diffs` table of unique-difference equations |
| `qarray_one_per_quad.json` | same, for `--one-per-quad` (created on first use) |
| `paper/` | the paper, its dataset and the reproduction scripts (see "Paper") |
| `videos/` | two explainer videos, on YouTube at https://youtu.be/_XSOJ0Yj77Q (the conjecture, 28 min) and https://youtu.be/JNWvt3hS540 (build any number, 11 min); `videos/LINKS.md` has the links and thumbnails, plus the narration scripts, the YouTube upload package and the `build/` pipeline that rendered them (the MP4 files are too large for GitHub) |
