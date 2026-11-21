# Benchmarks

All measurements were taken on real hardware running **Five Nights at Freddy's: Help Wanted 2** (`HW2-Win64-Shipping.exe`, UE 4.27, Steam AppID `2287520`) via DX11/DXVK in headless `gamescope` at **4K (3840x2160)** with VSync disabled (`DXVK_CONFIG="dxgi.syncInterval=0;d3d11.maxFrameLatency=3"`). Frame times and GPU stats were recorded every 100 ms with **MangoHud 0.8.4** (`pci_dev=0:03:00.0`).

## Test Setup

- **GPU:** AMD Radeon RX 7900 XT (RADV NAVI31)
- **CPU:** AMD Ryzen 9 7900 (12-Core / 24-Thread)
- **OS:** CachyOS Linux (`7.3.5-2-cachyos`)
- **Proton:** `proton-cachyos-slr` (DXVK / DX11)
- **Resolution:** `3840x2160` (4K, GPU-bound)
- **Baseline (`Stock High`):** The exact CVar set applied by stock `VisualQuality_Base_PC_High_FLAT`, `PlayerOverrides/*_High_FLAT`, and `BaseScalability.ini` tier 3 (`r.PostProcessAAQuality=6`, `r.TemporalAASamples=16`, `r.Shadow.MaxResolution=2048`, `r.Shadow.CSM.MaxCascades=10`, `r.SceneColorFormat=4`, `r.SSR.Quality=3`, `r.SeparateTranslucency=1`, `r.MipMapLODBias=-1`, `r.SkeletalMeshLODBias=-1`, `r.VolumetricFog.GridSizeZ=64`).

> **Note on test methodology:** To make every run 100% repeatable without manual menu navigation, the benchmark loaded `MAP_HUB_MainHub` and `MAP_BS_MakeoverRoxy` directly as the startup map (full 3D level geometry, lighting, lightmaps, mirror RenderTarget, ~6.5 GB VRAM, 100% GPU load, without scripted minigame AI ticks). During active gameplay with animatronics, CPU overhead can lower absolute peak FPS, while the GPU speedup ratio applies directly wherever the GPU is the bottleneck (VR, 4K, mid-range GPUs, Steam Deck).

## Main Results (4K 3840x2160)

### Scene A: `MAP_HUB_MainHub` (Pizzaplex Main Hub)

| Preset | Avg FPS | Speedup | Median FPS | 1% Low FPS | Avg Frametime | VRAM | GPU Power |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stock High (Flat)** | `395.91` | `1.00x` | `396.73` | `325.82` | `2.53 ms` | `6.68 GB` | `274 W` |
| **NativeQuality** (100% native res) | **`626.26`** | **`1.58x` (+58.2%)** | **`629.60`** | **`468.95` (+43.9%)** | **`1.60 ms`** | **`6.24 GB`** | **`261 W`** |
| **Balanced** (80% Fast TAAU) | **`818.98`** | **`2.07x` (+106.9%)** | **`832.56`** | **`570.98` (+75.2%)** | **`1.22 ms`** | **`6.24 GB`** | **`247 W`** |
| **UltraPerf** (75% Fast TAAU) | **`873.45`** | **`2.21x` (+120.6%)** | **`886.95`** | **`672.09` (+106.3%)** | **`1.14 ms`** | **`6.24 GB`** | **`241 W`** |

### Scene B: `MAP_BS_MakeoverRoxy` (Roxy's Salon with real-time mirror)

| Preset | Avg FPS | Speedup | Median FPS | 1% Low FPS | Avg Frametime | VRAM | GPU Power |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stock High (Flat)** | `324.17` | `1.00x` | `325.09` | `304.39` | `3.08 ms` | `6.50 GB` | `256 W` |
| **NativeQuality** (100% native res) | **`569.79`** | **`1.76x` (+75.8%)** | **`573.69`** | **`376.25` (+23.6%)** | **`1.76 ms`** | **`5.98 GB`** | **`258 W`** |
| **Balanced** (80% Fast TAAU) | **`724.60`** | **`2.24x` (+123.5%)** | **`719.80`** | **`671.19` (+120.5%)** | **`1.38 ms`** | **`5.90 GB`** | **`251 W`** |
| **UltraPerf** (75% Fast TAAU) | **`767.96`** | **`2.37x` (+136.9%)** | **`783.19`** | `231.58`\* | **`1.30 ms`** | **`5.73 GB`** | **`251 W`** |

*\*One brief frame spike happened during the 10-second capture window on UltraPerf Roxy; median FPS stayed at 783.19.*

## What did NOT work (ablation tests)

While tuning the mod on `MAP_HUB_MainHub` (4K, compared against the lighter default `WindowsDeviceProfiles` baseline of `422.77 FPS`), a few popular UE4 "performance tweaks" turned out to make things noticeably worse in HW2's Forward Renderer:

| Test | Avg FPS | vs. Default (`422.77`) | Takeaway |
|---|---:|---:|---|
| `r.TemporalAA.Algorithm=1` (Gen5 TAA) + `r.EarlyZPass=2` + `r.Forward.LightGridPixelSize=64` @ 100% | `257.38` | **0.61x (-39% slower)** | Gen5 TAA adds ~1.5 ms in Forward Shading; `LightGridPixelSize=64` makes light culling 4x coarser per pixel; `EarlyZPass=2` slows down the prepass. Removed all three. |
| `r.TemporalAA.Algorithm=1` (Gen5 TAAU) @ 75% | `458.90` | `1.09x` | Heavy Gen5 shader ate almost all of the 75% resolution gain. |
| **Forward 2x MSAA + Engine Fixes @ 100%** | **`493.52`** | **`1.17x`** | Solid gain even with zero upscaling (also great for VR). |
| **Fast Gen4 TAAU (`r.TemporalAA.Algorithm=0`) @ 80% + Engine Fixes** | **`676.66`** | **`1.60x`** | Huge jump with sharp edges and 390 MB less VRAM. |
| **Fast Gen4 TAAU (`r.TemporalAA.Algorithm=0`) @ 75% + Engine Fixes** | **`741.98`** | **`1.76x`** | Fastest preset with very minor visual tradeoff. |

## Other checks

- **DX11 vs. DX12** (`MAP_TB_Carousel`, 4K): DX11 (`264.05 FPS`, 1% Low `254.16`) beat DX12 (`260.34 FPS`, 1% Low `233.50`). Stick with default DX11.
- **Normal boot test:** Tested `presets/HW2PerfBoost_Balanced_P.pak` launching normally through `MAP_Splash` with no errors or crashes.
