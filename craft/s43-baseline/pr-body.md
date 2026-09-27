The readme links for the Baseline Marketplace, the Style Settings Migration Tool, the Open in Obsidian badge, and the Cupertino repo all point at aaaaalexis.github.io and github.com/aaaaalexis. Those now return 404 because that pages site and account are gone. Closes #258.

Every link was pointing at the same content that lives on the live pages site under this repo. This change swaps the four URLs to the svnaxis paths and the moved Cupertino repo. I verified each replacement target returns 200, including /marketplace/, /migration/, /install?name=Baseline, and the repo redirect.

Verified against the live site with curl before opening this. Repro for the broken state is in #258.
