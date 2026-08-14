#!/usr/bin/env bash
# Sync AgentKits Marketing to Cursor (.cursor/skills/, .cursor/rules/agents/)
# Usage: ./scripts/sync-to-cursor.sh [--dry-run] [--skip-agents]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MKT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$MKT_ROOT/../.." && pwd)"
CURSOR_SKILLS="$REPO_ROOT/.cursor/skills"
CURSOR_AGENTS="$REPO_ROOT/.cursor/rules/agents"
DRY_RUN=false
SKIP_AGENTS=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --skip-agents) SKIP_AGENTS=true ;;
  esac
done

log() { echo "[mkt-sync-to-cursor] $*" >&2; }

# AgentKits source files use CRLF — normalize before parsing
strip_crlf() { tr -d '\r'; }

extract_body_after_frontmatter() {
  strip_crlf < "$1" | awk 'BEGIN{skip=1} /^---$/{if(++fm==2){skip=0; next}} !skip'
}

# PM skills that must NOT be overwritten — AgentKits gets mkt- prefix always
PM_PROTECTED=("marketing-ideas" "pricing-strategy")

skill_dest_name() {
  local rel="$1"
  if [[ "$rel" == document-skills/* ]]; then
    echo "mkt-doc-$(basename "$rel")"
  else
    echo "mkt-$(basename "$rel")"
  fi
}

rewrite_paths() {
  sed -E \
    -e 's|\.claude/skills/document-skills/([a-z0-9-]+)/SKILL\.md|.cursor/skills/mkt-doc-\1/SKILL.md|g' \
    -e 's|\.claude/skills/([a-z0-9-]+)/SKILL\.md|.cursor/skills/mkt-\1/SKILL.md|g' \
    -e 's|Load `([a-z0-9-]+)` skill|Read `.cursor/skills/mkt-\1/SKILL.md`|g' \
    -e 's|Activate `([a-z0-9-]+)` skill|Read `.cursor/skills/mkt-\1/SKILL.md`|g' \
    -e 's|Activate `([a-z0-9-]+)`, `([a-z0-9-]+)` skills|Read `.cursor/skills/mkt-\1/SKILL.md` and `.cursor/skills/mkt-\2/SKILL.md`|g' \
    -e 's|Activate `([a-z0-9-]+)`, `([a-z0-9-]+)`, `([a-z0-9-]+)` skills|Read `.cursor/skills/mkt-\1/SKILL.md`, `.cursor/skills/mkt-\2/SKILL.md`, `.cursor/skills/mkt-\3/SKILL.md`|g' \
    -e 's|skills/([a-z0-9-]+)/SKILL\.md|.cursor/skills/mkt-\1/SKILL.md|g' \
    -e 's|`\./docs/brand-guidelines\.md`|`docs/marketing/brand-context.md`|g' \
    -e 's|\./docs/brand-guidelines\.md|docs/marketing/brand-context.md|g' \
    -e 's|\./plans/campaigns/|docs/marketing/campaigns/|g' \
    -e 's|\./plans/|docs/marketing/plans/|g' \
    -e 's|\./research/|docs/marketing/research/|g' \
    -e 's|\./content/|docs/marketing/content/|g' \
    -e 's|Delegate to `([a-z0-9-]+)` agent|Follow persona @.cursor/rules/agents/mkt-\1.md|g' \
    -e 's|delegate to `([a-z0-9-]+)` agent|follow persona @.cursor/rules/agents/mkt-\1.md|g' \
    -e 's|/([a-z]+):([a-z0-9-]+)|mkt-workflow-\1-\2|g' \
    -e 's|/report:\*|mkt-workflow-report-*|g' \
    -e 's|/content:\*|mkt-workflow-content-*|g' \
    -e 's|Apply the \*\*([a-z0-9-]+)\*\* skill|Read `.cursor/skills/mkt-\1/SKILL.md`|g' \
    -e 's|Apply \*\*([a-z0-9-]+)\*\* skill|Read `.cursor/skills/mkt-\1/SKILL.md`|g' \
    -e 's|\*\*([a-z0-9-]+)\*\* skill|skill `mkt-\1` (see `.cursor/skills/mkt-\1/SKILL.md`)|g'
}

update_skill_frontmatter() {
  local dest_name="$1"
  awk -v name="$dest_name" '
    BEGIN { in_fm=0; fm_done=0 }
    /^---$/ {
      if (!fm_done) { in_fm++; if (in_fm == 1) { print; next } }
      if (in_fm == 2) { fm_done=1; print; next }
    }
    in_fm == 1 && /^name:/ { print "name: " name; next }
    { print }
  '
}

copy_skill_dir() {
  local skill_dir="$1"
  local rel="${skill_dir#$MKT_ROOT/skills/}"
  local dest_name
  dest_name="$(skill_dest_name "$rel")"
  local dest="$CURSOR_SKILLS/$dest_name"

  if $DRY_RUN; then
    log "would copy skill dir: $rel -> $dest_name"
    return
  fi

  rm -rf "$dest"
  mkdir -p "$dest"

  if [[ -d "$skill_dir/references" ]]; then
    cp -r "$skill_dir/references" "$dest/"
  fi
  if [[ -d "$skill_dir/data" ]]; then
    cp -r "$skill_dir/data" "$dest/"
  fi

  update_skill_frontmatter "$dest_name" < <(strip_crlf < "$skill_dir/SKILL.md") \
    | rewrite_paths > "$dest/SKILL.md"

  log "skill: $dest_name"
}

convert_command() {
  local cmd_file="$1"
  local category
  category="$(basename "$(dirname "$cmd_file")")"
  local cmd_name
  cmd_name="$(basename "$cmd_file" .md)"
  local workflow_name="mkt-workflow-${category}-${cmd_name}"
  local dest="$CURSOR_SKILLS/$workflow_name"

  if $DRY_RUN; then
    log "would convert command: $category/$cmd_name -> $workflow_name"
    return
  fi

  local description
  description="$(grep -m1 '^description:' "$cmd_file" | sed 's/^description: *//' | tr -d '"\r')"

  mkdir -p "$dest"

  {
    echo "---"
    echo "name: $workflow_name"
    echo "description: \"${description}. Marketing workflow for Cursor (AgentKits). Use when the user asks for /${category}:${cmd_name} or a full ${category} ${cmd_name} workflow.\""
    echo "disable-model-invocation: true"
    echo "---"
    echo ""
    echo "# Marketing Workflow: ${category}/${cmd_name}"
    echo ""
    echo "> Cursor adaptation of AgentKits \`/${category}:${cmd_name}\`. Invoke explicitly:"
    echo "> «Следуй skill $workflow_name» или \`@.cursor/skills/$workflow_name/SKILL.md\`"
    echo ""
    echo "## Cursor notes"
    echo ""
    echo "- Slash commands (\`/${category}:${cmd_name}\`) недоступны — используй этот workflow skill."
    echo "- Atomic skills: \`.cursor/skills/mkt-*/SKILL.md\` (префикс \`mkt-\`, не путать с PM skills)."
    echo "- Personas: \`.cursor/rules/agents/mkt-*.md\`"
    echo "- Контекст проекта: \`docs/marketing/brand-context.md\`, \`docs/strategy/seo-strategy.md\`"
    echo "- Сохраняй артефакты в \`docs/marketing/\` (campaigns/, research/, content/, plans/)"
    echo "- MCP-метрики: если нет интеграции — пиши NOT AVAILABLE, не выдумывай цифры"
    echo ""
    echo "---"
    echo ""
    extract_body_after_frontmatter "$cmd_file" | rewrite_paths
  } > "$dest/SKILL.md"

  log "workflow: $workflow_name"
}

copy_agent() {
  local agent_file="$1"
  local agent_name
  agent_name="$(basename "$agent_file" .md)"
  local dest="$CURSOR_AGENTS/mkt-${agent_name}.md"

  if $DRY_RUN; then
    log "would copy agent: $agent_name -> mkt-${agent_name}"
    return
  fi

  {
    echo "---"
    echo "name: mkt-${agent_name}"
    grep -m1 '^description:' "$agent_file" | sed 's/^description: /description: /' | strip_crlf || true
    echo "---"
    echo ""
    echo "> Marketing persona (AgentKits). Invoke: «Review по @.cursor/rules/agents/mkt-${agent_name}.md»"
    echo ""
    echo "## Cursor context (chim_web)"
    echo ""
    echo "1. \`AGENTS.md\` — контекст monorepo"
    echo "2. \`docs/marketing/brand-context.md\` — продукт, аудитория, каналы"
    echo "3. \`docs/strategy/seo-strategy.md\` — SEO-стратегия"
    echo "4. \`frontend/app/(marketing)/\` — текущие landing pages"
    echo ""
    echo "---"
    echo ""
    extract_body_after_frontmatter "$agent_file" | rewrite_paths
  } > "$dest"

  log "agent: mkt-${agent_name}"
}

main() {
  log "Marketing root: $MKT_ROOT"
  log "Cursor skills: $CURSOR_SKILLS"
  log "Cursor agents: $CURSOR_AGENTS"

  if ! $DRY_RUN; then
    mkdir -p "$CURSOR_SKILLS" "$CURSOR_AGENTS"
  fi

  local skill_count=0
  local workflow_count=0
  local agent_count=0

  # Atomic skills (top-level + document-skills)
  while IFS= read -r skill_dir; do
    copy_skill_dir "$skill_dir"
    skill_count=$((skill_count + 1))
  done < <(find "$MKT_ROOT/skills" -name 'SKILL.md' -printf '%h\n' | sort -u)

  # Operational commands only (English, no training-*)
  while IFS= read -r cmd_file; do
    convert_command "$cmd_file"
    workflow_count=$((workflow_count + 1))
  done < <(find "$MKT_ROOT/commands" -mindepth 2 -maxdepth 2 -name '*.md' \
    ! -path '*/training/*' \
    ! -path '*/training-*/*' \
    | sort)

  if ! $SKIP_AGENTS; then
    while IFS= read -r agent_file; do
      copy_agent "$agent_file"
      agent_count=$((agent_count + 1))
    done < <(find "$MKT_ROOT/agents" -maxdepth 1 -name '*.md' | sort)
  fi

  log "done: $skill_count atomic skills, $workflow_count workflows, $agent_count agents"
}

main
