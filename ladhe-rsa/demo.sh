#!/usr/bin/env bash
#
# demo.sh — Reproduce every command shown in the
#   "Ladhe-RSA Signatures" explainer video.
#
# Usage:
#   chmod +x demo.sh         # first time only
#   ./demo.sh                # run the whole demo
#
# Runs cleanly on macOS and Linux with Python 3.9+.
#

set -euo pipefail
cd "$(dirname "$0")"

banner() {
    printf "\n"
    printf "============================================================\n"
    printf "  %s\n" "$1"
    printf "============================================================\n"
}

pause() {
    if [ -t 1 ]; then
        printf "\n[press ENTER to continue] "
        read -r _
    fi
}

# -----------------------------------------------------------
banner "Demo 1 — See it in action (from the video)"
# -----------------------------------------------------------
# Runs the full built-in demo: keygen → identification →
# signature → tamper check → LDP challenge.
python3 ladhe_rsa.py demo
pause

# -----------------------------------------------------------
banner "Demo 2 — Try to break it (the LDP challenge)"
# -----------------------------------------------------------
# Generates a fresh Ladhe Decomposition Problem instance.
# Anyone who can solve this faster than brute force has
# broken the scheme.
python3 -c "
import ladhe_rsa as LR
P, h, s = LR.generate_ldp_challenge(bits=32)
print('Your LDP challenge:')
print('  P    =', P)
print('  salt =', s.hex())
print('  h    =', h.hex())
print()
print('Task: find (a, b, c) > 0 with:')
print('  a + b + c = P')
print('  sha256(salt || canonical_encode(a, b, c)) == h')
"
pause

# -----------------------------------------------------------
banner "Demo 3 — The unit test suite"
# -----------------------------------------------------------
python3 -m unittest test_ladhe_rsa -v
pause

# -----------------------------------------------------------
banner "Demo 4 — Practical software-signing example"
# -----------------------------------------------------------
# Bob signs a release, an attacker tampers (fails),
# Alice verifies the genuine release (succeeds).
python3 example_code_signing.py
pause

# -----------------------------------------------------------
banner "Demo 5 — One-liner sanity check"
# -----------------------------------------------------------
python3 -c "
import ladhe_rsa as LR
pk, sk = LR.keygen()
sig = LR.sign(b'hi', sk, pk)
print('genuine message verifies:', LR.verify(b'hi', sig, pk))
print('tampered message rejects:', not LR.verify(b'evil', sig, pk))
"

printf "\n"
printf "============================================================\n"
printf "  All demos complete.\n"
printf "\n"
printf "  Next steps:\n"
printf "    * Read MANUAL_TESTING.md for deeper, step-by-step testing.\n"
printf "    * Read the paper: https://zenodo.org/records/19680322\n"
printf "    * If you break it, open an issue on the GitHub repo.\n"
printf "============================================================\n"
