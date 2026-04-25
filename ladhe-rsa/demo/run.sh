#!/usr/bin/env bash
#
# run.sh — Live Alice & Bob demo over a Ladhe-issued PKI.
#
# Acme Quantum CA issues certs for Alice and Bob; Alice signs a
# $1.25M purchase order; Bob verifies the cert chain and the
# signature; a tamper attempt is caught. Press ENTER between steps.
#
# Run from this folder:
#     ./run.sh
#
# Prereq:  ./setup.sh has been run at least once (creates ca/ alice/ bob/).

set -e

# ----------------------------------------------------------------------
# Resolve paths relative to this script
# ----------------------------------------------------------------------
HERE="$(cd "$(dirname "$0")" && pwd)"
LADHE_DIR="$(cd "$HERE/.." && pwd)"
CA_DIR="$HERE/ca"
ALICE_DIR="$HERE/alice"
BOB_DIR="$HERE/bob"
DOC_NAME="purchase_order.txt"
SIG_NAME="purchase_order.txt.sig"

# ----------------------------------------------------------------------
# Colours
# ----------------------------------------------------------------------
BOLD=$'\033[1m'
BLUE=$'\033[1;34m'
GREEN=$'\033[1;32m'
RED=$'\033[1;31m'
YELLOW=$'\033[1;33m'
RESET=$'\033[0m'

banner()  { echo ""; echo "${BLUE}======================================================================${RESET}"; echo "${BOLD}$1${RESET}"; echo "${BLUE}======================================================================${RESET}"; }
narrate() { echo "${YELLOW}$1${RESET}"; }
pause()   { echo ""; read -r -p "${BOLD}Press ENTER to continue...${RESET}"; echo ""; }
run()     { echo "${GREEN}\$ $*${RESET}"; eval "$@"; }

# ----------------------------------------------------------------------
# Pre-flight: make sure the demo PKI exists
# ----------------------------------------------------------------------
if [[ ! -f "${ALICE_DIR}/alice.cert.pem" || ! -f "${BOB_DIR}/bob.cert.pem" || ! -f "${CA_DIR}/ca.cert.pem" ]]; then
    echo "${RED}ERROR:${RESET} demo PKI missing. Run ./setup.sh first."
    exit 1
fi
if [[ ! -f "${ALICE_DIR}/${DOC_NAME}" ]]; then
    cp "$HERE/${DOC_NAME}" "${ALICE_DIR}/${DOC_NAME}"
fi

cd "${LADHE_DIR}"

# Reset Bob's folder to a clean slate
rm -f "${BOB_DIR}/${DOC_NAME}" \
      "${BOB_DIR}/${SIG_NAME}" \
      "${BOB_DIR}/alice.cert.pem" \
      "${ALICE_DIR}/${SIG_NAME}" 2>/dev/null || true

# ======================================================================
# INTRO
# ======================================================================
clear
banner "Ladhe Quantum-Safe Certificates — Live Demo"
cat <<'EOF'

Scenario: Acme Corporation runs its own internal quantum-safe CA.

  - Alice, Director of Procurement, needs to approve a $1.25M
    purchase order.
  - Bob, in Finance, must verify the approval is authentic before
    processing payment.
  - Both have certificates issued by Acme Quantum CA, signed
    with Ladhe — a one-time hash-based signature scheme whose
    security reduces to SHA-256 preimage resistance (same
    foundation as SPHINCS+ / SLH-DSA).

This demo shows quantum-safe PKI workflows in action.

EOF
pause

# ======================================================================
# STEP 1
# ======================================================================
banner "Step 1 — Alice's quantum-safe certificate"
narrate "This is what a Ladhe certificate looks like. Issued by"
narrate "Acme Quantum CA. Signature OID 1.3.6.1.4.1.65644.1.1."
echo ""
run "cat ${ALICE_DIR}/alice.cert.pem"
pause

# ======================================================================
# STEP 2
# ======================================================================
banner "Step 2 — The document Alice is approving"
narrate "A \$1.25 million purchase order. Bob needs to know this"
narrate "really came from Alice — and the amount wasn't altered."
echo ""
run "cat ${ALICE_DIR}/${DOC_NAME}"
pause

# ======================================================================
# STEP 3
# ======================================================================
banner "Step 3 — Alice signs with her private key"
narrate "Alice's private key (her sorted prime decomposition) never"
narrate "leaves her machine. Signing reveals it — Ladhe is one-time;"
narrate "Alice would use a fresh keypair for the next document."
echo ""
run "python3 ladhe_cert_cli.py sign \
    --subject alice \
    --dir ${ALICE_DIR} \
    --doc ${ALICE_DIR}/${DOC_NAME}"
pause

# ======================================================================
# STEP 4
# ======================================================================
banner "Step 4 — Alice sends the package to Bob"
narrate "Bob receives three files: the document, Alice's certificate,"
narrate "and the signature. Transport doesn't matter — email, Slack,"
narrate "a message bus, a USB stick. The math does the work."
echo ""
run "cp ${ALICE_DIR}/${DOC_NAME}     ${BOB_DIR}/"
run "cp ${ALICE_DIR}/${SIG_NAME}     ${BOB_DIR}/"
run "cp ${ALICE_DIR}/alice.cert.pem  ${BOB_DIR}/"
pause

# ======================================================================
# STEP 5
# ======================================================================
banner "Step 5 — Bob verifies Alice's certificate against the CA"
narrate "Bob trusts the Acme Quantum CA. He checks that Alice's cert"
narrate "was genuinely issued by that CA — the same chain of trust"
narrate "any enterprise PKI uses today."
echo ""
run "python3 ladhe_cert_cli.py verify \
    --cert ${BOB_DIR}/alice.cert.pem \
    --ca   ${CA_DIR}/ca.cert.pem"
pause

# ======================================================================
# STEP 6
# ======================================================================
banner "Step 6 — Bob verifies the signature on the document"
narrate "Now Bob verifies that the document was actually signed by"
narrate "Alice, and matches what she signed — byte for byte."
echo ""
run "python3 ladhe_cert_cli.py verify-doc \
    --subject alice \
    --dir ${BOB_DIR} \
    --doc ${BOB_DIR}/${DOC_NAME} \
    --sig ${BOB_DIR}/${SIG_NAME}"
pause

# ======================================================================
# STEP 7
# ======================================================================
banner "Step 7 — The tamper test: an attacker changes the amount"
narrate "Imagine an attacker intercepts this message and changes"
narrate "\$1,250,000 to \$12,500,000 — a 10x multiplier. Watch what"
narrate "happens when Bob re-verifies."
echo ""
run "sed -i '' 's/1,250,000/12,500,000/' ${BOB_DIR}/${DOC_NAME}"
echo ""
narrate "Bob's copy now shows the tampered amount:"
echo ""
run "grep Amount ${BOB_DIR}/${DOC_NAME}"
echo ""
narrate "Bob re-runs the same verify command. This time it should fail:"
echo ""
set +e
python3 ladhe_cert_cli.py verify-doc \
    --subject alice \
    --dir "${BOB_DIR}" \
    --doc "${BOB_DIR}/${DOC_NAME}" \
    --sig "${BOB_DIR}/${SIG_NAME}"
VERIFY_RC=$?
set -e
echo ""
if [[ ${VERIFY_RC} -ne 0 ]]; then
    echo "${RED}${BOLD}Signature rejected. The tamper was caught.${RESET}"
else
    echo "${RED}${BOLD}UNEXPECTED: signature verified a tampered document.${RESET}"
fi
pause

# ======================================================================
# OUTRO
# ======================================================================
banner "Demo complete"
cat <<'EOF'

What we just proved:

  1. Hash-based signatures work today.
  2. They drop into the same PKI workflow that enterprise CAs use.
  3. Tampered documents are rejected immediately by the math —
     no trust required, no separate audit trail.
  4. Pure software, open source, no hardware changes.
  5. Ladhe is one-time per keypair. For multi-signature use,
     a Merkle-aggregated extension is sketched in the paper (§6).

EOF

# Restore Bob's copy so the demo can be re-run cleanly
cp "${ALICE_DIR}/${DOC_NAME}" "${BOB_DIR}/${DOC_NAME}"
