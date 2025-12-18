#!/usr/bin/env bash
#
# verify-skill-creation.sh
#
# Verifies that skill creation only touched allowed files.
# Run BEFORE committing/pushing new skills.
#
# Usage: ./scripts/verify-skill-creation.sh <skill-name>
# Example: ./scripts/verify-skill-creation.sh google-workspace
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check argument
if [[ $# -lt 1 ]]; then
    echo -e "${RED}Usage: $0 <skill-name>${NC}"
    echo "Example: $0 google-workspace"
    exit 1
fi

SKILL_NAME="$1"
SKILL_DIR="mcps/$SKILL_NAME"
ERRORS=0
WARNINGS=0

echo "========================================"
echo "  Skill Creation Verification"
echo "  Skill: $SKILL_NAME"
echo "========================================"
echo ""

# ============================================
# PROTECTED FILES - MUST NEVER BE MODIFIED
# ============================================
PROTECTED_FILES=(
    "ARCHITECTURE.md"
    "SKILL_BLUEPRINT.md"
    "README.md"
    "HANDOFF.md"
    "WALKTHROUGH.md"
    ".env"
    ".env.example"
    ".gitignore"
)

# ============================================
# PROTECTED DIRECTORIES - MUST NEVER BE MODIFIED
# ============================================
PROTECTED_DIRS=(
    "launch"
    ".github"
    "shared"
)

# ============================================
# EXISTING SKILLS - MUST NEVER BE MODIFIED
# ============================================
EXISTING_SKILLS=(
    "mcps/git-manager"
    "mcps/disk-manager"
    "mcps/media-hub"
)

# ============================================
# Get all changed files (staged + unstaged)
# ============================================
cd "$REPO_ROOT"

echo "📋 Checking git status..."
echo ""

# Get all modified/added/deleted files
CHANGED_FILES=$(git status --porcelain | awk '{print $2}')

if [[ -z "$CHANGED_FILES" ]]; then
    echo -e "${YELLOW}⚠️  No changes detected. Nothing to verify.${NC}"
    exit 0
fi

echo "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  /'
echo ""

# ============================================
# TEST 1: Check new skill directory exists
# ============================================
echo "🔍 Test 1: Checking new skill directory..."

if [[ -d "$SKILL_DIR" ]]; then
    echo -e "  ${GREEN}✅ Directory exists: $SKILL_DIR${NC}"
else
    echo -e "  ${RED}❌ Directory NOT found: $SKILL_DIR${NC}"
    ((ERRORS++))
fi
echo ""

# ============================================
# TEST 2: Check skill has required files
# ============================================
echo "🔍 Test 2: Checking required files..."

if [[ -f "$SKILL_DIR/skill.json" ]]; then
    echo -e "  ${GREEN}✅ skill.json exists${NC}"
else
    echo -e "  ${RED}❌ Missing: skill.json${NC}"
    ((ERRORS++))
fi

if [[ -f "$SKILL_DIR/server.py" ]] || [[ -f "$SKILL_DIR/hub.py" ]]; then
    echo -e "  ${GREEN}✅ server.py or hub.py exists${NC}"
else
    echo -e "  ${RED}❌ Missing: server.py or hub.py${NC}"
    ((ERRORS++))
fi
echo ""

# ============================================
# TEST 3: Check protected files NOT modified
# ============================================
echo "🔍 Test 3: Checking protected files..."

for file in "${PROTECTED_FILES[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "^$file$"; then
        echo -e "  ${RED}❌ FORBIDDEN: $file was modified${NC}"
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✅ Protected: $file${NC}"
    fi
done
echo ""

# ============================================
# TEST 4: Check protected directories NOT modified
# ============================================
echo "🔍 Test 4: Checking protected directories..."

for dir in "${PROTECTED_DIRS[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "^$dir/"; then
        echo -e "  ${RED}❌ FORBIDDEN: Files in $dir/ were modified${NC}"
        echo "$CHANGED_FILES" | grep "^$dir/" | sed 's/^/      /'
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✅ Protected: $dir/${NC}"
    fi
done
echo ""

# ============================================
# TEST 5: Check existing skills NOT modified
# ============================================
echo "🔍 Test 5: Checking existing skills..."

for skill in "${EXISTING_SKILLS[@]}"; do
    SKILL_CHANGES=$(echo "$CHANGED_FILES" | grep "^$skill/" || true)
    if [[ -n "$SKILL_CHANGES" ]]; then
        echo -e "  ${RED}❌ FORBIDDEN: Existing skill modified: $skill${NC}"
        echo "$SKILL_CHANGES" | sed 's/^/      /'
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✅ Untouched: $skill${NC}"
    fi
done
echo ""

# ============================================
# TEST 6: Check all changes are in allowed locations
# ============================================
echo "🔍 Test 6: Verifying all changes are in allowed locations..."

while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    
    ALLOWED=false
    
    # Allowed: New skill directory
    if [[ "$file" == "$SKILL_DIR"* ]]; then
        ALLOWED=true
    fi
    
    # Allowed: Agent definitions (adding skill to agent)
    if [[ "$file" == agents/*.json ]]; then
        ALLOWED=true
    fi
    
    # Allowed: Scripts directory (for this verification script itself)
    if [[ "$file" == scripts/* ]]; then
        ALLOWED=true
    fi
    
    # Allowed: SKILL_BLUEPRINT.md updates (only by human, flagged as warning)
    if [[ "$file" == "SKILL_BLUEPRINT.md" ]]; then
        ALLOWED=false  # Already caught in Test 3
    fi
    
    if [[ "$ALLOWED" == true ]]; then
        echo -e "  ${GREEN}✅ Allowed: $file${NC}"
    else
        # Check if it's in the known lists (already reported)
        ALREADY_REPORTED=false
        for pf in "${PROTECTED_FILES[@]}"; do
            [[ "$file" == "$pf" ]] && ALREADY_REPORTED=true
        done
        for pd in "${PROTECTED_DIRS[@]}"; do
            [[ "$file" == "$pd"* ]] && ALREADY_REPORTED=true
        done
        for es in "${EXISTING_SKILLS[@]}"; do
            [[ "$file" == "$es"* ]] && ALREADY_REPORTED=true
        done
        
        if [[ "$ALREADY_REPORTED" == false ]]; then
            echo -e "  ${RED}❌ UNEXPECTED: $file${NC}"
            ((ERRORS++))
        fi
    fi
done <<< "$CHANGED_FILES"
echo ""

# ============================================
# TEST 7: Validate skill.json structure
# ============================================
echo "🔍 Test 7: Validating skill.json..."

if [[ -f "$SKILL_DIR/skill.json" ]]; then
    # Check it's valid JSON
    if python3 -c "import json; json.load(open('$SKILL_DIR/skill.json'))" 2>/dev/null; then
        echo -e "  ${GREEN}✅ Valid JSON${NC}"
        
        # Check required fields
        HAS_NAME=$(python3 -c "import json; d=json.load(open('$SKILL_DIR/skill.json')); print('yes' if 'name' in d else 'no')")
        HAS_DESC=$(python3 -c "import json; d=json.load(open('$SKILL_DIR/skill.json')); print('yes' if 'description' in d else 'no')")
        HAS_CMD=$(python3 -c "import json; d=json.load(open('$SKILL_DIR/skill.json')); print('yes' if 'command' in d else 'no')")
        
        [[ "$HAS_NAME" == "yes" ]] && echo -e "  ${GREEN}✅ Has 'name' field${NC}" || { echo -e "  ${RED}❌ Missing 'name' field${NC}"; ((ERRORS++)); }
        [[ "$HAS_DESC" == "yes" ]] && echo -e "  ${GREEN}✅ Has 'description' field${NC}" || { echo -e "  ${RED}❌ Missing 'description' field${NC}"; ((ERRORS++)); }
        [[ "$HAS_CMD" == "yes" ]] && echo -e "  ${GREEN}✅ Has 'command' field${NC}" || { echo -e "  ${RED}❌ Missing 'command' field${NC}"; ((ERRORS++)); }
    else
        echo -e "  ${RED}❌ Invalid JSON in skill.json${NC}"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}⚠️  Skipped (skill.json not found)${NC}"
fi
echo ""

# ============================================
# TEST 8: Check server.py syntax
# ============================================
echo "🔍 Test 8: Checking Python syntax..."

if [[ -f "$SKILL_DIR/server.py" ]]; then
    if python3 -m py_compile "$SKILL_DIR/server.py" 2>/dev/null; then
        echo -e "  ${GREEN}✅ server.py syntax OK${NC}"
    else
        echo -e "  ${RED}❌ server.py has syntax errors${NC}"
        python3 -m py_compile "$SKILL_DIR/server.py" 2>&1 | sed 's/^/      /'
        ((ERRORS++))
    fi
elif [[ -f "$SKILL_DIR/hub.py" ]]; then
    if python3 -m py_compile "$SKILL_DIR/hub.py" 2>/dev/null; then
        echo -e "  ${GREEN}✅ hub.py syntax OK${NC}"
    else
        echo -e "  ${RED}❌ hub.py has syntax errors${NC}"
        python3 -m py_compile "$SKILL_DIR/hub.py" 2>&1 | sed 's/^/      /'
        ((ERRORS++))
    fi
fi
echo ""

# ============================================
# SUMMARY
# ============================================
echo "========================================"
echo "  VERIFICATION SUMMARY"
echo "========================================"

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}"
    echo "  ✅ ALL TESTS PASSED"
    echo ""
    echo "  Safe to commit and push!"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "  ❌ VERIFICATION FAILED"
    echo ""
    echo "  $ERRORS error(s) found."
    echo "  DO NOT PUSH until all errors are fixed."
    echo -e "${NC}"
    exit 1
fi
