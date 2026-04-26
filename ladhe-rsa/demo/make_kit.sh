#!/usr/bin/env bash
#
# make_kit.sh — Build a self-contained Ladhe verification kit.
#
# Output: ladhe_demo_kit.zip in the current directory, containing:
#   - verify.py           (zero-dep standalone verifier)
#   - ca.cert.pem         (the CA's cert)
#   - alice.cert.pem      (Alice's cert, signed by the CA)
#   - <doc>               (the document Alice signed)
#   - <doc>.sig           (Alice's signature on the document)
#   - README.txt          (instructions for the recipient)
#
# Usage:
#     ./make_kit.sh                                # uses purchase_order.txt
#     ./make_kit.sh path/to/some_other_file.docx   # signs that file instead
#
# Prereq: ./setup.sh has been run at least once (creates ca/ alice/ bob/).

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LADHE="$(cd "$HERE/.." && pwd)"

# ---------------------------------------------------------------------
# Pick the document to sign (default: purchase_order.txt)
# ---------------------------------------------------------------------
DOC_SRC="${1:-$HERE/purchase_order.txt}"
if [[ ! -f "$DOC_SRC" ]]; then
    echo "ERROR: document not found: $DOC_SRC" >&2
    exit 1
fi
DOC_BASENAME="$(basename "$DOC_SRC")"

# ---------------------------------------------------------------------
# Make sure the demo PKI exists; bootstrap if missing
# ---------------------------------------------------------------------
if [[ ! -f "$HERE/ca/ca.cert.pem" || ! -f "$HERE/alice/alice.cert.pem" ]]; then
    echo ">> Demo PKI missing; running setup.sh first..."
    "$HERE/setup.sh"
fi

# ---------------------------------------------------------------------
# Sign the document with Alice's key (overwrite any old .sig)
# ---------------------------------------------------------------------
cp -f "$DOC_SRC" "$HERE/alice/$DOC_BASENAME"
rm -f "$HERE/alice/$DOC_BASENAME.sig"

cd "$LADHE"
python3 ladhe_cert_cli.py sign \
    --subject alice \
    --dir "$HERE/alice" \
    --doc "$HERE/alice/$DOC_BASENAME" \
    --sig "$HERE/alice/$DOC_BASENAME.sig"

# ---------------------------------------------------------------------
# Stage the kit in a temp directory
# ---------------------------------------------------------------------
STAGE="$(mktemp -d -t ladhe_kit.XXXXXX)/ladhe_demo_kit"
mkdir -p "$STAGE"

cp "$LADHE/verify.py"                       "$STAGE/verify.py"
cp "$HERE/ca/ca.cert.pem"                   "$STAGE/ca.cert.pem"
cp "$HERE/alice/alice.cert.pem"             "$STAGE/alice.cert.pem"
cp "$HERE/alice/$DOC_BASENAME"              "$STAGE/$DOC_BASENAME"
cp "$HERE/alice/$DOC_BASENAME.sig"          "$STAGE/$DOC_BASENAME.sig"

# ---------------------------------------------------------------------
# Generate README.txt for the recipient
# ---------------------------------------------------------------------
cat > "$STAGE/README.txt" <<EOF
LADHE VERIFICATION KIT
======================

This bundle contains a digitally signed document and the tools to
verify it. The signature was produced with Ladhe, a one-time
hash-based signature scheme whose security reduces to SHA-256
preimage resistance (paper: https://zenodo.org/records/19738891).

CONTENTS
--------
  verify.py              standalone verifier (no installs needed)
  ca.cert.pem            the certificate authority's cert
  alice.cert.pem         the signer's cert (issued by the CA)
  $DOC_BASENAME            the signed document
  $DOC_BASENAME.sig        Alice's signature on the document
  README.txt             this file

REQUIREMENTS
------------
  Python 3.9 or newer. That's it. No pip install. No virtualenv.

VERIFY EVERYTHING (the easy way)
---------------------------------
  cd ladhe_demo_kit
  python3 verify.py

  Expected last line: "All verifications passed."

ATTEMPT A TAMPER (the demo's punchline)
----------------------------------------
  1. Open  $DOC_BASENAME  in your editor.
  2. Change ANY single byte (one digit, one letter — anything).
  3. Save the file.
  4. Re-run:    python3 verify.py
  5. The signature check should now FAIL — that's the math
     catching the tampering.
  6. Restore the file from the original and verify again — passes.

EXPLICIT MODE (per-step)
------------------------
  python3 verify.py verify-cert alice.cert.pem ca.cert.pem
  python3 verify.py verify-doc  $DOC_BASENAME  $DOC_BASENAME.sig  alice.cert.pem

QUESTIONS / FEEDBACK
--------------------
  spalgorithm@gmail.com

Thank you for taking the time to test this.
EOF

# ---------------------------------------------------------------------
# Bundle into a zip in the user's CWD
# ---------------------------------------------------------------------
KIT_NAME="${KIT_NAME:-ladhe_demo_kit.zip}"
OUT="$(pwd)/$KIT_NAME"
rm -f "$OUT"

(cd "$(dirname "$STAGE")" && zip -r -q "$OUT" "ladhe_demo_kit")

# Clean up the stage
rm -rf "$(dirname "$STAGE")"

echo ""
echo "==============================================="
echo "  Kit built: $OUT"
echo ""
echo "  Contents:"
unzip -l "$OUT" | sed 's/^/    /'
echo ""
echo "  To test locally:"
echo "    rm -rf /tmp/ladhe_kit_test && unzip -d /tmp/ladhe_kit_test \"$OUT\""
echo "    cd /tmp/ladhe_kit_test/ladhe_demo_kit && python3 verify.py"
echo "==============================================="
