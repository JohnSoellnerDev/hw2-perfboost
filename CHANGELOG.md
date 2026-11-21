# Changelog

All notable changes to **HW2-PerfBoost** will be documented in this file.

## [1.0.0] - 2026-11-21

### Added
- **Three ready-to-install UE4.27 `_P.pak` presets** for *Five Nights at Freddy's: Help Wanted 2* (VR & Flat Mode):
  - `HW2PerfBoost_NativeQuality_P.pak` (Recommended — Maximum Visual Fidelity): Keeps **100% native resolution** (zero upscaling) while delivering **1.58x–1.76x FPS** via pure engine, shadow, bandwidth, and Steel Wool CVar bugfixes.
  - `HW2PerfBoost_Balanced_P.pak` (Recommended — High FPS & VR): Delivers **2.07x–2.24x FPS** (80% Fast TAAU in Flat Mode, 2x MSAA + VR Round-Robin Occlusion + FFR1 in VR) with near-identical visual fidelity.
  - `HW2PerfBoost_UltraPerf_P.pak`: Maximum FPS preset (**2.21x–2.37x FPS**) for mid/low-end GPUs, Steam Deck, and high-refresh VR headsets.
- **Direct `VisualQualityOptions` DataAsset patching**: Prevents `UVisualQualitySubsystem` from overwriting `Engine.ini` tweaks at runtime.
- **One-click installers** for both Windows (`install.bat`) and Linux / SteamOS / Steam Deck (`install.sh`) with automatic Steam library detection and clean one-step uninstallation.
- **Full open-source reproducible build pipeline** (`tools/build_mod.py`, `tools/ue4_pak.py`, `tools/vq_patcher.py`).
- **Forensic technical analysis** (`docs/TECHNICAL_ANALYSIS.md`) and **verified benchmark results** (`docs/BENCHMARKS.md`).
