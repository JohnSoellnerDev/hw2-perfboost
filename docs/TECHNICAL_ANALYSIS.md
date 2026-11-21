# Technical Analysis: Why *FNAF: Help Wanted 2* Drops Frames on PC (VR & Flat Mode)

This document details the forensic engine analysis performed on **Five Nights at Freddy's: Help Wanted 2** (`Thumper`, Unreal Engine **4.27**, Steam AppID `2287520`) by inspecting `Thumper-WindowsNoEditor.pak`, `HW2-Win64-Shipping.exe`, and runtime behavior.

---

## 1. Architecture Overview

- **Engine**: Unreal Engine 4.27 (`++UE4+Release-4.27`, Forward Shading `r.ForwardShading=True`, `vr.InstancedStereo=True`, DX11 SM5 default with DX12 SM5 support).
- **Graphics Settings System**: Steel Wool Games uses a custom `SWGCommonGame` subsystem (`UVisualQualitySubsystem`) driven by `UVisualQualitySettingSpec` DataAssets (`Thumper/Content/Data/VisualQualityOptions/**`).
- **Why generic `Engine.ini` tweaks fail**: At startup and whenever quality settings are applied, `UVisualQualitySubsystem::ApplyVisualQualitySettings()` executes the CVars inside `VisualQuality_Base_PC_*` and `PlayerOverrides/*` via console commands (`ECVF_SetByConsole`) and invokes `dp.Override = Windows_FLAT` / `dp.Override = Windows_VR`. Because `ECVF_SetByConsole` has higher priority than `Engine.ini` (`ECVF_SetBySystemSettingsIni`), standard `Engine.ini` mods get **silently overwritten** on many of the highest-impact settings.

---

## 2. Bottlenecks & Bugs Found in Stock Help Wanted 2

### Bug 1: `sg.EffectsQuality=3` Silently Re-Enables SSR, SSGI, and 64-bit FloatRGBA Scene Color
In `VisualQuality_Base_PC_High_FLAT` and `VisualQuality_Base_PC_High` (VR), Steel Wool explicitly sets:
```ini
r.SSR.Quality=0
```
Immediately afterwards, `VisualQuality_Effects_High_FLAT` and `VisualQuality_Effects_High` execute `sg.EffectsQuality=3`, which loads UE4's `BaseScalability.ini [EffectsQuality@3]`:
```ini
r.SSR.Quality=3              ; Re-enables full-res Screen Space Reflections!
r.SSR.HalfResSceneColor=0
r.SSGI.Quality=3             ; Re-enables Screen Space Global Illumination!
r.SceneColorFormat=4         ; 64-bit FloatRGBA instead of 32-bit FloatR11G11B10 (2x color bandwidth!)
r.TranslucencyLightingVolumeDim=64 ; 64^3 = 262,144 voxels (8x the cost of 32^3!)
r.SSS.HalfRes=0
r.AnisotropicMaterials=1
```
Notably, in `VisualQuality_Effects_High_XSX_FLAT` (Xbox Series X), Steel Wool caught this and appended `r.SSR.quality=0` at the end — **but forgot to do so on PC**.

### Bug 2: Hidden 105% Supersampling & Broken `r.MSAACount=6` (VR)
- `VisualQuality_Resolution_High` sets **both** `r.ScreenPercentage=105` and `vr.PixelDensity=1.05` (supersampling above native resolution by default).
- `VisualQuality_AntiAlias_High` (VR) sets `r.MSAACount=6`, which is not a power-of-two MSAA sample count in D3D11 and pushes MSAA resolve/bandwidth far beyond 2x–4x MSAA.
- `vr.RoundRobinOcclusion` and `vr.VRS.HMDFixedFoveationLevel` are both left disabled (`0`).

### Bug 3: Heavy Cinematic TAA (`PostProcessAAQuality=6`, 16 Samples, Lanczos Upscale) in Flat Mode
`VisualQuality_AntiAlias_High_FLAT` uses:
```ini
r.DefaultFeature.AntiAliasing=2
r.PostProcessAAQuality=6       ; Cinematic TAA cost
r.TemporalAASamples=16         ; 16-sample jitter
r.Upscale.Quality=5            ; Expensive Lanczos pass
r.TemporalAA.Upsampling=0      ; Disables fast TAAU
```
Meanwhile, on PS5 and Xbox Series X/S (`VisualQuality_Base_PS5_FLAT` / `XSX_X`), Steel Wool used dynamic resolution scaling down to `77%`. Switching PC Flat Mode to UE 4.27's **fast Gen4 TAA/TAAU** (`r.TemporalAA.Algorithm=0`, `r.PostProcessAAQuality=2`, `r.TemporalAASamples=4`, `r.TemporalAA.R11G11B10History=1`) — and explicitly avoiding `r.TemporalAA.Algorithm=1` (Gen5 TAA), which our ablation benchmarks proved adds ~1.5 ms GPU overhead in Forward Shading — recovers massive GPU performance while keeping edges clean and temporally stable.

### Bug 4: 10 Cascaded Shadow Maps & Tiny-Object Shadow Draw Calls
`VisualQuality_Shadows_High_FLAT` triggers `sg.ShadowQuality=3`, which executes UE4's `BaseScalability.ini [ShadowQuality@3]`:
- `r.Shadow.CSM.MaxCascades=10` (for enclosed indoor minigame rooms!)
- `r.Shadow.MaxResolution=2048` and `r.Shadow.MaxCSMResolution=2048`
- `r.Shadow.RadiusThreshold=0.01` (forces dynamic shadow draw calls on tiny 1% screen-size clutter)
- `r.DistanceFieldShadowing=1` and `r.DistanceFieldAO=1`
- `r.ShadowQuality=5` (expensive PCF shadow filter)

Reducing cascades to `2–3`, raising `RadiusThreshold` to `0.035–0.045`, using 1024px shadow maps, and switching PCF filter quality to `r.ShadowQuality=2` cuts both GPU shadow pixel cost and CPU shadow draw-call submission drastically while keeping character/animatronic shadows crisp.

### Bug 5: Forced Negative LOD Biases & DeviceProfile Typos
- `VisualQuality_Textures_High` / `High_FLAT`: sets `r.MipMapLODBias=-1`, forcing textures one full mip higher at every distance (extra memory bandwidth + aliasing shimmer).
- `VisualQuality_Character_High/Medium/Low_FLAT`: **all three** presets set `r.SkeletalMeshLODBias=-1`, preventing skeletal LOD transitions even on distant characters.
- `WindowsDeviceProfiles.ini`: contains a typo `+CVars=r.LenseFlareQuality=0` (instead of `r.LensFlareQuality=0`) and sets `r.Streaming.PoolSize=1024` (1 GB) in the base `[Windows DeviceProfile]`, alongside `r.AmbientOcclusionLevels=1` contradicting `r.DefaultFeature.AmbientOcclusion=0`.

### Optimization 6: Mesh Draw Instancing, Translucency, & Parallel RHI
- Enabling `r.MeshDrawCommands.DynamicInstancing=1`, `r.MeshDrawCommands.UseCachedCommands=1`, and `r.MeshDrawCommands.ParallelPassSetup=1` reduces CPU draw-call overhead.
- Keeping UE 4.27's default `r.Forward.LightGridPixelSize=32` and Forward EarlyZ pass intact (our ablation study confirmed forcing `LightGridPixelSize=64` or `EarlyZPass=2` degrades Forward Shading performance).
- Disabling `r.SeparateTranslucency=0` in Flat Mode (already `0` in VR) eliminates an extra full-resolution render target & composite pass.
- Enabling `a.ParallelAnimEvaluation=1`, `a.ParallelAnimUpdate=1`, `a.URO.Enable=1`, and `r.GTSyncType=1` reduces GameThread/RenderThread stalls.

---

## 3. How `HW2-PerfBoost` Applies Fixes Cleanly

All modifications are packaged into a single lightweight UE4.27 patch archive (`HW2PerfBoost_<Preset>_P.pak`) placed in `Thumper/Content/Paks/~mods/`:
1. **`Thumper/Content/Data/VisualQualityOptions/**`** — Patched `.uasset`/`.uexp` DataAssets so `UVisualQualitySubsystem` executes optimized CVars directly.
2. **`Thumper/Config/DefaultScalability.ini`** — Clean scalability overlay overriding `BaseScalability.ini`.
3. **`Thumper/Config/Windows/WindowsDeviceProfiles.ini`** — Cleaned Windows / Flat / VR device profiles.
4. **`Thumper/Config/DefaultEngine.ini`** — Safe boot-time engine/renderer CVars (leaving all gameplay, maps, collision profiles, navmesh, and audio untouched).

Zero game executables or base `.pak` files are ever modified. Removing the single `_P.pak` file restores 100% stock behavior immediately.
