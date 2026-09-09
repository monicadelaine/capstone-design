#!/usr/bin/env bash
set -euo pipefail

# Standard CS 495 GitHub setup.
# Safe to rerun: labels, Project, fields, and views are reused when found.

if [[ -z "${REPO:-}" ]]; then
    REPO="GauravS11112003/Capstone-Design-Manager-Fall-2026-"
fi
if [[ -z "$REPO" ]]; then
  echo "ERROR: Run from a GitHub repository or set REPO=owner/repository."
  exit 1
fi

OWNER="${REPO%%/*}"
PROJECT_TITLE="${PROJECT_TITLE:-Senior Design Project}"

gh auth status >/dev/null

# Project commands require the classic OAuth token used by gh to include the `project` scope.
# Test access up front so students get a useful repair command instead of failing halfway through.
if ! gh project list --owner "$OWNER" --limit 1 >/dev/null 2>&1; then
  echo
  echo "ERROR: GitHub CLI does not currently have permission to use Projects for '$OWNER'."
  echo "Run:"
  echo
  echo "  gh auth refresh -s project"
  echo
  echo "Then verify with:"
  echo
  echo "  gh auth status"
  echo
  echo "and rerun this script."
  exit 1
fi

create_label() {
  local name="$1" color="$2" description="$3"
  gh label create "$name" -R "$REPO" --color "$color" --description "$description" --force >/dev/null
  echo "LABEL: $name"
}

echo "Creating/updating standard labels..."
create_label "type:feature" "1D76DB" "User- or sponsor-facing product functionality"
create_label "type:bug" "D73A4A" "Defect or unexpected behavior"
create_label "type:investigation" "8250DF" "Timeboxed technical investigation / spike"
create_label "type:test" "0E8A16" "Testing, test automation, or quality verification"
create_label "type:documentation" "0075CA" "Durable project documentation"
create_label "type:security" "B60205" "Security analysis, remediation, or controls"
create_label "type:deployment" "5319E7" "Hosting, deployment, infrastructure, CI/CD, or operations"
create_label "type:setup" "BFDADC" "Repository, tooling, README, CI, or project setup"
create_label "stand-up" "FBCA04" "Formal team stand-up meeting"

echo
echo "Creating/reusing GitHub Project..."
PROJECT_NUMBER="$(
  gh project list --owner "$OWNER" --format json \
    --jq ".projects[]? | select(.title == \"$PROJECT_TITLE\") | .number" | head -n 1
)"
if [[ -z "$PROJECT_NUMBER" ]]; then
  PROJECT_NUMBER="$(gh project create --owner "$OWNER" --title "$PROJECT_TITLE" \
    --format json --jq '.number')"
  echo "CREATED Project #$PROJECT_NUMBER: $PROJECT_TITLE"
else
  echo "EXISTS Project #$PROJECT_NUMBER: $PROJECT_TITLE"
fi

gh project link "$PROJECT_NUMBER" --owner "$OWNER" --repo "$REPO" >/dev/null 2>&1 || true

ensure_field() {
  local name="$1" type="$2" options="${3:-}"
  local found
  found="$(
    gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --limit 100 --format json \
      --jq ".fields[]? | select(.name == \"$name\") | .id" | head -n 1
  )"
  if [[ -n "$found" ]]; then
    echo "EXISTS field: $name"
    return
  fi
  if [[ "$type" == "SINGLE_SELECT" ]]; then
    gh project field-create "$PROJECT_NUMBER" --owner "$OWNER" --name "$name" \
      --data-type SINGLE_SELECT --single-select-options "$options" >/dev/null
  else
    gh project field-create "$PROJECT_NUMBER" --owner "$OWNER" --name "$name" \
      --data-type "$type" >/dev/null
  fi
  echo "CREATED field: $name"
}

echo
echo "Creating/reusing Project fields..."
ensure_field "Priority" "SINGLE_SELECT" "P1,P2,P3"
ensure_field "Iteration" "SINGLE_SELECT" "Iteration 1,Iteration 2,Iteration 3"
ensure_field "Work Type" "SINGLE_SELECT" "Feature,Bug,Investigation,Test,Documentation,Security,Deployment,Setup"
ensure_field "Estimate" "NUMBER"
ensure_field "Risk" "SINGLE_SELECT" "Low,Medium,High"
ensure_field "Planned" "SINGLE_SELECT" "Planned,Added During Iteration"
ensure_field "Evidence Ready" "SINGLE_SELECT" "Yes,No"

PROJECT_ID="$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq '.id')"

# Determine whether the project owner is a personal account or an organization.
OWNER_ACCOUNT_TYPE="$(gh api "users/$OWNER" --jq '.type')"
if [[ "$OWNER_ACCOUNT_TYPE" == "Organization" ]]; then
  OWNER_TYPE="org"
else
  OWNER_TYPE="user"
fi

PROJECT_ID="$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq '.id')"

# Confirm the REST representation of the project before attempting view creation.
if [[ "$OWNER_TYPE" == "org" ]]; then
  if ! gh api "orgs/$OWNER/projectsV2/$PROJECT_NUMBER" \
      -H "X-GitHub-Api-Version: 2026-03-10" >/dev/null 2>&1; then
    echo "WARNING: The GitHub REST API could not resolve organization Project #$PROJECT_NUMBER."
  fi
else
  if ! gh api "users/$OWNER/projectsV2/$PROJECT_NUMBER" \
      -H "X-GitHub-Api-Version: 2026-03-10" >/dev/null 2>&1; then
    echo "WARNING: The GitHub REST API could not resolve user Project #$PROJECT_NUMBER for $OWNER."
  fi
fi

view_exists() {
  local name="$1"
  gh api graphql \
    -f query='query($id:ID!){node(id:$id){... on ProjectV2{views(first:100){nodes{name}}}}}' \
    -f id="$PROJECT_ID" \
    --jq ".data.node.views.nodes[]? | select(.name == \"$name\") | .name" 2>/dev/null | head -n 1
}

post_view() {
  local endpoint="$1"
  local name="$2"
  local layout="$3"
  local filter="$4"
  local response_file="$5"

  gh api --method POST "$endpoint" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    -f name="$name" \
    -f layout="$layout" \
    -f filter="$filter" >"$response_file" 2>&1
}

create_view() {
  local name="$1"
  local layout="$2"
  local filter="$3"
  local existing response_file endpoint USER_NUMERIC_ID USER_NODE_ID

  existing="$(view_exists "$name" || true)"
  if [[ -n "$existing" ]]; then
    echo "EXISTS view: $name"
    return 0
  fi

  echo "Creating view: $name"
  response_file="$(mktemp)"

  if [[ "$OWNER_TYPE" == "org" ]]; then
    endpoint="orgs/$OWNER/projectsV2/$PROJECT_NUMBER/views"
    if post_view "$endpoint" "$name" "$layout" "$filter" "$response_file"; then
      echo "CREATED view: $name"
      rm -f "$response_file"
      return 0
    fi
  else
    # GitHub's current Project Views documentation names this path parameter `user_id`,
    # while other user-owned Project endpoints use the username. In practice, accounts
    # may resolve one form but not another, so try the supported identifiers without
    # creating duplicates.
    #
    # 1) username/login
    endpoint="users/$OWNER/projectsV2/$PROJECT_NUMBER/views"
    if post_view "$endpoint" "$name" "$layout" "$filter" "$response_file"; then
      echo "CREATED view: $name"
      rm -f "$response_file"
      return 0
    fi

    # 2) numeric REST user id
    USER_NUMERIC_ID="$(gh api "users/$OWNER" --jq '.id')"
    endpoint="users/$USER_NUMERIC_ID/projectsV2/$PROJECT_NUMBER/views"
    if post_view "$endpoint" "$name" "$layout" "$filter" "$response_file"; then
      echo "CREATED view: $name"
      rm -f "$response_file"
      return 0
    fi

    # 3) GraphQL node id, in case GitHub interprets "unique identifier" as node id.
    USER_NODE_ID="$(gh api "users/$OWNER" --jq '.node_id')"
    endpoint="users/$USER_NODE_ID/projectsV2/$PROJECT_NUMBER/views"
    if post_view "$endpoint" "$name" "$layout" "$filter" "$response_file"; then
      echo "CREATED view: $name"
      rm -f "$response_file"
      return 0
    fi
  fi

  echo "FAILED view: $name"
  echo "  GitHub did not accept automatic saved-view creation for this account/project."
  echo "  Last GitHub response:"
  sed 's/^/    /' "$response_file"
  echo
  echo "  Create this view manually in the Project UI:"
  echo "    Name:   $name"
  echo "    Layout: $layout"
  echo "    Filter: $filter"
  rm -f "$response_file"
  return 0
}

echo
echo "Creating/reusing submission views..."
create_view "01 - Product Backlog" "table" 'is:issue -label:"stand-up"'
create_view "02 - Iteration 1 Plan" "table" 'iteration:"Iteration 1"'
create_view "03 - Iteration 2 Plan" "table" 'iteration:"Iteration 2"'
create_view "04 - Iteration 3 Plan" "table" 'iteration:"Iteration 3"'
create_view "05 - Iteration 1 Results" "table" 'iteration:"Iteration 1"'
create_view "06 - Iteration 2 Results" "table" 'iteration:"Iteration 2"'
create_view "07 - Iteration 3 Results" "table" 'iteration:"Iteration 3"'
create_view "08 - Team Contributions" "table" 'is:issue -label:"stand-up"'
create_view "09 - Engineering & Quality Work" "table" 'is:issue -label:"type:feature" -label:"stand-up"'
create_view "10 - Decisions & Investigations" "table" 'label:"type:investigation"'
create_view "11 - Remaining Backlog" "table" '-status:Done -label:"stand-up"'

echo
echo "View setup notes:"
echo "  • Plan and Results views intentionally use the same iteration filter."
echo "    The LMS snapshots preserve the planning-time vs. deadline-time state."
echo "  • In the Project UI, group 'Team Contributions' by Assignee if useful."
echo "  • Customize visible columns (Priority, Status, Iteration, Work Type, Estimate, Risk,"
echo "    Planned, Evidence Ready) in the UI."
echo
echo
echo "Setup complete."
echo "Open the Project in GitHub and customize visible fields/grouping as needed."
