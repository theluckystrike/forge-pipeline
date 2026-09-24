#!/bin/bash
set -u
D=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r
mkdir -p $D/issues
REPOS="medusajs/medusa strapi/strapi n8n-io/n8n directus/directus payloadcms/payload supabase/supabase RocketChat/Rocket.Chat mattermost/mattermost appwrite/appwrite calcom/cal.com langgenius/dify Infisical/infisical hoppscotch/hoppscotch ToolJet/ToolJet baptisteArno/typebot.io twentyhq/twenty formbricks/formbricks documenso/documenso saleor/saleor vendure-ecommerce/vendure"
for R in $REPOS; do
  F=$D/issues/$(echo $R | tr '/' '_').json
  for try in 1 2 3; do
    gh api "search/issues?q=repo:$R+is:issue+is:open&sort=created&order=desc&per_page=100" \
      --jq '{total:.total_count, items:[.items[] | select(.pull_request == null) | {repo:"'"$R"'", number, html_url, title, created_at, updated_at, author_association, comments, login:.user.login, user_type:.user.type, labels:[.labels[].name], body:(.body // "")}]}' > $F && break
    echo "retry $R"; sleep 20
  done
  echo "$R total_open=$(jq .total $F) sampled=$(jq '.items|length' $F)"
  sleep 3
done
echo DONE
