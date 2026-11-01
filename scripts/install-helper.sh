#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DSH_ROOT="${DSH_DAFEIYU_ROOT:-$HOME/.dsh/profiles/web/node_modules/dsh-dafeiyu}"
SOURCE_APP="${1:-$PROJECT_ROOT/build/dsh-dafeiyu-helper.app}"
TARGET_APP="$DSH_ROOT/runtime/bin/darwin/dsh-dafeiyu-helper.app"
BACKUP_ROOT="${DSH_DAFEIYU_BACKUP_ROOT:-$HOME/.dsh/dsh-dafeiyu/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"
BACKUP_APP="$BACKUP_ROOT/kurumi-helper-$STAMP.app"
STAGED_APP="$TARGET_APP.next-$STAMP"

if [[ ! -d "$SOURCE_APP" ]]; then
  echo "Built helper not found: $SOURCE_APP" >&2
  echo "Run native/macos/build-helper.sh first." >&2
  exit 2
fi
if [[ ! -d "$DSH_ROOT" ]]; then
  echo "Installed dsh-dafeiyu package not found: $DSH_ROOT" >&2
  exit 2
fi

mkdir -p "$(dirname "$TARGET_APP")" "$BACKUP_ROOT"
ditto --norsrc --noextattr "$SOURCE_APP" "$STAGED_APP"
codesign --verify --deep --strict "$STAGED_APP"
lipo "$STAGED_APP/Contents/MacOS/dsh-dafeiyu-helper" -verify_arch arm64 x86_64
BACKUP_NOTE="none (there was no existing Helper)"
if [[ -e "$TARGET_APP" ]]; then
  mv "$TARGET_APP" "$BACKUP_APP"
  BACKUP_NOTE="$BACKUP_APP"
fi
if ! mv "$STAGED_APP" "$TARGET_APP"; then
  if [[ -d "$BACKUP_APP" ]]; then
    mv "$BACKUP_APP" "$TARGET_APP"
  fi
  echo "Could not install the new Helper; restored the previous bundle when available." >&2
  exit 1
fi
codesign --verify --deep --strict "$TARGET_APP"
lipo "$TARGET_APP/Contents/MacOS/dsh-dafeiyu-helper" -verify_arch arm64 x86_64
printf 'Installed helper: %s\nBackup: %s\n' "$TARGET_APP" "$BACKUP_NOTE"
