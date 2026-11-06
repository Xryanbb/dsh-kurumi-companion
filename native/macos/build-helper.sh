#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DSH_ROOT="${DSH_DAFEIYU_ROOT:-$HOME/.dsh/profiles/web/node_modules/dsh-dafeiyu}"
ASSET_ROOT="$DSH_ROOT/assets"
APP="${DSH_DAFEIYU_DARWIN_APP:-$PROJECT_ROOT/build/dsh-dafeiyu-helper.app}"
BIN="$APP/Contents/MacOS/dsh-dafeiyu-helper"

if [[ ! -f "$ASSET_ROOT/pet-manifest.json" ]]; then
  echo "Cannot find DSH Dafeiyu assets at: $ASSET_ROOT" >&2
  echo "Set DSH_DAFEIYU_ROOT to the installed dsh-dafeiyu package directory." >&2
  exit 2
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
rm -rf "$APP"
mkdir -p "$(dirname "$BIN")" "$APP/Contents/Resources"
cp "$PROJECT_ROOT/native/macos/Info.plist" "$APP/Contents/Info.plist"
ditto --norsrc --noextattr "$ASSET_ROOT" "$APP/Contents/Resources/assets"
MODEL_ROOT="$PROJECT_ROOT/assets/kurumi3d"
MODEL_DEST="$APP/Contents/Resources/assets/kurumi3d"
# Runtime bundles contain only the textures and evaluated geometry they use,
# never historical .blend projects, review renders, or authoring scripts.
if [[ -d "$MODEL_ROOT/v2" ]]; then
  mkdir -p "$MODEL_DEST/v2"
  for texture in face.png hair.png; do
    if [[ -f "$MODEL_ROOT/v2/$texture" ]]; then
      ditto --norsrc --noextattr "$MODEL_ROOT/v2/$texture" "$MODEL_DEST/v2/$texture"
    fi
  done
fi
if [[ -d "$MODEL_ROOT/v8/runtime" ]]; then
  for asset in scene.json face.png hair-albedo.png; do
    if [[ ! -s "$MODEL_ROOT/v8/runtime/$asset" ]]; then
      echo "Incomplete Kurumi v8 runtime package: missing or empty $asset" >&2
      exit 2
    fi
  done
  mkdir -p "$MODEL_DEST/v8/runtime"
  if [[ -s "$MODEL_ROOT/v8/runtime/geometry.bin.gz" ]]; then
    gzip -dc "$MODEL_ROOT/v8/runtime/geometry.bin.gz" > "$MODEL_DEST/v8/runtime/geometry.bin"
  elif [[ -s "$MODEL_ROOT/v8/runtime/geometry.bin" ]]; then
    ditto --norsrc --noextattr "$MODEL_ROOT/v8/runtime/geometry.bin" "$MODEL_DEST/v8/runtime/geometry.bin"
  else
    echo "Missing v8 runtime geometry" >&2
    exit 2
  fi
  for asset in scene.json face.png hair-albedo.png; do
    ditto --norsrc --noextattr "$MODEL_ROOT/v8/runtime/$asset" "$MODEL_DEST/v8/runtime/$asset"
  done
fi
PACKAGE_VERSION="$(node -e 'process.stdout.write(require(process.argv[1]).version)' "$DSH_ROOT/package.json")"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $PACKAGE_VERSION" "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $PACKAGE_VERSION" "$APP/Contents/Info.plist"

SOURCES=(
  "$PROJECT_ROOT/native/macos/Sources/AnimationModel.swift"
  "$PROJECT_ROOT/native/macos/Sources/CustomSkinMotion.swift"
  "$PROJECT_ROOT/native/macos/Sources/KurumiHeadStudy.swift"
  "$PROJECT_ROOT/native/macos/Sources/Kurumi3D.swift"
  "$PROJECT_ROOT/native/macos/Sources/LayoutStore.swift"
  "$PROJECT_ROOT/native/macos/Sources/PetGeometry.swift"
  "$PROJECT_ROOT/native/macos/Sources/Permissions.swift"
  "$PROJECT_ROOT/native/macos/Sources/PetController.swift"
  "$PROJECT_ROOT/native/macos/Sources/PetView.swift"
  "$PROJECT_ROOT/native/macos/Sources/main.swift"
)
FRAMEWORKS=(
  -framework AppKit
  -framework SceneKit
  -framework CoreImage
  -framework UserNotifications
  -framework ApplicationServices
  -framework QuartzCore
)

echo "Building arm64 slice (macOS 12+)..."
swiftc -O -swift-version 5 -target arm64-apple-macosx12.0 \
  "${SOURCES[@]}" "${FRAMEWORKS[@]}" -o "$WORK/helper-arm64"
echo "Building x86_64 slice (macOS 12+)..."
swiftc -O -swift-version 5 -target x86_64-apple-macosx12.0 \
  "${SOURCES[@]}" "${FRAMEWORKS[@]}" -o "$WORK/helper-x86_64"

lipo -create "$WORK/helper-arm64" "$WORK/helper-x86_64" -output "$BIN"
chmod 0755 "$BIN"
xattr -cr "$APP"
codesign --force --deep --sign - --timestamp=none "$APP"
lipo "$BIN" -verify_arch arm64 x86_64
plutil -lint "$APP/Contents/Info.plist"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "Built universal helper: $APP"
