#!/usr/bin/env bash
# ==============================================================================
# HW2-PerfBoost Installer for Linux / SteamOS / Steam Deck
# Five Nights at Freddy's: Help Wanted 2 Performance Mod
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESETS_DIR="$SCRIPT_DIR/presets"
MOD_PREFIX="HW2PerfBoost_"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

find_hw2_dir() {
  local candidates=(
    "$HOME/.local/share/Steam/steamapps/common/HW2"
    "$HOME/.steam/steam/steamapps/common/HW2"
    "$HOME/.steam/debian-installation/steamapps/common/HW2"
    "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/HW2"
  )
  # Also parse Steam libraryfolders.vdf if present
  local vdfs=(
    "$HOME/.local/share/Steam/steamapps/libraryfolders.vdf"
    "$HOME/.steam/steam/steamapps/libraryfolders.vdf"
    "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf"
  )
  for vdf in "${vdfs[@]}"; do
    if [[ -f "$vdf" ]]; then
      while IFS= read -r libpath; do
        candidates+=("$libpath/steamapps/common/HW2")
      done < <(grep -oE '"path"[[:space:]]+"[^"]+"' "$vdf" | sed -E 's/"path"[[:space:]]+"([^"]+)"/\1/')
    fi
  done

  for dir in "${candidates[@]}"; do
    if [[ -d "$dir/Thumper/Content/Paks" ]]; then
      echo "$dir"
      return 0
    fi
  done
  return 1
}

usage() {
  cat << EOF
Usage: ./install.sh [OPTIONS]

Options:
  --preset <balanced|native|ultra>   Install a specific preset non-interactively
  --game-dir <path>                  Path to HW2 installation folder
  --uninstall                        Remove all HW2-PerfBoost mod files
  -h, --help                         Show this help message
EOF
}

PRESET=""
GAME_DIR=""
UNINSTALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preset)    PRESET="${2:-}"; shift 2 ;;
    --game-dir)  GAME_DIR="${2:-}"; shift 2 ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *)           echo -e "${RED}Unknown option: $1${NC}"; usage; exit 1 ;;
  esac
done

echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}   FNAF: Help Wanted 2 — HW2-PerfBoost Installer (Linux)${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

if [[ -z "$GAME_DIR" ]]; then
  if GAME_DIR="$(find_hw2_dir)"; then
    echo -e "${GREEN}[OK]${NC} Found Help Wanted 2 at: ${BOLD}$GAME_DIR${NC}"
  else
    echo -e "${YELLOW}[!]${NC} Could not auto-detect Help Wanted 2."
    read -rp "Enter path to your HW2 folder (containing HW2.exe): " GAME_DIR
  fi
fi

PAKS_DIR="$GAME_DIR/Thumper/Content/Paks"
MODS_DIR="$PAKS_DIR/~mods"

if [[ ! -d "$PAKS_DIR" ]]; then
  echo -e "${RED}[ERROR]${NC} Invalid HW2 directory: $PAKS_DIR not found."
  exit 1
fi

if [[ "$UNINSTALL" -eq 1 ]]; then
  rm -f "$MODS_DIR/${MOD_PREFIX}"*.pak
  echo -e "${GREEN}[OK]${NC} HW2-PerfBoost uninstalled cleanly. Game restored to stock!"
  exit 0
fi

if [[ -z "$PRESET" ]]; then
  echo ""
  echo "Choose a preset to install:"
  echo "  1) NativeQuality (Recommended - Max Visuals) — 1.58x-1.76x FPS at 100% NATIVE resolution (zero upscaling!)"
  echo "  2) Balanced      (Recommended - High FPS/VR) — 2.07x-2.24x FPS (80% Fast TAAU Flat / 2x MSAA VR)"
  echo "  3) UltraPerf                                 — 2.21x-2.37x FPS (75% Fast TAAU / Steam Deck / Low-End GPU)"
  echo "  4) Uninstall                                 — Remove HW2-PerfBoost and restore stock"
  echo ""
  read -rp "Selection [1-4, default=1]: " CHOICE
  case "${CHOICE:-1}" in
    1) PRESET="native" ;;
    2) PRESET="balanced" ;;
    3) PRESET="ultra" ;;
    4)
      rm -f "$MODS_DIR/${MOD_PREFIX}"*.pak
      echo -e "${GREEN}[OK]${NC} HW2-PerfBoost uninstalled cleanly."
      exit 0
      ;;
    *) echo -e "${RED}Invalid selection.${NC}"; exit 1 ;;
  esac
fi

case "$PRESET" in
  balanced) PAK_FILE="HW2PerfBoost_Balanced_P.pak" ;;
  native)   PAK_FILE="HW2PerfBoost_NativeQuality_P.pak" ;;
  ultra)    PAK_FILE="HW2PerfBoost_UltraPerf_P.pak" ;;
  *)        echo -e "${RED}Unknown preset: $PRESET (use balanced, native, or ultra)${NC}"; exit 1 ;;
esac

if [[ ! -f "$PRESETS_DIR/$PAK_FILE" ]]; then
  echo -e "${RED}[ERROR]${NC} Preset file not found: $PRESETS_DIR/$PAK_FILE"
  exit 1
fi

mkdir -p "$MODS_DIR"
# Remove any previously installed HW2-PerfBoost preset to avoid conflicts
rm -f "$MODS_DIR/${MOD_PREFIX}"*.pak
cp "$PRESETS_DIR/$PAK_FILE" "$MODS_DIR/$PAK_FILE"

echo ""
echo -e "${GREEN}${BOLD}[SUCCESS]${NC} Installed ${BOLD}$PAK_FILE${NC} to:"
echo "  $MODS_DIR/$PAK_FILE"
echo ""
echo "Launch Help Wanted 2 normally via Steam (VR or Flat Mode)."
echo "To uninstall anytime, run: ./install.sh --uninstall"
