# Technical Notes: Help Wanted 2 Performance Bottlenecks

This is a short breakdown of what we found while digging into **Five Nights at Freddy's: Help Wanted 2** (`Thumper`, Unreal Engine 4.27, Steam AppID `2287520`) by inspecting `Thumper-WindowsNoEditor.pak` and `HW2-Win64-Shipping.exe`.

## Why normal Engine.ini tweaks barely work

Help Wanted 2 uses UE 4.27 with Forward Shading (`r.ForwardShading=True`) and `vr.InstancedStereo=True`. Instead of relying on standard `Engine.ini` settings, Steel Wool uses a custom `UVisualQualitySubsystem` that reads DataAssets from `Thumper/Content/Data/VisualQualityOptions/**`.

When the game starts or updates graphics settings, it runs the commands from those assets via console commands (`ECVF_SetByConsole`) and switches device profiles (`dp.Override = Windows_FLAT` or `Windows_VR`). Because `ECVF_SetByConsole` beats `Engine.ini`, regular config tweaks get silently overwritten on many of the settings that matter most.

## Main issues found in the stock PC presets

### 1. `sg.EffectsQuality=3` turns SSR, SSGI, and 64-bit SceneColor back on

Both `VisualQuality_Base_PC_High_FLAT` and `VisualQuality_Base_PC_High` (VR) explicitly disable SSR with `r.SSR.Quality=0`. Right after that, `VisualQuality_Effects_High` runs `sg.EffectsQuality=3`, which pulls in Unreal's `BaseScalability.ini [EffectsQuality@3]`:

```ini
r.SSR.Quality=3
r.SSR.HalfResSceneColor=0
r.SSGI.Quality=3
r.SceneColorFormat=4               ; 64-bit FloatRGBA instead of 32-bit R11G11B10F
r.TranslucencyLightingVolumeDim=64 ; 64^3 voxels instead of 24^3 or 32^3
r.SSS.HalfRes=0
r.AnisotropicMaterials=1
```

Interestingly, Steel Wool noticed this on Xbox Series X (`VisualQuality_Effects_High_XSX_FLAT`) and added `r.SSR.quality=0` at the end of that asset, but forgot to do the same on PC.

### 2. VR double-supersampling and `r.MSAACount=6`

- `VisualQuality_Resolution_High` sets both `r.ScreenPercentage=105` and `vr.PixelDensity=1.05`.
- `VisualQuality_AntiAlias_High` sets `r.MSAACount=6`, which is not a standard D3D11 power-of-two sample count and increases MSAA bandwidth cost well beyond 2x/4x.
- `vr.RoundRobinOcclusion` and `vr.VRS.HMDFixedFoveationLevel` are both left at `0`.

### 3. Heavy Flat Mode TAA setup

`VisualQuality_AntiAlias_High_FLAT` sets:

```ini
r.DefaultFeature.AntiAliasing=2
r.PostProcessAAQuality=6
r.TemporalAASamples=16
r.Upscale.Quality=5
r.TemporalAA.Upsampling=0
```

On PS5 and Xbox Series X/S (`VisualQuality_Base_PS5_FLAT` / `XSX_X`), the game already uses dynamic resolution scaling down to 77%. On PC, switching to standard fast UE 4.27 TAA/TAAU (`r.TemporalAA.Algorithm=0`, `r.PostProcessAAQuality=2`, `r.TemporalAASamples=4`, `r.TemporalAA.R11G11B10History=1`) saves a lot of GPU time while keeping edges clean.

One important lesson from testing: enabling UE 4.27's Gen5 TAA (`r.TemporalAA.Algorithm=1`) actually hurts performance badly here (around +1.5 ms GPU overhead at 4K in Forward Shading), so we keep `r.TemporalAA.Algorithm=0`.

### 4. Overkill shadow settings for indoor rooms

`VisualQuality_Shadows_High_FLAT` sets `sg.ShadowQuality=3`, which enables:

- `r.Shadow.CSM.MaxCascades=10` (for small indoor FNAF minigame rooms)
- `r.Shadow.MaxResolution=2048` and `r.Shadow.MaxCSMResolution=2048`
- `r.Shadow.RadiusThreshold=0.01` (casts dynamic shadows from tiny background clutter)
- `r.DistanceFieldShadowing=1` and `r.DistanceFieldAO=1`
- `r.ShadowQuality=5`

Dropping this to 2 or 3 cascades, 1024px shadow maps, `r.Shadow.RadiusThreshold=0.035` to `0.045`, and `r.ShadowQuality=2` cuts both GPU and draw-call load while keeping animatronic and room shadows sharp.

### 5. Forced negative LOD biases and DeviceProfile typos

- `VisualQuality_Textures_High` and `High_FLAT` set `r.MipMapLODBias=-1`, pushing textures one mip level higher than needed and adding extra bandwidth and shimmer.
- `VisualQuality_Character_High`, `Medium`, and `Low` (Flat) all set `r.SkeletalMeshLODBias=-1`, preventing skeletal LOD transitions even at a distance.
- `WindowsDeviceProfiles.ini` has a typo (`+CVars=r.LenseFlareQuality=0` instead of `r.LensFlareQuality=0`), caps `r.Streaming.PoolSize=1024` in the base profile, and sets `r.AmbientOcclusionLevels=1` even though `r.DefaultFeature.AmbientOcclusion=0`.

### 6. Draw calls and Forward Shading traps to avoid

- Enabling `r.MeshDrawCommands.DynamicInstancing=1`, `r.MeshDrawCommands.UseCachedCommands=1`, and `r.MeshDrawCommands.ParallelPassSetup=1` helps reduce CPU draw-call overhead.
- Disabling `r.SeparateTranslucency=0` in Flat Mode (it is already `0` in VR) avoids an extra full-resolution render target pass.
- We tested `r.Forward.LightGridPixelSize=64` and `r.EarlyZPass=2` and found they made performance worse in HW2's Forward Renderer, so both are intentionally left at UE4 defaults.

## How the mod applies these fixes

Everything is packed into a single uncompressed ~156 KB UE4.27 `_P.pak` file loaded from `Thumper/Content/Paks/~mods/`:

1. `Thumper/Content/Data/VisualQualityOptions/**`: patched `.uasset` and `.uexp` assets so `UVisualQualitySubsystem` applies the fixed CVars cleanly.
2. `Thumper/Config/DefaultScalability.ini`: overrides `BaseScalability.ini` tiers cleanly.
3. `Thumper/Config/Windows/WindowsDeviceProfiles.ini`: cleaned-up Windows, Flat, and VR profiles.
4. `Thumper/Config/DefaultEngine.ini`: safe renderer, shadow, instancing, streaming, and VR defaults (all gameplay, map, audio, and collision settings stay untouched).

Deleting the single `.pak` file restores the game completely to stock.
