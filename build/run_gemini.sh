#!/bin/bash
# מריץ את 10 הבריפים דרך ג'מיני, אחד אחרי השני
S=/private/tmp/claude-501/-Users-adisomech/14c91065-01dc-4b91-8525-3aaa8381f5ac/scratchpad/articles
mkdir -p "$S"; cd ~/gemini-copy
for f in briefs/seo-*.md; do
  b=$(basename "$f" .md)
  [ -s "$S/$b.txt" ] && { echo "skip $b"; continue; }
  python3 gcopy.py "$f" > "$S/$b.txt" 2> "$S/$b.err"
  echo "$b exit=$? bytes=$(wc -c < "$S/$b.txt") $(date +%H:%M)"
done
echo ALL DONE
