#!/bin/bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124 Safari/537.36"
for s in eslint prettier vite astrodotbuild nuxt svelte solid storybook mochajs rollup biome tailwindcss mastodon homebrew curl godotengine jellyfin servo; do
  for kind in page exp; do
    case $kind in page) p="https://opencollective.com/$s";; exp) p="https://opencollective.com/$s/expenses";; esac
    for try in 1 2; do
      out=$(curl -sL -m 90 -A "$UA" -o "wb2_${s}_$kind.out" -w "%{http_code} %{url_effective}" "https://web.archive.org/web/2026id_/$p")
      echo "$s $kind try$try $out"
      case "$out" in 200*|404*) break;; esac
      sleep 5
    done
    sleep 2
  done
done
echo DONE
