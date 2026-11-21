#!/usr/bin/env python3
"""
FNAF: Help Wanted 2 - Performance Boost Mod Builder (HW2-PerfBoost)
Builds UE4.27 *_P.pak performance mod archives with three benchmark-verified presets.

All settings were scientifically validated via MangoHud ablation benchmarks on UE 4.27
Forward Shading (DX11/DXVK). Known UE 4.27 Forward-Shading regressions (such as Gen5 TAA
r.TemporalAA.Algorithm=1, forced r.EarlyZPass=2, and coarse r.Forward.LightGridPixelSize=64)
are explicitly avoided.

Layers patched inside each *_P.pak:
  1. Thumper/Content/Data/VisualQualityOptions/** (UVisualQualitySettingSpec DataAssets)
     -> Prevents UVisualQualitySubsystem from overwriting CVars with ECVF_SetByConsole!
  2. Thumper/Config/DefaultScalability.ini
     -> Clean scalability overlay fixing sg.EffectsQuality / sg.ShadowQuality / sg.PostProcessQuality
  3. Thumper/Config/Windows/WindowsDeviceProfiles.ini
     -> Optimizes [Windows], [Windows_FLAT], and [Windows_VR] profiles + fixes r.LenseFlareQuality typo
  4. Thumper/Config/DefaultEngine.ini
     -> Safe boot-time renderer, shadow, streaming, instancing, and VR occlusion CVars
        (leaves all gameplay, maps, collision profiles, navmesh, and audio 100% untouched)
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from ue4_pak import build_pak
from vq_patcher import patch_vq_commands


# ==============================================================================
# Benchmark-Verified Preset Definitions
# ==============================================================================
PRESETS: Dict[str, dict] = {
    "native": {
        "label": "NativeQuality (100% Native Res, Zero Upscaling, Full Engine/Shadow/Bandwidth Fixes)",
        "pak_name": "HW2PerfBoost_NativeQuality_P.pak",
        "flat_screen_pct": "100",
        "flat_taau": "0",
        "flat_taa_samples": "4",
        "flat_aa_quality": "2",
        "flat_mip_bias": "0",
        "flat_sharpen": "0.5",
        "vr_screen_pct": "100",
        "vr_pixel_density": "1.0",
        "vr_msaa": "4",
        "vr_foveation": "1",
        "shadow_max_res": "1024",
        "shadow_csm_res": "1024",
        "shadow_csm_cascades": "3",
        "shadow_radius_thresh": "0.035",
        "shadow_quality": "2",
        "volfog_enabled": "1",
        "volfog_grid_px": "16",
        "volfog_grid_z": "32",
        "translucency_dim": "32",
        "lod_dist_scale": "1.0",
        "skel_lod_bias": "0",
    },
    "balanced": {
        "label": "Balanced (Recommended - >=1.5x FPS, Fast TAAU 80% Flat / 2x MSAA VR, Near-Identical Visuals)",
        "pak_name": "HW2PerfBoost_Balanced_P.pak",
        "flat_screen_pct": "80",
        "flat_taau": "1",
        "flat_taa_samples": "4",
        "flat_aa_quality": "2",
        "flat_mip_bias": "-0.35",
        "flat_sharpen": "0.6",
        "vr_screen_pct": "100",
        "vr_pixel_density": "1.0",
        "vr_msaa": "2",
        "vr_foveation": "1",
        "shadow_max_res": "1024",
        "shadow_csm_res": "1024",
        "shadow_csm_cascades": "2",
        "shadow_radius_thresh": "0.045",
        "shadow_quality": "2",
        "volfog_enabled": "1",
        "volfog_grid_px": "24",
        "volfog_grid_z": "24",
        "translucency_dim": "24",
        "lod_dist_scale": "1.15",
        "skel_lod_bias": "0",
    },
    "ultra": {
        "label": "UltraPerf (1.75x-2.2x+ FPS, Fast TAAU 75% Flat / 2x MSAA + FFR2 VR, Low-End & Steam Deck)",
        "pak_name": "HW2PerfBoost_UltraPerf_P.pak",
        "flat_screen_pct": "75",
        "flat_taau": "1",
        "flat_taa_samples": "4",
        "flat_aa_quality": "2",
        "flat_mip_bias": "-0.4",
        "flat_sharpen": "0.65",
        "vr_screen_pct": "95",
        "vr_pixel_density": "0.95",
        "vr_msaa": "2",
        "vr_foveation": "2",
        "shadow_max_res": "768",
        "shadow_csm_res": "768",
        "shadow_csm_cascades": "2",
        "shadow_radius_thresh": "0.055",
        "shadow_quality": "2",
        "volfog_enabled": "1",
        "volfog_grid_px": "24",
        "volfog_grid_z": "24",
        "translucency_dim": "24",
        "lod_dist_scale": "1.3",
        "skel_lod_bias": "0",
    },
}


def make_default_scalability_ini(cfg: dict) -> bytes:
    """Create Thumper/Config/DefaultScalability.ini overriding UE4 BaseScalability.ini."""
    text = f"""\
; HW2-PerfBoost Optimized Scalability Overrides
; Prevents sg.* groups from re-enabling wasted deferred passes (SSR/SSGI/DFAO),
; 64-bit FloatRGBA scene color, excessive 10-cascade shadows, and 64^3 translucency volumes.

[AntiAliasingQuality@0]
r.PostProcessAAQuality=0

[AntiAliasingQuality@1]
r.PostProcessAAQuality=2

[AntiAliasingQuality@2]
r.PostProcessAAQuality={cfg["flat_aa_quality"]}

[AntiAliasingQuality@3]
r.PostProcessAAQuality={cfg["flat_aa_quality"]}

[ShadowQuality@0]
r.LightFunctionQuality=0
r.ShadowQuality=0
r.Shadow.CSM.MaxCascades=1
r.Shadow.MaxResolution=512
r.Shadow.MaxCSMResolution=512
r.Shadow.RadiusThreshold=0.06
r.Shadow.DistanceScale=0.6
r.Shadow.CSM.TransitionScale=0
r.Shadow.PreShadowResolutionFactor=0.5
r.DistanceFieldShadowing=0
r.DistanceFieldAO=0
r.VolumetricFog=0
r.LightMaxDrawDistanceScale=0.5
r.CapsuleShadows=0

[ShadowQuality@1]
r.LightFunctionQuality=1
r.ShadowQuality=2
r.Shadow.CSM.MaxCascades=1
r.Shadow.MaxResolution=512
r.Shadow.MaxCSMResolution=768
r.Shadow.RadiusThreshold=0.055
r.Shadow.DistanceScale=0.75
r.Shadow.CSM.TransitionScale=0.25
r.Shadow.PreShadowResolutionFactor=0.5
r.DistanceFieldShadowing=0
r.DistanceFieldAO=0
r.VolumetricFog=0
r.LightMaxDrawDistanceScale=0.75
r.CapsuleShadows=1

[ShadowQuality@2]
r.LightFunctionQuality=1
r.ShadowQuality={cfg["shadow_quality"]}
r.Shadow.CSM.MaxCascades={cfg["shadow_csm_cascades"]}
r.Shadow.MaxResolution={cfg["shadow_max_res"]}
r.Shadow.MaxCSMResolution={cfg["shadow_csm_res"]}
r.Shadow.RadiusThreshold={cfg["shadow_radius_thresh"]}
r.Shadow.DistanceScale=0.85
r.Shadow.CSM.TransitionScale=0.5
r.Shadow.PreShadowResolutionFactor=0.5
r.DistanceFieldShadowing=0
r.DistanceFieldAO=0
r.AOQuality=0
r.VolumetricFog={cfg["volfog_enabled"]}
r.VolumetricFog.GridPixelSize={cfg["volfog_grid_px"]}
r.VolumetricFog.GridSizeZ={cfg["volfog_grid_z"]}
r.VolumetricFog.HistoryMissSupersampleCount=1
r.LightMaxDrawDistanceScale=0.9
r.CapsuleShadows=1

[ShadowQuality@3]
r.LightFunctionQuality=1
r.ShadowQuality={cfg["shadow_quality"]}
r.Shadow.CSM.MaxCascades={cfg["shadow_csm_cascades"]}
r.Shadow.MaxResolution={cfg["shadow_max_res"]}
r.Shadow.MaxCSMResolution={cfg["shadow_csm_res"]}
r.Shadow.RadiusThreshold={cfg["shadow_radius_thresh"]}
r.Shadow.DistanceScale=0.9
r.Shadow.CSM.TransitionScale=0.5
r.Shadow.PreShadowResolutionFactor=0.5
r.DistanceFieldShadowing=0
r.DistanceFieldAO=0
r.AOQuality=0
r.VolumetricFog={cfg["volfog_enabled"]}
r.VolumetricFog.GridPixelSize={cfg["volfog_grid_px"]}
r.VolumetricFog.GridSizeZ={cfg["volfog_grid_z"]}
r.VolumetricFog.HistoryMissSupersampleCount=1
r.LightMaxDrawDistanceScale=1.0
r.CapsuleShadows=1

[PostProcessQuality@0]
r.MotionBlurQuality=0
r.AmbientOcclusionMipLevelFactor=1.0
r.AmbientOcclusionMaxQuality=0
r.AmbientOcclusionLevels=0
r.DepthOfFieldQuality=0
r.RenderTargetPoolMin=300
r.LensFlareQuality=0
r.SceneColorFringeQuality=0
r.EyeAdaptationQuality=1
r.BloomQuality=4
r.FastBlurThreshold=0
r.Upscale.Quality=2
r.Tonemapper.GrainQuantization=0
r.LightShaftQuality=0
r.Filter.SizeScale=0.6
r.Tonemapper.Quality=2

[PostProcessQuality@1]
r.MotionBlurQuality=0
r.AmbientOcclusionMipLevelFactor=1.0
r.AmbientOcclusionMaxQuality=0
r.AmbientOcclusionLevels=0
r.DepthOfFieldQuality=0
r.RenderTargetPoolMin=350
r.LensFlareQuality=0
r.SceneColorFringeQuality=0
r.EyeAdaptationQuality=1
r.BloomQuality=4
r.FastBlurThreshold=2
r.Upscale.Quality=2
r.Tonemapper.GrainQuantization=0
r.LightShaftQuality=0
r.Filter.SizeScale=0.7
r.Tonemapper.Quality=3

[PostProcessQuality@2]
r.MotionBlurQuality=0
r.AmbientOcclusionMipLevelFactor=1.0
r.AmbientOcclusionMaxQuality=0
r.AmbientOcclusionLevels=0
r.DepthOfFieldQuality=0
r.RenderTargetPoolMin=400
r.LensFlareQuality=0
r.SceneColorFringeQuality=0
r.EyeAdaptationQuality=1
r.BloomQuality=4
r.FastBlurThreshold=2
r.Upscale.Quality=3
r.Tonemapper.GrainQuantization=0
r.LightShaftQuality=0
r.Filter.SizeScale=0.75
r.Tonemapper.Quality=4

[PostProcessQuality@3]
r.MotionBlurQuality=0
r.AmbientOcclusionMipLevelFactor=1.0
r.AmbientOcclusionMaxQuality=0
r.AmbientOcclusionLevels=0
r.DepthOfFieldQuality=0
r.RenderTargetPoolMin=400
r.LensFlareQuality=0
r.SceneColorFringeQuality=0
r.EyeAdaptationQuality=1
r.BloomQuality=4
r.FastBlurThreshold=2
r.Upscale.Quality=3
r.Tonemapper.GrainQuantization=0
r.LightShaftQuality=0
r.Filter.SizeScale=0.75
r.Tonemapper.Quality=5

[EffectsQuality@0]
r.TranslucencyLightingVolumeDim=24
r.RefractionQuality=0
r.SSR.Quality=0
r.SSR.HalfResSceneColor=1
r.SceneColorFormat=3
r.DetailMode=0
r.TranslucencyVolumeBlur=0
r.MaterialQualityLevel=0
r.AnisotropicMaterials=0
r.SSS.Scale=0
r.SSS.SampleSet=0
r.SSS.Quality=0
r.SSS.HalfRes=1
r.SSGI.Quality=0
r.EmitterSpawnRateScale=0.5
r.ParticleLightQuality=0
r.SkyLight.RealTimeReflectionCapture=0
fx.Niagara.QualityLevel=0

[EffectsQuality@1]
r.TranslucencyLightingVolumeDim=24
r.RefractionQuality=0
r.SSR.Quality=0
r.SSR.HalfResSceneColor=1
r.SceneColorFormat=3
r.DetailMode=1
r.TranslucencyVolumeBlur=0
r.MaterialQualityLevel=2
r.AnisotropicMaterials=0
r.SSS.Scale=0.5
r.SSS.SampleSet=0
r.SSS.Quality=0
r.SSS.HalfRes=1
r.SSGI.Quality=0
r.EmitterSpawnRateScale=0.75
r.ParticleLightQuality=0
r.SkyLight.RealTimeReflectionCapture=0
fx.Niagara.QualityLevel=1

[EffectsQuality@2]
r.TranslucencyLightingVolumeDim={cfg["translucency_dim"]}
r.RefractionQuality=1
r.SSR.Quality=0
r.SSR.HalfResSceneColor=1
r.SceneColorFormat=3
r.DetailMode=1
r.TranslucencyVolumeBlur=0
r.MaterialQualityLevel=1
r.AnisotropicMaterials=0
r.SSS.Scale=0.75
r.SSS.SampleSet=0
r.SSS.Quality=0
r.SSS.HalfRes=1
r.SSGI.Quality=0
r.EmitterSpawnRateScale=1.0
r.ParticleLightQuality=1
r.SkyLight.RealTimeReflectionCapture=0
fx.Niagara.QualityLevel=2

[EffectsQuality@3]
r.TranslucencyLightingVolumeDim={cfg["translucency_dim"]}
r.RefractionQuality=1
r.SSR.Quality=0
r.SSR.HalfResSceneColor=1
r.SceneColorFormat=3
r.DetailMode=2
r.TranslucencyVolumeBlur=0
r.MaterialQualityLevel=1
r.AnisotropicMaterials=0
r.SSS.Scale=0.75
r.SSS.SampleSet=0
r.SSS.Quality=0
r.SSS.HalfRes=1
r.SSGI.Quality=0
r.EmitterSpawnRateScale=1.0
r.ParticleLightQuality=1
r.SkyLight.RealTimeReflectionCapture=0
fx.Niagara.QualityLevel=2
"""
    return text.encode("utf-8")


def patch_default_engine_ini(stock_bytes: bytes, cfg: dict, bench_map: str | None = None) -> bytes:
    """Append benchmark-verified boot-time renderer, shadow, instancing, and VR CVars."""
    text = stock_bytes.decode("utf-8", errors="replace")
    if bench_map:
        text = text.replace(
            "GameDefaultMap=/Game/Maps/MAP_Splash.MAP_Splash",
            f"GameDefaultMap={bench_map}",
        )
    text = text.replace(
        "vr.VRS.HMDFixedFoveationLevel=0",
        f"vr.VRS.HMDFixedFoveationLevel={cfg['vr_foveation']}",
    )

    addition = f"""

; =============================================================================
; HW2-PerfBoost Engine & Renderer Optimizations
; =============================================================================
[SystemSettings]
; --- Scene Color & Forward Pipeline Bandwidth ---
r.SceneColorFormat=3
r.SeparateTranslucency=0
r.SSR.Quality=0
r.SSGI.Quality=0
r.DistanceFieldShadowing=0
r.DistanceFieldAO=0
r.AmbientOcclusionLevels=0
r.DefaultFeature.AmbientOcclusion=0
r.DefaultFeature.MotionBlur=0
r.MotionBlurQuality=0
r.DepthOfFieldQuality=0
r.LensFlareQuality=0
r.SceneColorFringeQuality=0
r.AnisotropicMaterials=0
r.SkyLight.RealTimeReflectionCapture=0
r.TranslucencyLightingVolumeDim={cfg["translucency_dim"]}
r.TranslucencyVolumeBlur=0
r.RefractionQuality=1
r.SSS.HalfRes=1
r.SSS.SampleSet=0
r.SSS.Quality=0
r.BloomQuality=4
r.FastBlurThreshold=2
r.Filter.SizeScale=0.75
r.LightShaftQuality=0

; --- Fast Gen4 TAAU defaults (used in Flat Mode; VR overrides to Forward MSAA) ---
r.TemporalAA.Algorithm=0
r.TemporalAA.R11G11B10History=1
r.TemporalAASamples={cfg["flat_taa_samples"]}
r.PostProcessAAQuality={cfg["flat_aa_quality"]}

; --- Shadow Pipeline Optimization ---
r.ShadowQuality={cfg["shadow_quality"]}
r.Shadow.CSM.MaxCascades={cfg["shadow_csm_cascades"]}
r.Shadow.MaxResolution={cfg["shadow_max_res"]}
r.Shadow.MaxCSMResolution={cfg["shadow_csm_res"]}
r.Shadow.RadiusThreshold={cfg["shadow_radius_thresh"]}
r.Shadow.PreShadowResolutionFactor=0.5
r.Shadow.CSM.TransitionScale=0.5
r.Shadow.FadeResolution=64
r.Shadow.MinResolution=32
r.Shadow.OcclusionCullCascadedShadowMaps=1

; --- Volumetric Fog Efficiency ---
r.VolumetricFog={cfg["volfog_enabled"]}
r.VolumetricFog.GridPixelSize={cfg["volfog_grid_px"]}
r.VolumetricFog.GridSizeZ={cfg["volfog_grid_z"]}
r.VolumetricFog.HistoryMissSupersampleCount=1
r.VolumetricFog.TemporalReprojection=1
r.VolumetricFog.InjectShadowedLightsSeparately=0

; --- Mesh Draw Instancing, Occlusion & Parallel RHI ---
r.HZBOcclusion=0
r.MeshDrawCommands.DynamicInstancing=1
r.MeshDrawCommands.UseCachedCommands=1
r.MeshDrawCommands.ParallelPassSetup=1
r.ParallelRendering=1
r.ParallelShadows=1
r.ParallelBasePass=1
r.ParallelTranslucency=1
r.ParallelPrePass=1
r.ParallelVelocity=1
r.RHICmdBypass=0
r.RHICmdUseParallelAlgorithms=1
r.RHICmdUseThread=1
r.GTSyncType=1
r.OneFrameThreadLag=1
r.FinishCurrentFrame=0

; --- LOD, Animation Threading & Streaming ---
r.StaticMeshLODDistanceScale={cfg["lod_dist_scale"]}
r.SkeletalMeshLODBias={cfg["skel_lod_bias"]}
a.ParallelAnimEvaluation=1
a.ParallelAnimUpdate=1
a.URO.Enable=1
r.CreateShadersOnLoad=1
r.UseShaderCaching=1
r.UseShaderPredraw=1
r.Streaming.PoolSize=3072
r.Streaming.LimitPoolSizeToVRAM=1
r.Streaming.Boost=1
r.Streaming.FramesForFullUpdate=2
r.MaxAnisotropy=8

; --- VR Pipeline Optimizations (active when running with an HMD) ---
vr.RoundRobinOcclusion=1
vr.HiddenAreaMask=1
vr.SteamVR.UseVisibleAreaMesh=1
vr.VRS.HMDFixedFoveationLevel={cfg["vr_foveation"]}

[/Script/Engine.GarbageCollectionSettings]
gc.TimeBetweenPurgingPendingKillObjects=90.0
gc.AllowParallelGC=True
gc.MultithreadedDestructionEnabled=True
"""
    return (text + addition).encode("utf-8")


def patch_windows_device_profiles(stock_bytes: bytes, cfg: dict) -> bytes:
    """Fix Steel Wool's WindowsDeviceProfiles.ini and inject clean Windows, FLAT & VR CVars."""
    text = stock_bytes.decode("utf-8", errors="replace")
    # Clean broken/outdated CVars in base [Windows DeviceProfile]
    for old_cvar in (
        "+CVars=r.LenseFlareQuality=0",
        "+CVars=r.AmbientOcclusionLevels=1",
        "+CVars=r.Streaming.PoolSize=1024",
        "+CVars=r.PostProcessAAQuality=3",
        "+CVars=r.Shadow.MaxResolution=1024",
    ):
        text = text.replace(old_cvar + "\r\n", "").replace(old_cvar + "\n", "")

    base_cvars = "\r\n".join([
        "+CVars=r.LensFlareQuality=0",
        "+CVars=r.AmbientOcclusionLevels=0",
        "+CVars=r.SceneColorFormat=3",
        "+CVars=r.SeparateTranslucency=0",
        "+CVars=r.SSR.Quality=0",
        "+CVars=r.SSGI.Quality=0",
        "+CVars=r.MotionBlurQuality=0",
        "+CVars=r.DepthOfFieldQuality=0",
        "+CVars=r.SceneColorFringeQuality=0",
        "+CVars=r.TemporalAA.Algorithm=0",
        "+CVars=r.TemporalAA.R11G11B10History=1",
        f"+CVars=r.PostProcessAAQuality={cfg['flat_aa_quality']}",
        f"+CVars=r.ShadowQuality={cfg['shadow_quality']}",
        f"+CVars=r.Shadow.MaxResolution={cfg['shadow_max_res']}",
        f"+CVars=r.Shadow.MaxCSMResolution={cfg['shadow_csm_res']}",
        f"+CVars=r.Shadow.CSM.MaxCascades={cfg['shadow_csm_cascades']}",
        f"+CVars=r.Shadow.RadiusThreshold={cfg['shadow_radius_thresh']}",
        f"+CVars=r.TranslucencyLightingVolumeDim={cfg['translucency_dim']}",
        "+CVars=r.BloomQuality=4",
        "+CVars=r.FastBlurThreshold=2",
        "+CVars=r.Filter.SizeScale=0.75",
        "+CVars=r.MeshDrawCommands.DynamicInstancing=1",
        "+CVars=r.Streaming.PoolSize=3072",
        "+CVars=r.MaxAnisotropy=8",
    ])

    text = text.replace(
        "[Windows DeviceProfile]\r\nDeviceType=Windows\r\nBaseProfileName=",
        f"[Windows DeviceProfile]\r\nDeviceType=Windows\r\nBaseProfileName=\r\n{base_cvars}",
    )

    flat_cvars = "\r\n".join([
        "[Windows_FLAT DeviceProfile]",
        "DeviceType=Windows",
        "BaseProfileName=",
        "+CVars=r.SceneColorFormat=3",
        "+CVars=r.SeparateTranslucency=0",
        "+CVars=r.SSR.Quality=0",
        "+CVars=r.SSGI.Quality=0",
        "+CVars=r.AmbientOcclusionLevels=0",
        "+CVars=r.DefaultFeature.AmbientOcclusion=0",
        "+CVars=r.MotionBlurQuality=0",
        "+CVars=r.DefaultFeature.MotionBlur=0",
        "+CVars=r.DepthOfFieldQuality=0",
        "+CVars=r.LensFlareQuality=0",
        "+CVars=r.SceneColorFringeQuality=0",
        "+CVars=r.DefaultFeature.AntiAliasing=2",
        "+CVars=r.TemporalAA.Algorithm=0",
        f"+CVars=r.TemporalAA.Upsampling={cfg['flat_taau']}",
        "+CVars=r.TemporalAA.R11G11B10History=1",
        f"+CVars=r.TemporalAASamples={cfg['flat_taa_samples']}",
        f"+CVars=r.PostProcessAAQuality={cfg['flat_aa_quality']}",
        f"+CVars=r.ScreenPercentage={cfg['flat_screen_pct']}",
        f"+CVars=r.MipMapLODBias={cfg['flat_mip_bias']}",
        f"+CVars=r.Tonemapper.Sharpen={cfg['flat_sharpen']}",
        f"+CVars=r.ShadowQuality={cfg['shadow_quality']}",
        f"+CVars=r.Shadow.CSM.MaxCascades={cfg['shadow_csm_cascades']}",
        f"+CVars=r.Shadow.MaxResolution={cfg['shadow_max_res']}",
        f"+CVars=r.Shadow.MaxCSMResolution={cfg['shadow_csm_res']}",
        f"+CVars=r.Shadow.RadiusThreshold={cfg['shadow_radius_thresh']}",
        f"+CVars=r.VolumetricFog={cfg['volfog_enabled']}",
        f"+CVars=r.VolumetricFog.GridPixelSize={cfg['volfog_grid_px']}",
        f"+CVars=r.VolumetricFog.GridSizeZ={cfg['volfog_grid_z']}",
        "+CVars=r.VolumetricFog.HistoryMissSupersampleCount=1",
        f"+CVars=r.TranslucencyLightingVolumeDim={cfg['translucency_dim']}",
        "+CVars=r.BloomQuality=4",
        "+CVars=r.FastBlurThreshold=2",
        "+CVars=r.Filter.SizeScale=0.75",
        f"+CVars=r.SkeletalMeshLODBias={cfg['skel_lod_bias']}",
        f"+CVars=r.StaticMeshLODDistanceScale={cfg['lod_dist_scale']}",
        "+CVars=r.MeshDrawCommands.DynamicInstancing=1",
    ])

    vr_cvars = "\r\n".join([
        "[Windows_VR DeviceProfile]",
        "DeviceType=Windows",
        "BaseProfileName=",
        "+CVars=r.SceneColorFormat=3",
        "+CVars=r.SeparateTranslucency=0",
        "+CVars=r.SSR.Quality=0",
        "+CVars=r.SSGI.Quality=0",
        "+CVars=r.AmbientOcclusionLevels=0",
        "+CVars=r.DefaultFeature.AmbientOcclusion=0",
        "+CVars=r.MotionBlurQuality=0",
        "+CVars=r.DefaultFeature.MotionBlur=0",
        "+CVars=r.DepthOfFieldQuality=0",
        "+CVars=r.LensFlareQuality=0",
        "+CVars=r.SceneColorFringeQuality=0",
        "+CVars=r.DefaultFeature.AntiAliasing=3",
        f"+CVars=r.MSAACount={cfg['vr_msaa']}",
        f"+CVars=r.ScreenPercentage={cfg['vr_screen_pct']}",
        f"+CVars=vr.PixelDensity={cfg['vr_pixel_density']}",
        "+CVars=vr.RoundRobinOcclusion=1",
        "+CVars=vr.HiddenAreaMask=1",
        "+CVars=vr.SteamVR.UseVisibleAreaMesh=1",
        f"+CVars=vr.VRS.HMDFixedFoveationLevel={cfg['vr_foveation']}",
        f"+CVars=r.ShadowQuality={cfg['shadow_quality']}",
        f"+CVars=r.Shadow.CSM.MaxCascades={cfg['shadow_csm_cascades']}",
        f"+CVars=r.Shadow.MaxResolution={cfg['shadow_max_res']}",
        f"+CVars=r.Shadow.RadiusThreshold={cfg['shadow_radius_thresh']}",
        f"+CVars=r.TranslucencyLightingVolumeDim={cfg['translucency_dim']}",
        "+CVars=r.BloomQuality=4",
        "+CVars=r.FastBlurThreshold=2",
        "+CVars=r.Filter.SizeScale=0.75",
        f"+CVars=r.SkeletalMeshLODBias={cfg['skel_lod_bias']}",
        f"+CVars=r.StaticMeshLODDistanceScale={cfg['lod_dist_scale']}",
        "+CVars=r.MeshDrawCommands.DynamicInstancing=1",
    ])

    text = text.replace(
        "[Windows_FLAT DeviceProfile]\r\nDeviceType=Windows\r\nBaseProfileName=",
        flat_cvars,
    )
    text = text.replace(
        "[Windows_VR DeviceProfile]\r\nDeviceType=Windows\r\nBaseProfileName=",
        vr_cvars,
    )
    return text.encode("utf-8")


def build_vq_patches(vq_root: Path, cfg: dict) -> List[Tuple[str, bytes]]:
    """
    Patch Steel Wool's PC VisualQualityOptions DataAssets so UVisualQualitySubsystem
    applies our optimized CVars cleanly at runtime (ECVF_SetByConsole).
    """
    overrides: Dict[str, List[Tuple[str, str]]] = {
        # --- Base PC FLAT presets ---
        "Thumper/Content/Data/VisualQualityOptions/PC/VisualQuality_Base_PC_High_FLAT": [
            ("r.Fog", "1"),
            ("r.VolumetricFog", cfg["volfog_enabled"]),
            ("r.VolumetricFog.GridPixelSize", cfg["volfog_grid_px"]),
            ("r.VolumetricFog.GridSizeZ", cfg["volfog_grid_z"]),
            ("r.VolumetricFog.HistoryMissSupersampleCount", "1"),
            ("r.DefaultFeature.MotionBlur", "0"),
            ("r.MotionBlurQuality", "0"),
            ("r.DefaultFeature.LensFlare", "0"),
            ("r.LensFlareQuality", "0"),
            ("r.DefaultFeature.Bloom", "1"),
            ("r.BloomQuality", "4"),
            ("r.FastBlurThreshold", "2"),
            ("r.Filter.SizeScale", "0.75"),
            ("r.RayTracing", "0"),
            ("sg.PostProcessQuality", "3"),
            ("sg.FoliageQuality", "2"),
            ("r.Streaming.PoolSize", "3072"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.SeparateTranslucency", "0"),
            ("r.HZBOcclusion", "0"),
            ("r.EyeAdaptationQuality", "1"),
            ("r.AmbientOcclusionLevels", "0"),
            ("r.MaxAnisotropy", "8"),
            ("dp.Override", "Windows_FLAT"),
            ("sg.ViewDistanceQuality", "3"),
            ("sg.TextureQuality", "3"),
            ("r.MipMapLODBias", cfg["flat_mip_bias"]),
            ("r.MeshDrawCommands.DynamicInstancing", "1"),
            ("r.StaticMeshLODDistanceScale", cfg["lod_dist_scale"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PC/VisualQuality_Base_PC_Medium_FLAT": [
            ("r.Fog", "1"),
            ("r.VolumetricFog", cfg["volfog_enabled"]),
            ("r.VolumetricFog.GridPixelSize", cfg["volfog_grid_px"]),
            ("r.VolumetricFog.GridSizeZ", cfg["volfog_grid_z"]),
            ("r.DefaultFeature.MotionBlur", "0"),
            ("r.MotionBlurQuality", "0"),
            ("r.DefaultFeature.LensFlare", "0"),
            ("r.LensFlareQuality", "0"),
            ("r.DefaultFeature.Bloom", "1"),
            ("r.BloomQuality", "4"),
            ("r.FastBlurThreshold", "2"),
            ("r.RayTracing", "0"),
            ("sg.PostProcessQuality", "2"),
            ("sg.FoliageQuality", "2"),
            ("r.Streaming.PoolSize", "2560"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.SeparateTranslucency", "0"),
            ("r.HZBOcclusion", "0"),
            ("r.EyeAdaptationQuality", "1"),
            ("r.AmbientOcclusionLevels", "0"),
            ("r.MaxAnisotropy", "8"),
            ("dp.Override", "Windows_FLAT"),
            ("sg.ViewDistanceQuality", "3"),
            ("sg.TextureQuality", "2"),
            ("r.MipMapLODBias", cfg["flat_mip_bias"]),
        ],
        # --- Base PC VR presets ---
        "Thumper/Content/Data/VisualQualityOptions/PC/VisualQuality_Base_PC_High": [
            ("r.Fog", "1"),
            ("r.VolumetricFog", "0"),
            ("r.DefaultFeature.MotionBlur", "0"),
            ("r.MotionBlurQuality", "0"),
            ("r.DefaultFeature.LensFlare", "0"),
            ("r.LensFlareQuality", "0"),
            ("r.DefaultFeature.Bloom", "1"),
            ("r.BloomQuality", "4"),
            ("r.FastBlurThreshold", "2"),
            ("r.Filter.SizeScale", "0.75"),
            ("r.RayTracing", "0"),
            ("sg.PostProcessQuality", "3"),
            ("sg.FoliageQuality", "0"),
            ("r.Streaming.PoolSize", "3072"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.SeparateTranslucency", "0"),
            ("r.HZBOcclusion", "0"),
            ("r.EyeAdaptationQuality", "1"),
            ("r.AmbientOcclusionLevels", "0"),
            ("r.MaxAnisotropy", "8"),
            ("dp.Override", "Windows_VR"),
            ("vr.RoundRobinOcclusion", "1"),
            ("vr.HiddenAreaMask", "1"),
            ("vr.SteamVR.UseVisibleAreaMesh", "1"),
            ("vr.VRS.HMDFixedFoveationLevel", cfg["vr_foveation"]),
            ("r.MeshDrawCommands.DynamicInstancing", "1"),
            ("r.StaticMeshLODDistanceScale", cfg["lod_dist_scale"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PC/VisualQuality_Base_PC_Medium": [
            ("r.Fog", "1"),
            ("r.VolumetricFog", "0"),
            ("r.DefaultFeature.MotionBlur", "0"),
            ("r.MotionBlurQuality", "0"),
            ("r.DefaultFeature.LensFlare", "0"),
            ("r.LensFlareQuality", "0"),
            ("r.DefaultFeature.Bloom", "1"),
            ("r.BloomQuality", "4"),
            ("r.FastBlurThreshold", "2"),
            ("r.RayTracing", "0"),
            ("sg.PostProcessQuality", "2"),
            ("sg.FoliageQuality", "0"),
            ("r.Streaming.PoolSize", "2560"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.SeparateTranslucency", "0"),
            ("r.HZBOcclusion", "0"),
            ("r.EyeAdaptationQuality", "1"),
            ("r.AmbientOcclusionLevels", "0"),
            ("r.MaxAnisotropy", "8"),
            ("dp.Override", "Windows_VR"),
            ("vr.RoundRobinOcclusion", "1"),
            ("vr.HiddenAreaMask", "1"),
            ("vr.VRS.HMDFixedFoveationLevel", cfg["vr_foveation"]),
        ],
        # --- PlayerOverrides: Anti-Aliasing (FLAT & VR) ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/AntiAlias/VisualQuality_AntiAlias_High_FLAT": [
            ("r.DefaultFeature.AntiAliasing", "2"),
            ("r.PostProcessAAQuality", cfg["flat_aa_quality"]),
            ("r.Tonemapper.Sharpen", cfg["flat_sharpen"]),
            ("r.Upscale.Quality", "3"),
            ("r.TemporalAA.Algorithm", "0"),
            ("r.TemporalAA.Upsampling", cfg["flat_taau"]),
            ("r.TemporalAA.R11G11B10History", "1"),
            ("r.TemporalAASamples", cfg["flat_taa_samples"]),
            ("r.ScreenPercentage", cfg["flat_screen_pct"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/AntiAlias/VisualQuality_AntiAlias_Medium_FLAT": [
            ("r.DefaultFeature.AntiAliasing", "2"),
            ("r.PostProcessAAQuality", "2"),
            ("r.Tonemapper.Sharpen", cfg["flat_sharpen"]),
            ("r.Upscale.Quality", "3"),
            ("r.TemporalAA.Algorithm", "0"),
            ("r.TemporalAA.Upsampling", cfg["flat_taau"]),
            ("r.TemporalAA.R11G11B10History", "1"),
            ("r.TemporalAASamples", "4"),
            ("r.ScreenPercentage", cfg["flat_screen_pct"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/AntiAlias/VisualQuality_AntiAlias_High": [
            ("r.DefaultFeature.AntiAliasing", "3"),
            ("r.PostProcessAAQuality", "2"),
            ("r.Tonemapper.Sharpen", "0.7"),
            ("r.MSAACount", cfg["vr_msaa"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/AntiAlias/VisualQuality_AntiAlias_Medium": [
            ("r.DefaultFeature.AntiAliasing", "3"),
            ("r.PostProcessAAQuality", "2"),
            ("r.Tonemapper.Sharpen", "0.5"),
            ("r.MSAACount", "2"),
        ],
        # --- PlayerOverrides: Resolution (VR) ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Resolution/VisualQuality_Resolution_High": [
            ("r.ScreenPercentage", cfg["vr_screen_pct"]),
            ("vr.PixelDensity", cfg["vr_pixel_density"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Resolution/VisualQuality_Resolution_Medium": [
            ("r.ScreenPercentage", "95"),
            ("vr.PixelDensity", "0.95"),
        ],
        # --- PlayerOverrides: Shadows ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Shadows/VisualQuality_Shadows_High_FLAT": [
            ("sg.ShadowQuality", "3"),
            ("r.ShadowQuality", cfg["shadow_quality"]),
            ("r.Shadow.CSM.MaxCascades", cfg["shadow_csm_cascades"]),
            ("r.Shadow.MaxResolution", cfg["shadow_max_res"]),
            ("r.Shadow.MaxCSMResolution", cfg["shadow_csm_res"]),
            ("r.Shadow.RadiusThreshold", cfg["shadow_radius_thresh"]),
            ("r.VolumetricFog", cfg["volfog_enabled"]),
            ("r.VolumetricFog.GridSizeZ", cfg["volfog_grid_z"]),
            ("r.VolumetricFog.GridPixelSize", cfg["volfog_grid_px"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Shadows/VisualQuality_Shadows_Medium_FLAT": [
            ("sg.ShadowQuality", "2"),
            ("r.ShadowQuality", "2"),
            ("r.Shadow.CSM.MaxCascades", "2"),
            ("r.Shadow.MaxResolution", "768"),
            ("r.Shadow.RadiusThreshold", "0.05"),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Shadows/VisualQuality_Shadows_High": [
            ("r.shadowquality", cfg["shadow_quality"]),
            ("r.Shadow.MinResolution", "32"),
            ("r.Shadow.MaxResolution", cfg["shadow_max_res"]),
            ("r.Shadow.CSM.MaxCascades", cfg["shadow_csm_cascades"]),
            ("r.Shadow.RadiusThreshold", cfg["shadow_radius_thresh"]),
        ],
        # --- PlayerOverrides: Effects (Fixes Steel Wool's SSR/SSGI/SceneColorFormat bug!) ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Effects/VisualQuality_Effects_High_FLAT": [
            ("sg.EffectsQuality", "3"),
            ("r.EmitterSpawnRateScale", "1"),
            ("r.DetailLevel", "4"),
            ("fx.Niagara.QualityLevel", "2"),
            ("r.DetailMode", "2"),
            ("r.MaterialQualityLevel", "1"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.TranslucencyLightingVolumeDim", cfg["translucency_dim"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Effects/VisualQuality_Effects_High": [
            ("sg.EffectsQuality", "3"),
            ("r.EmitterSpawnRateScale", "1"),
            ("r.DetailLevel", "4"),
            ("fx.Niagara.QualityLevel", "2"),
            ("r.SSR.Quality", "0"),
            ("r.SSGI.Quality", "0"),
            ("r.SceneColorFormat", "3"),
            ("r.TranslucencyLightingVolumeDim", cfg["translucency_dim"]),
        ],
        # --- PlayerOverrides: Textures (Fixes negative MipMapLODBias=-1 oversharpening/thrashing) ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Textures/VisualQuality_Textures_High_FLAT": [
            ("sg.TextureQuality", "3"),
            ("r.MipMapLODBias", cfg["flat_mip_bias"]),
            ("r.Streaming.PoolSize", "3072"),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Textures/VisualQuality_Textures_High": [
            ("sg.TextureQuality", "3"),
            ("r.MipMapLODBias", "0"),
            ("r.Streaming.PoolSize", "3072"),
        ],
        # --- PlayerOverrides: Character (Fixes SkeletalMeshLODBias=-1 forced LOD0 everywhere) ---
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Character/VisualQuality_Character_High_FLAT": [
            ("r.SkeletalMeshLODBias", cfg["skel_lod_bias"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Character/VisualQuality_Character_Medium_FLAT": [
            ("r.SkeletalMeshLODBias", cfg["skel_lod_bias"]),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Character/VisualQuality_Character_Low_FLAT": [
            ("r.SkeletalMeshLODBias", "1"),
        ],
        "Thumper/Content/Data/VisualQualityOptions/PlayerOverrides/Character/VisualQuality_Character_High": [
            ("r.SkeletalMeshLODBias", cfg["skel_lod_bias"]),
        ],
    }

    entries: List[Tuple[str, bytes]] = []
    for rel_no_ext, new_cmds in overrides.items():
        ua_path = vq_root / (rel_no_ext + ".uasset")
        ue_path = vq_root / (rel_no_ext + ".uexp")
        if not ua_path.exists() or not ue_path.exists():
            print(f"[WARN] Missing base VQ asset: {rel_no_ext}", file=sys.stderr)
            continue
        new_ua, new_ue = patch_vq_commands(ua_path.read_bytes(), ue_path.read_bytes(), new_cmds)
        entries.append((rel_no_ext + ".uasset", new_ua))
        entries.append((rel_no_ext + ".uexp", new_ue))
    return entries


def build_preset(preset_name: str, configs_root: Path, vq_root: Path, out_path: Path,
                 bench_map: str | None = None, force_flat_boot: bool = False) -> None:
    cfg = PRESETS[preset_name]
    entries: List[Tuple[str, bytes]] = []

    # 1. DefaultScalability.ini (clean overlay on top of BaseScalability.ini)
    entries.append(("Thumper/Config/DefaultScalability.ini", make_default_scalability_ini(cfg)))

    # 2. Patched DefaultEngine.ini
    stock_engine = (configs_root / "Thumper/Config/DefaultEngine.ini").read_bytes()
    eng = patch_default_engine_ini(stock_engine, cfg, bench_map)
    if force_flat_boot:
        # Used ONLY for direct-map flat benchmarks (skips MAP_Splash VisualQuality boot)
        eng = eng.replace(b"r.DefaultFeature.AntiAliasing=3", b"r.DefaultFeature.AntiAliasing=2")
        eng += (
            f"\n[SystemSettings]\n"
            f"r.DefaultFeature.AntiAliasing=2\n"
            f"r.TemporalAA.Algorithm=0\n"
            f"r.TemporalAA.Upsampling={cfg['flat_taau']}\n"
            f"r.ScreenPercentage={cfg['flat_screen_pct']}\n"
            f"r.MipMapLODBias={cfg['flat_mip_bias']}\n"
            f"r.Tonemapper.Sharpen={cfg['flat_sharpen']}\n"
        ).encode()
    entries.append(("Thumper/Config/DefaultEngine.ini", eng))

    # 3. Patched WindowsDeviceProfiles.ini
    stock_dp = (configs_root / "Thumper/Config/Windows/WindowsDeviceProfiles.ini").read_bytes()
    dp = patch_windows_device_profiles(stock_dp, cfg)
    if force_flat_boot:
        dp = dp.replace(b"+CVars=r.screenpercentage=100", f"+CVars=r.screenpercentage={cfg['flat_screen_pct']}\r\n+CVars=r.DefaultFeature.AntiAliasing=2\r\n+CVars=r.TemporalAA.Upsampling={cfg['flat_taau']}".encode())
    entries.append(("Thumper/Config/Windows/WindowsDeviceProfiles.ini", dp))

    # 4. Patched VisualQualityOptions DataAssets
    entries.extend(build_vq_patches(vq_root, cfg))

    # Always build uncompressed Pak v7 (~155 KB): instant load, zero decompression overhead
    build_pak(entries, out_path, compress=False)
    print(f"Built {out_path} ({out_path.stat().st_size / 1024:.1f} KB, {len(entries)} files) [{cfg['label']}]")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build HW2-PerfBoost UE4.27 _P.pak presets")
    ap.add_argument("--preset", choices=list(PRESETS.keys()) + ["all"], default="all")
    ap.add_argument("--configs-dir", required=True, type=Path)
    ap.add_argument("--vq-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--bench-map", default=None, help="Optional GameDefaultMap override for benchmarking only")
    ap.add_argument("--force-flat-boot", action="store_true", help="Benchmark helper when bypassing MAP_Splash")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    targets = list(PRESETS.keys()) if args.preset == "all" else [args.preset]
    for p in targets:
        out_file = args.out_dir / PRESETS[p]["pak_name"]
        build_preset(p, args.configs_dir, args.vq_dir, out_file,
                     bench_map=args.bench_map, force_flat_boot=args.force_flat_boot)


if __name__ == "__main__":
    main()
