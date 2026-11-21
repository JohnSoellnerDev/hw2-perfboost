# HW2-PerfBoost (Five Nights at Freddy's: Help Wanted 2)

Eine Performance-Mod für **Five Nights at Freddy's: Help Wanted 2** (VR und Flat Mode). Ziel der Mod ist es, deutlich mehr FPS herauszuholen, ohne das Spiel hässlich zu machen oder irgendetwas am Gameplay zu verändern.

Normale `Engine.ini`-Tweaks bringen bei Help Wanted 2 leider meistens kaum etwas, weil das Spiel beim Start über das eigene `UVisualQualitySubsystem` viele Grafik-CVars direkt wieder überschreibt. **HW2-PerfBoost** setzt deshalb direkt als kleine `.pak`-Datei (~156 KB) im `~mods`-Ordner an und passt die `VisualQualityOptions`, die Skalierungs-Tabellen und die `WindowsDeviceProfiles.ini` sauber an.

## Performance-Vergleich

Getestet in 4K (3840x2160) auf einer RX 7900 XT (DX11/DXVK, VSync aus, gemessen mit MangoHud):

| Preset | Auflösung (Flat / VR) | `MAP_HUB_MainHub` | `MAP_BS_MakeoverRoxy` | VRAM | Gedacht für |
|---|---|---:|---:|---:|---|
| **Stock High** | 100% / 105% + 6x MSAA | `395.9 FPS` (`1.00x`) | `324.2 FPS` (`1.00x`) | 6.50 bis 6.68 GB | Standard-Einstellung |
| **NativeQuality** | **100% Nativ** / 100% + 4x MSAA | **`626.3 FPS` (`1.58x`)** | **`569.8 FPS` (`1.76x`)** | ca. 450 bis 520 MB weniger | Maximale Bildschärfe ohne Upscaling |
| **Balanced** | **80% TAAU** / 100% + 2x MSAA | **`819.0 FPS` (`2.07x`)** | **`724.6 FPS` (`2.24x`)** | ca. 450 bis 600 MB weniger | Beste Mischung für hohe FPS und VR |
| **UltraPerf** | **75% TAAU** / 95% + 2x MSAA + FFR2 | **`873.5 FPS` (`2.21x`)** | **`768.0 FPS` (`2.37x`)** | ca. 450 bis 770 MB weniger | Schwächere GPUs, Steam Deck, 120Hz+ VR |

Mehr Details zu den Tests und wie genau gemessen wurde stehen in [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

## Was ändert die Mod eigentlich?

Beim Durchschauen der Spieldateien (`Thumper-WindowsNoEditor.pak`) sind ein paar ziemlich unnötige Performance-Fresser und Bugs in den PC-Presets von Steel Wool aufgefallen (alle Details in [docs/TECHNICAL_ANALYSIS.md](docs/TECHNICAL_ANALYSIS.md)):

- **Der `sg.EffectsQuality=3`-Bug:** In den PC-High-Presets schaltet das Spiel zwar `r.SSR.Quality=0` aus, ruft direkt danach aber `sg.EffectsQuality=3` auf. Dadurch gehen Full-Res SSR, SSGI und 64-Bit-SceneColor (`r.SceneColorFormat=4`, doppelte Speicherbandbreite) im Hintergrund einfach wieder an. Auf der Xbox Series X wurde das von den Entwicklern gefixt, am PC aber vergessen.
- **Überdimensionierte Schatten:** Im Flat Mode rendert High 10 Shadow Cascades (`r.Shadow.CSM.MaxCascades=10`) mit 2048px und `RadiusThreshold=0.01`, obwohl die meisten Minigames in kleinen Innenräumen spielen. Mit 2 bis 3 Cascades, 1024px Shadow Maps und `r.ShadowQuality=2` sehen die Schatten praktisch gleich aus, kosten aber deutlich weniger Leistung.
- **Anti-Aliasing und LOD-Bugs (Flat):** Das Spiel nutzt im Flat Mode teures Cine-TAA (`r.PostProcessAAQuality=6`, 16 Samples, Lanczos) und zwingt Texturen und Charaktere über `r.MipMapLODBias=-1` und `r.SkeletalMeshLODBias=-1` dauerhaft auf das höchste Detaillevel. Die Mod wechselt auf schnelles UE4-TAA/TAAU (`r.TemporalAA.Algorithm=0`, 4 Samples, 32-Bit-History) und normalisiert die LOD-Biases.
- **VR-Fixes:** VR High setzt gleichzeitig `r.ScreenPercentage=105` und `vr.PixelDensity=1.05` (doppeltes Supersampling) sowie das ungerade `r.MSAACount=6`. Die Mod korrigiert das auf sauberes 100% + 2x/4x MSAA und aktiviert `vr.RoundRobinOcclusion=1`, `vr.HiddenAreaMask=1` und leichtes Fixed Foveated Rendering (wo unterstützt).
- **Kleinkram & Streaming:** Reduziert das `64³`-Translucency-Volume auf `24³`/`32³`, korrigiert den Tippfehler `r.LenseFlareQuality` in der `WindowsDeviceProfiles.ini`, hebt den Texture-Streaming-Pool von 1 GB auf 3 GB an und aktiviert `r.MeshDrawCommands.DynamicInstancing=1`.

## Installation

### Variante 1: Installer nutzen (am einfachsten)

1. Lade die aktuelle `HW2-PerfBoost-v1.0.0.zip` aus den [Releases](https://github.com/JohnSoellnerDev/hw2-perfboost/releases) herunter und entpacke sie.
2. Starte das passende Skript:
   - **Windows:** Doppelklick auf `install.bat`
   - **Linux / SteamOS / Steam Deck:**
     ```bash
     ./install.sh
     ```
     Oder direkt per Parameter:
     ```bash
     ./install.sh --preset native    # 100% Nativ (1.58x - 1.76x FPS)
     ./install.sh --preset balanced  # 80% TAAU / 2x MSAA VR (2.07x - 2.24x FPS)
     ./install.sh --preset ultra     # Max FPS / Steam Deck (2.21x - 2.37x FPS)
     ```
3. Der Installer findet deinen Help Wanted 2 Steam-Ordner automatisch und legt die gewählte `.pak`-Datei ab.

### Variante 2: Manuell kopieren

1. Geh in deinen Spielordner:
   - **Windows:** `...\Steam\steamapps\common\HW2\Thumper\Content\Paks\`
   - **Linux:** `~/.local/share/Steam/steamapps/common/HW2/Thumper/Content/Paks/`
2. Erstelle dort den Ordner `~mods` (falls es ihn noch nicht gibt).
3. Kopiere **eine** Datei aus `presets/` hinein:
   - `HW2PerfBoost_NativeQuality_P.pak`
   - `HW2PerfBoost_Balanced_P.pak`
   - `HW2PerfBoost_UltraPerf_P.pak`
4. Spiel ganz normal über Steam starten.

### Deinstallieren

Entweder im Installer die Option zum Deinstallieren wählen (`./install.sh --uninstall` unter Linux, bzw. Option `4` in `install.bat`) oder einfach die `HW2PerfBoost_*.pak`-Datei aus `Thumper/Content/Paks/~mods/` löschen. Originaldateien werden nicht verändert.

## Häufige Fragen

**Gehen Spielstände oder Steam-Achievements kaputt?**  
Nein. Die Mod fasst weder Spielstände noch Maps, Blueprints, Kollisionen oder die `.exe` an. Alles verhält sich genau wie im Originalspiel.

**Sollte ich mit `-dx12` starten?**  
In unseren Tests lief der Standard-DX11-Modus schneller und hatte bessere 1%-Lows als DX12. Du brauchst also keine speziellen Startoptionen.

**Warum sehe ich nach der Installation immer noch genau z. B. 144 oder 240 FPS?**  
Standardmäßig ist VSync aktiv und begrenzt die FPS auf die Hz-Zahl deines Monitors. Wenn deine Grafikkarte vorher schon das Limit erreicht hat, merkst du es im Flat Mode vor allem an niedrigerer GPU-Auslastung und weniger Stromverbrauch (oder wenn du VSync zum Testen ausschaltest). Richtig deutlich wird der FPS-Sprung vor allem in VR, in 4K oder auf schwächerer Hardware.

**Funktioniert die Mod gleichzeitig für VR und Flat Mode?**  
Ja. In jeder `.pak`-Datei sind getrennte Profile für `Windows_FLAT` und `Windows_VR` hinterlegt, das Spiel wählt automatisch das richtige.

## Selbst bauen

Alle Skripte zum Nachbauen der `.pak`-Dateien liegen offen im Ordner [`tools/`](tools/):

- `tools/ue4_pak.py`: baut UE4.27 Pak-v7-Dateien inkl. SHA-1-Hashes
- `tools/vq_patcher.py`: liest und patcht `UVisualQualitySettingSpec`-Assets (`.uasset` / `.uexp`)
- `tools/build_mod.py`: generiert alle drei Presets
- `tools/package_release.py`: packt die Release-ZIP und erstellt `SHA256SUMS.txt`

## Lizenz

[MIT License](LICENSE). *Five Nights at Freddy's: Help Wanted 2* gehört Scott Cawthon / Steel Wool Studios. Das hier ist eine unabhängige Community-Mod.
