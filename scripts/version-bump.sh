#!/bin/sh
# Version bump script — single source of truth for all cyim version references.
#
# Usage:
#   sh scripts/version-bump.sh 1.3.0          # bump VERSION + regenerate everything
#   sh scripts/version-bump.sh "$(cat VERSION)" # regenerate without bumping
#
# Why this exists: the v1.2.2 toolchain bump initially shipped with
# `print_version` still emitting "cyim 1.2.1" because the literal was
# hardcoded into src/main.cyr and the version-sync checklist
# (VERSION / cyrius.cyml / CHANGELOG header) didn't include it.
# This script regenerates `src/version_str.cyr` unconditionally so
# the literal can never drift again. Same pattern cyrius uses for
# `cc5 --version`.

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Current: $(cat VERSION)"
    exit 1
fi

NEW="$1"
OLD=$(cat VERSION | tr -d '[:space:]')

# 1. Regenerate src/version_str.cyr unconditionally — including same-version
#    invocations. This file is the single source of truth for the cyim
#    `--version` string; if it drifts vs `VERSION`, `cyim --version` reports
#    stale data. Same-version `version-bump.sh "$(cat VERSION)"` is the
#    documented "regenerate without bumping" path.
LEN_CYIM=$((${#NEW} + 6))   # "cyim " + version + "\n"
cat > src/version_str.cyr <<EOF
# src/version_str.cyr — AUTO-GENERATED from \`VERSION\` by
# \`scripts/version-bump.sh\`. Do NOT edit by hand; the next bump
# will overwrite. To regenerate without bumping, run:
#
#   sh scripts/version-bump.sh "\$(cat VERSION)"
#
# Why this file exists: the v1.2.2 toolchain bump shipped with
# \`print_version\` still emitting "cyim 1.2.1" because the literal
# was hardcoded into \`src/main.cyr\` and the version-sync checklist
# (VERSION / cyrius.cyml / CHANGELOG header) didn't list it.
# Centralising the strings here means version-bump.sh writes ONE
# file every time and \`src/main.cyr\` references these vars. No
# regex hunting; no drift; no fourth-file gotcha. The cyrius
# compiler itself uses the same pattern (see cyrius's
# \`src/version_str.cyr\` + \`scripts/version-bump.sh\`).

var _VERSION_STR_CYIM = "cyim $NEW\n";
var _VERSION_LEN_CYIM = $LEN_CYIM;
EOF

if [ "$NEW" = "$OLD" ]; then
    echo "Already at $OLD (regenerated src/version_str.cyr)"
    exit 0
fi

# 2. VERSION file (source of truth). cyrius.cyml resolves
#    `${file:VERSION}` so it doesn't need its own touch.
echo "$NEW" > VERSION

# 3. CHANGELOG.md — insert new version header after [Unreleased].
#    Anchored regex matches ONLY the literal "## [Unreleased]"
#    header line, not body text quoting it (cyrius v5.8.49 lesson).
if ! grep -q "## \[$NEW\]" CHANGELOG.md 2>/dev/null; then
    sed -i "/^## \[Unreleased\]$/a\\
\\
## [$NEW] — $(date +%Y-%m-%d)" CHANGELOG.md 2>/dev/null || true
fi

echo "$OLD -> $NEW"
echo ""
echo "Updated:"
echo "  VERSION"
echo "  src/version_str.cyr (regenerated)"
echo "  CHANGELOG.md (new header inserted)"
echo ""
echo "Still manual:"
echo "  - CHANGELOG.md body (Fixed/Changed/Added sections)"
echo "  - docs/development/state.md (Last bumped, VERSION, Last release narrative)"
echo "  - Cyrius toolchain pin in cyrius.cyml [package].cyrius (separate from cyim version)"
