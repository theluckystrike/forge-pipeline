#!/bin/bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124 Safari/537.36"
for s in webpack babel eslint prettier vuejs vitejs astro withastro nuxt svelte solid storybook mocha jest rollup biome tailwindcss mastodon homebrew curl ghost matrix matrixdotorg lichess jellyfin godotengine blender bevy deno ladybird servo zig ziglang rust-foundation; do
  for kind in json page exp; do
    case $kind in json) p="https://opencollective.com/$s.json";; page) p="https://opencollective.com/$s";; exp) p="https://opencollective.com/$s/expenses";; esac
    out=$(curl -sL -m 60 -A "$UA" -o "wb_${s}_$kind.out" -w "%{http_code} %{url_effective}" "https://web.archive.org/web/2026id_/$p")
    echo "$s $kind $out"
  done
done
