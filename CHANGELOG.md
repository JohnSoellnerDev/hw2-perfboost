# Changelog

## [1.0.0] - 2026-11-21

### Added
- Three ready-to-install UE4.27 `_P.pak` presets for *Five Nights at Freddy's: Help Wanted 2* (VR and Flat Mode):
  - `HW2PerfBoost_NativeQuality_P.pak`: 100% native resolution (no upscaling), 1.58x to 1.76x FPS from engine, shadow, bandwidth, and VisualQuality bugfixes.
  - `HW2PerfBoost_Balanced_P.pak`: 2.07x to 2.24x FPS (80% Fast TAAU in Flat Mode, 2x MSAA + VR occlusion & FFR1 in VR) with almost identical visuals.
  - `HW2PerfBoost_UltraPerf_P.pak`: 2.21x to 2.37x FPS for weaker GPUs, Steam Deck, and high-refresh VR headsets.
- Direct patching of `VisualQualityOptions` DataAssets so `UVisualQualitySubsystem` no longer overwrites performance fixes on startup.
- Install scripts for Windows (`install.bat`) and Linux / SteamOS / Steam Deck (`install.sh`) with automatic Steam folder detection and clean uninstall.
- Open-source build tools (`tools/build_mod.py`, `tools/ue4_pak.py`, `tools/vq_patcher.py`, `tools/package_release.py`).
- Technical breakdown (`docs/TECHNICAL_ANALYSIS.md`) and MangoHud benchmark notes (`docs/BENCHMARKS.md`).
