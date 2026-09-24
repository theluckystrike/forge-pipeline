#!/bin/bash
set -u
D=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r
until grep -q USERS_DONE $D/fetch_users.log; do sleep 15; done
i=0
while read L; do
  O=$D/users/$L.json
  [ -s "$O" ] && continue
  for try in 1 2 3; do
    gh api "users/$L" --jq '{login, name, company, blog, email, bio, location, hireable, public_repos, followers, created_at, type}' > $O.tmp 2>$O.err
    if [ $? -eq 0 ]; then mv $O.tmp $O; rm -f $O.err; break; fi
    if grep -qE '403|429' $O.err; then sleep 60; else sleep 5; fi
  done
  i=$((i+1)); [ $((i % 10)) -eq 0 ] && sleep 2
done < $D/authors_extra_new.txt
echo USERS2_DONE
