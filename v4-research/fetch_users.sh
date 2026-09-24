#!/bin/bash
# Step 2b: for each repo, unique issue authors (order of appearance, newest issues first), cap 60, type User only; gh api users/{login}
set -u
D=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r
for F in $D/issues/*.json; do
  jq -r '[.items[] | select(.user_type=="User") | .login] | unique_by(.) | .[]' $F
done | sort -u > $D/authors_all.txt
# per-repo cap 60 in order of appearance
for F in $D/issues/*.json; do
  jq -r '[.items[] | select(.user_type=="User") | .login] | reduce .[] as $l ([]; if index($l) then . else . + [$l] end) | .[:60] | .[]' $F
done | sort -u > $D/authors_sampled.txt
echo "authors sampled: $(wc -l < $D/authors_sampled.txt)"
i=0
while read L; do
  O=$D/users/$L.json
  [ -s "$O" ] && continue
  for try in 1 2 3; do
    gh api "users/$L" --jq '{login, name, company, blog, email, bio, location, hireable, public_repos, followers, created_at, type}' > $O.tmp 2>$O.err
    rc=$?
    if [ $rc -eq 0 ]; then mv $O.tmp $O; rm -f $O.err; break; fi
    if grep -qE '403|429' $O.err; then echo "backoff $L"; sleep 60; else sleep 5; fi
  done
  i=$((i+1))
  if [ $((i % 10)) -eq 0 ]; then sleep 2; echo "done $i"; fi
done < $D/authors_sampled.txt
echo USERS_DONE
