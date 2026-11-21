# HW2-PerfBoost — Performance Mod for *Five Nights at Freddy's: Help Wanted 2*

[![Game](https://img.shields.io/badge/Game-FNAF%3A%20Help%20Wanted%202-blueviolet)](#)
[![Engine](https://img.shields.io/badge/Engine-Unreal%20Engine%204.27-blue)](#)
[![Modes](https://img.shields.io/badge/Modes-VR%20%26%20Flat%20Mode-brightgreen)](#)
[![Platforms](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%2F%20Steam%20Deck-orange)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**HW2-PerfBoost** ist eine wissenschaftlich gebenchmarkte Performance-Mod für **Five Nights at Freddy's: Help Wanted 2** (VR & Flat Mode), die **1,58x bis 2,37x höhere FPS** liefert — bei **nahezu identischer Optik** und **100 % unverändertem Gameplay**.

Anders als klassische `Engine.ini`-Tweaks (die in *Help Wanted 2* beim Spielstart stillschweigend von Steel Wools eigenem `UVisualQualitySubsystem` überschrieben werden!) patcht **HW2-PerfBoost** gezielt die Engine-Skalierung, die `WindowsDeviceProfiles.ini` **und** die `VisualQualityOptions`-DataAssets sauber über eine einzige, leichtgewichtige `*_P.pak`-Datei (~156 KB) im `~mods`-Ordner.

---

## Gemessene Performance (4K 3840×2160, RX 7900 XT, MangoHud)

| Preset | Auflösung (Flat / VR) | `MAP_HUB_MainHub` | `MAP_BS_MakeoverRoxy` | VRAM-Ersparnis | Empfohlen für |
|---|---|---:|---:|---:|---|
| **Stock High** | 100% / 105% + 6x MSAA | `395.9 FPS` (`1.00x`) | `324.2 FPS` (`1.00x`) | Baseline | — |
| **NativeQuality** *(Empfohlen für maximale Optik)* | **100% Nativ** / 100% + 4x MSAA | **`626.3 FPS` (`1.58x`)** | **`569.8 FPS` (`1.76x`)** | **-440 bis -520 MB** | Maximale Bildtreue ohne Upscaling — bereits **>1,5x FPS!** |
| **Balanced** *(Empfohlen für Allround & VR)* | **80% Fast TAAU** / 100% + 2x MSAA | **`819.0 FPS` (`2.07x`)** | **`724.6 FPS` (`2.24x`)** | **-440 bis -600 MB** | **2x+ FPS** bei optisch kaum unterscheidbarem Bild |
| **UltraPerf** | **75% Fast TAAU** / 95% + 2x MSAA + FFR2 | **`873.5 FPS` (`2.21x`)** | **`768.0 FPS` (`2.37x`)** | **-440 bis -770 MB** | Schwächere GPUs, Steam Deck & High-Refresh-VR |

> Alle Details, 1%-Low-Werte, Frametimes und Ablation-Tests findest du in [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

---

## Was genau wird optimiert? (Keine Placebo-Tweaks!)

Eine forensische Analyse von `Thumper-WindowsNoEditor.pak` und `HW2-Win64-Shipping.exe` hat mehrere echte Engine-Bugs und Bandbreiten-Engpässe in *Help Wanted 2* aufgedeckt ([vollständige Analyse](docs/TECHNICAL_ANALYSIS.md)):

1. **Behebt Steel Wools `sg.EffectsQuality=3`-Bug**: `VisualQuality_Base_PC_High` deaktiviert `r.SSR.Quality=0`, doch unmittelbar danach aktiviert `VisualQuality_Effects_High` über `sg.EffectsQuality=3` stillschweigend wieder Full-Res **SSR**, **SSGI** und **64-bit FloatRGBA Scene Color (`r.SceneColorFormat=4`)** — doppelte Speicherbandbreite ohne sichtbaren Nutzen! (Auf Xbox Series X hat Steel Wool diesen Bug gefixt, auf PC vergessen.)
2. **Schatten-Pipeline entschlackt**: Stock Flat High rendert **10 Cascaded Shadow Maps** (`r.Shadow.CSM.MaxCascades=10`) mit 2048px und `RadiusThreshold=0.01` für kleinste Deko-Objekte in kleinen Innenräumen — plus Distance-Field-Shadows/AO. Wir reduzieren sauber auf `2–3` Cascades, 1024px Shadow Maps und `r.ShadowQuality=2` (Animatronics & Räume behalten volle, scharfe Schatten).
3. **Schnelles TAAU statt Cine-TAA (Flat) & MSAA-Fix (VR)**:
   - **Flat Mode**: Ersetzt das teure `r.PostProcessAAQuality=6` + `16` Temporal-Samples + `r.Upscale.Quality=5` durch schnelles, scharfes UE 4.27 TAA/TAAU (`r.TemporalAA.Algorithm=0`, `R11G11B10History=1`, `4` Samples) und behebt das erzwungene `r.MipMapLODBias=-1` & `r.SkeletalMeshLODBias=-1`.
   - **VR Mode**: Entfernt das doppelte 105%-Supersampling (`r.ScreenPercentage=105` + `vr.PixelDensity=1.05`), korrigiert das fehlerhafte `r.MSAACount=6` auf sauberes `2x`/`4x` MSAA und aktiviert `vr.RoundRobinOcclusion=1`, `vr.HiddenAreaMask=1` sowie subtiles `vr.VRS.HMDFixedFoveationLevel`.
4. **Translucency, Volumetric Fog & Post-Process**: Senkt das Translucency-Lighting-Volume von `64³` auf `24³–32³` (bis zu 18× weniger Voxel), optimiert Volumetric-Fog-Grid, deaktiviert überflüssiges Motion Blur, Chromatic Aberration, DoF und fixt Steel Wools Tippfehler `r.LenseFlareQuality` → `r.LensFlareQuality=0`.
5. **Draw Calls & Streaming**: Aktiviert `r.MeshDrawCommands.DynamicInstancing=1`, parallele Animation-Updates (`a.ParallelAnimEvaluation=1`, `a.URO.Enable=1`) und stabilen 3 GB Texture-Streaming-Pool statt 1 GB Thrashing.

---

## Einfache Installation

### Option 1: 1-Klick-Installer (Empfohlen)
1. Lade das neueste Release (`HW2-PerfBoost-v1.0.0.zip`) herunter und entpacke es.
2. Starte den Installer für dein System:
   - **Windows**: Doppelklick auf `install.bat`
   - **Linux / SteamOS / Steam Deck**:
     ```bash
     ./install.sh
     # Oder direkt ohne Rückfrage:
     ./install.sh --preset native    # 100% Nativ (1.58x–1.76x FPS)
     ./install.sh --preset balanced  # 80% TAAU (2.07x–2.24x FPS)
     ./install.sh --preset ultra     # 75% TAAU (2.21x–2.37x FPS)
     ```
3. Der Installer erkennt deinen Steam-Ordner für *Help Wanted 2* automatisch und kopiert genau **eine** `.pak`-Datei in `Thumper/Content/Paks/~mods/`.

### Option 2: Manuelles Drag & Drop (10 Sekunden)
1. Öffne deinen Spielordner von *Help Wanted 2*:
   - **Windows**: `...\Steam\steamapps\common\HW2\Thumper\Content\Paks\`
   - **Linux**: `~/.local/share/Steam/steamapps/common/HW2/Thumper/Content/Paks/`
2. Erstelle dort (falls nicht vorhanden) den Ordner `~mods`.
3. Kopiere **genau eine** Datei aus `presets/` in `~mods/`:
   - `HW2PerfBoost_NativeQuality_P.pak` *(100% Nativ, >1,5x FPS)*
   - `HW2PerfBoost_Balanced_P.pak` *(80% TAAU / 2x MSAA VR, >2x FPS)*
   - `HW2PerfBoost_UltraPerf_P.pak` *(Max FPS / Steam Deck)*
4. Spiel ganz normal über Steam starten (VR oder Flat Mode)!

### Deinstallation
- Über den Installer (`install.bat` → Option `4`, bzw. `./install.sh --uninstall`) **oder** einfach die `HW2PerfBoost_*_P.pak`-Datei aus `Thumper/Content/Paks/~mods/` löschen. Es werden **keine** Originaldateien des Spiels verändert!

---

## FAQ & Hinweise

- **Werden Spielstände, Achievements oder Gameplay beeinflusst?**
  Nein. Keine Maps, Blueprints, Kollisionen, Audio-Dateien oder Exe-Dateien werden angetastet. Steam Achievements und Savegames funktionieren zu 100 % normal.
- **DX11 oder DX12?**
  Unsere Benchmarks zeigen, dass der Standard-Renderer **DX11** schneller und stabiler in den 1%-Lows läuft als `-dx12`. Keine speziellen Steam-Startoptionen nötig.
- **VR & Flat Mode gleichzeitig?**
  Ja! Jede `.pak`-Datei enthält separate, optimierte Profile für `Windows_FLAT` (TAA/TAAU) und `Windows_VR` (Forward MSAA + Round-Robin Occlusion + Hidden Area Mask + Foveation).

---

## Selbst bauen (Open Source & Auditierbar)

Alle Tools zum Nachbauen der `.pak`-Dateien liegen vollständig im Ordner [`tools/`](tools/):
- `tools/ue4_pak.py` — UE4.27 Pak-v7-Builder mit SHA-1-Integritätsprüfung
- `tools/vq_patcher.py` — Byte-exakter `UVisualQualitySettingSpec` (`.uasset`/`.uexp`) Patcher
- `tools/build_mod.py` — Reproduzierbarer Mod-Builder für alle 3 Presets
- `tools/package_release.py` — Erstellt fertiges Release-ZIP + `SHA256SUMS.txt`

---

## Lizenz

Veröffentlicht unter der [MIT License](LICENSE). *Five Nights at Freddy's: Help Wanted 2* ist Eigentum von Scott Cawthon / Steel Wool Studios. Diese Mod ist ein unabhängiges Community-Projekt.
