#!/usr/bin/env bash
# Sync PM Skills Marketplace to Cursor (.cursor/skills/)
# Usage: ./scripts/sync-to-cursor.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PM_ROOT/../.." && pwd)"
CURSOR_SKILLS="$REPO_ROOT/.cursor/skills"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

log() { echo "[sync-to-cursor] $*" >&2; }

copy_skill() {
  local src="$1"
  local name
  name="$(basename "$(dirname "$src")")"
  local dest="$CURSOR_SKILLS/$name"

  if $DRY_RUN; then
    log "would copy skill: $name"
    return
  fi

  mkdir -p "$dest"
  cp "$src" "$dest/SKILL.md"
  log "skill: $name"
}

convert_command() {
  local cmd_file="$1"
  local cmd_name
  cmd_name="$(basename "$cmd_file" .md)"
  local workflow_name="pm-workflow-${cmd_name}"
  local dest="$CURSOR_SKILLS/$workflow_name"

  if $DRY_RUN; then
    log "would convert command: $cmd_name -> $workflow_name"
    return
  fi

  local description
  description="$(grep -m1 '^description:' "$cmd_file" | sed 's/^description: *//' | tr -d '"')"

  mkdir -p "$dest"

  {
    echo "---"
    echo "name: $workflow_name"
    echo "description: \"${description}. End-to-end PM workflow for Cursor (chains multiple pm skills). Use when the user asks for /$cmd_name or a full $cmd_name workflow.\""
    echo "disable-model-invocation: true"
    echo "---"
    echo ""
    echo "# PM Workflow: $cmd_name"
    echo ""
    echo "> Cursor adaptation of Claude Code \`/$cmd_name\`. Invoke explicitly:"
    echo "> «Следуй skill $workflow_name» или \`@.cursor/skills/$workflow_name/SKILL.md\`"
    echo ""
    echo "## Cursor notes"
    echo ""
    echo "- Slash commands (\`/$cmd_name\`) недоступны — используй этот workflow skill."
    echo "- Шаги со ссылкой на **skill-name** → прочитай \`.cursor/skills/<skill-name>/SKILL.md\` и следуй ему."
    echo "- Сохраняй артефакты в \`docs/pm/\` или корень workspace, если пользователь не указал путь."
    echo "- После завершения предложи следующий workflow из секции «Next steps» исходной команды."
    echo ""
    echo "---"
    echo ""
    # Strip Claude command frontmatter; keep body from first heading
    awk 'BEGIN{skip=1} /^---$/{if(++fm==2){skip=0; next}} !skip' "$cmd_file" \
      | sed 's|`/\([a-z0-9-]*\)`|skill `pm-workflow-\1` or atomic pm skill|g' \
      | sed -E 's|[Aa]pply the \*\*([a-z0-9-]+)\*\* skill|Read and follow `.cursor/skills/\1/SKILL.md`|g' \
      | sed -E 's|[Aa]pply \*\*([a-z0-9-]+)\*\* skill|Read and follow `.cursor/skills/\1/SKILL.md`|g' \
      | sed -E 's|[Aa]pply the \*\*([a-z0-9-]+)\*\* or \*\*([a-z0-9-]+)\*\* skill|Read `.cursor/skills/\1/SKILL.md` or `.cursor/skills/\2/SKILL.md`|g' \
      | sed -E 's|[Ff]or each selected idea, apply the \*\*([a-z0-9-]+)\*\* or \*\*([a-z0-9-]+)\*\* skill|For each selected idea, read `.cursor/skills/\1/SKILL.md` or `.cursor/skills/\2/SKILL.md`|g' \
      | sed -E 's|\*\*([a-z0-9-]+)\*\* skill|skill `\1` (see `.cursor/skills/\1/SKILL.md`)|g'
  } > "$dest/SKILL.md"

  log "workflow: $workflow_name"
}

main() {
  log "PM root: $PM_ROOT"
  log "Cursor skills: $CURSOR_SKILLS"

  if ! $DRY_RUN; then
    mkdir -p "$CURSOR_SKILLS"
  fi

  local skill_count=0
  local workflow_count=0

  while IFS= read -r skill_file; do
    copy_skill "$skill_file"
    skill_count=$((skill_count + 1))
  done < <(find "$PM_ROOT" -path '*/skills/*/SKILL.md' | sort)

  while IFS= read -r cmd_file; do
    convert_command "$cmd_file"
    workflow_count=$((workflow_count + 1))
  done < <(find "$PM_ROOT" -path '*/commands/*.md' | sort)

  log "done: $skill_count atomic skills, $workflow_count workflow skills"
}

main
