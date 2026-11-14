#!/usr/bin/env bash
# Optional helper: creates the project's labels using the GitHub CLI.
# Requires: gh installed and authenticated (gh auth login). Run from the repo folder.
set -e
mk() { gh label create "$1" --color "$2" --description "$3" --force; }

mk "ws:case-engine"        "1d76db" "Pathways module, escalation, audit"
mk "ws:records-referrals"  "0e8a16" "Patients, screenings, referrals, tasks, notifications"
mk "ws:frontend"           "5319e7" "Dashboard, review queue, patient view"
mk "ws:data-ai"            "fbca04" "Synthetic data, risk score, assistant, evaluation"
mk "ws:docs-governance"    "c5def5" "Documents, privacy, demo and pitch"
mk "ws:platform"           "bfd4f2" "Repo setup, tests, run instructions"
mk "type:feature"          "a2eeef" "New behaviour"
mk "type:bug"              "d73a4a" "Something is broken"
mk "type:task"             "cfd3d7" "Technical or setup task"
mk "type:docs"             "0075ca" "Documentation"
mk "P0-must"               "b60205" "Required for the demo"
mk "P1-should"             "e99695" "Important, do after P0"
mk "P2-could"              "f9d0c4" "Nice to have"
mk "blocked"               "000000" "Waiting on another task"
mk "needs-review"          "fef2c0" "Ready for a teammate to review"
mk "good-first-issue"      "7057ff" "Good for getting started"
echo "Labels created."
