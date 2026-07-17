#!/bin/bash

set -e

OUTPUT="tilawah_source_bundle.txt"

echo "Mulai membuat bundle..."
> "$OUTPUT"

FILES=(
  "main/endpoint/tilawah/tilawah_views.py"
  "main/models_tilawah.py"
  "main/models.py"
  "main/serializers/tilawah_serializers.py"
  "main/serializers/__init__.py"
  "main/utils_tilawah/quran_data.py"
  "main/utils_tilawah/tajwid_classifier.py"
  "main/utils_tilawah/tajwid_engine.py"
  "main/utils_tilawah/whisper_engine.py"
  "main/utils_tilawah/word_matcher.py"
  "main/utils_tilawah/feedback_builder.py"
  "main/pagination_utils.py"
  "main/urls.py"
  "main/admin.py"
)

for file in "${FILES[@]}"; do
  echo "Memproses: $file"

  if [ -f "$file" ]; then
    {
      printf "\n\n"
      printf "================================================================================\n"
      printf "FILE: %s\n" "$file"
      printf "================================================================================\n\n"
      cat "$file"
    } >> "$OUTPUT"
  else
    {
      printf "\n\n"
      printf "================================================================================\n"
      printf "FILE NOT FOUND: %s\n" "$file"
      printf "================================================================================\n"
    } >> "$OUTPUT"
  fi
done

if [ -f "requirements.txt" ]; then
  echo "Memproses: requirements.txt"

  {
    printf "\n\n"
    printf "================================================================================\n"
    printf "FILE: requirements.txt\n"
    printf "================================================================================\n\n"
    cat requirements.txt
  } >> "$OUTPUT"
else
  echo "requirements.txt tidak ditemukan, dilewati."
fi

echo ""
echo "Selesai membuat: $OUTPUT"
echo "Ukuran file:"
ls -lh "$OUTPUT"
