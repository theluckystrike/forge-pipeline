#!/bin/bash
# Step 2a: pull 100 most recent open issues per repo (PRs filtered), save raw JSON
set -u
D=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r
mkdir -p $D/issues $D/contrib
REPOS="medusajs/medusa strapi/strapi n8n-io/n8n directus/directus payloadcms/payload supabase/supabase RocketChat/Rocket.Chat mattermost/mattermost appwrite/appwrite calcom/cal.com langgenius/dify Infisical/infisical hoppscotch/hoppscotch ToolJet/ToolJet baptisteArno/typebot.io twentyhq/twenty formbricks/formbricks documenso/documenso saleor/saleor vendure-ecommerce/vendure"
for R in $REPOS; do
  F=$D/issues/$(echo $R | tr '/' '_').json
  # per_page=100 sorted by created desc; PRs have pull_request key -> drop
  gh api "repos/$R/issues?state=open&per_page=100&sort=created&direction=desc" \
    --jq '[.[] | select(.pull_request == null) | {repo:"'"$R"'", number, html_url, title, created_at, updated_at, author_association, comments, login:.user.login, user_type:.user.type, labels:[.labels[].name], body:(.body // "")}]' > $F
  echo "$R $(jq length $F)"
  # CONTRIBUTING.md (step 5)
  C=$D/contrib/$(echo $R | tr '/' '_').md
  gh api "repos/$R/contents/CONTRIBUTING.md" --jq '.content' 2>/dev/null | base64 -d > $C 2>/dev/null
  if [ ! -s $C ]; then gh api "repos/$R/contents/.github/CONTRIBUTING.md" --jq '.content' 2>/dev/null | base64 -d > $C 2>/dev/null; fi
  if [ ! -s $C ]; then gh api "repos/$R/contents/docs/CONTRIBUTING.md" --jq '.content' 2>/dev/null | base64 -d > $C 2>/dev/null; fi
  sleep 2
done
echo ISSUES_DONE
