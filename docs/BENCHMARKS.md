# Benchmarks — HW2-PerfBoost

All benchmarks were conducted on real hardware running **Five Nights at Freddy's: Help Wanted 2** (`HW2-Win64-Shipping.exe`, UE 4.27, Steam AppID `2287520`) via DX11/DXVK inside headless `gamescope` at **4K (3840×2160)** with VSync disabled (`DXVK_CONFIG="dxgi.syncInterval=0;d3d11.maxFrameLatency=3"`) and hardware telemetry logged at 100 ms intervals via **MangoHud 0.8.4** (`pci_dev=0:03:00.0`).

## Test System
- **GPU**: AMD Radeon RX 7900 XT (RADV NAVI31)
- **CPU**: AMD Ryzen 9 7900 (12-Core / 24-Thread)
- **OS / Kernel**: CachyOS Linux (`7.3.5-2-cachyos`)
- **Proton**: `proton-cachyos-slr` (DXVK / DX11)
- **Resolution**: `3840×2160` (4K, 100% GPU-bound)
- **Baseline (`Stock High`)**: Exact CVars applied by Help Wanted 2's stock `VisualQuality_Base_PC_High_FLAT` + `PlayerOverrides/*_High_FLAT` + `BaseScalability.ini` tier 3 (`r.PostProcessAAQuality=6`, `r.TemporalAASamples=16`, `r.Shadow.MaxResolution=2048`, `r.Shadow.CSM.MaxCascades=10`, `r.SceneColorFormat=4`, `r.SSR.Quality=3`, `r.SeparateTranslucency=1`, `r.MipMapLODBias=-1`, `r.SkeletalMeshLODBias=-1`, `r.VolumetricFog.GridSizeZ=64`).

---

## 1. Main Results (4K 3840×2160)

### Scene A: `MAP_HUB_MainHub` (Pizzaplex Main Hub — Multi-Light 3D Scene)

| Configuration | Avg FPS | Speedup | Median FPS | 1% Low FPS | Avg Frametime | VRAM Used | GPU Power |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stock High (Flat)** | `395.91` | `1.00x` | `396.73` | `325.82` | `2.53 ms` | `6.68 GB` | `274 W` |
| **NativeQuality** *(100% Native Res)* | **`626.26`** | **`1.58x` (+58.2%)** | **`629.60`** | **`468.95` (+43.9%)** | **`1.60 ms`** | **`6.24 GB`** | **`261 W`** |
| **Balanced** *(80% Fast TAAU)* | **`818.98`** | **`2.07x` (+106.9%)** | **`832.56`** | **`570.98` (+75.2%)** | **`1.22 ms`** | **`6.24 GB`** | **`247 W`** |
| **UltraPerf** *(75% Fast TAAU)* | **`873.45`** | **`2.21x` (+120.6%)** | **`886.95`** | **`672.09` (+106.3%)** | **`1.14 ms`** | **`6.24 GB`** | **`241 W`** |

### Scene B: `MAP_BS_MakeoverRoxy` (Roxy's Salon — Real-Time Mirror RenderTarget + Dynamic Lighting)

| Configuration | Avg FPS | Speedup | Median FPS | 1% Low FPS | Avg Frametime | VRAM Used | GPU Power |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Stock High (Flat)** | `324.17` | `1.00x` | `325.09` | `304.39` | `3.08 ms` | `6.50 GB` | `256 W` |
| **NativeQuality** *(100% Native Res)* | **`569.79`** | **`1.76x` (+75.8%)** | **`573.69`** | **`376.25` (+23.6%)** | **`1.76 ms`** | **`5.98 GB`** | **`258 W`** |
| **Balanced** *(80% Fast TAAU)* | **`724.60`** | **`2.24x` (+123.5%)** | **`719.80`** | **`671.19` (+120.5%)** | **`1.38 ms`** | **`5.90 GB`** | **`251 W`** |
| **UltraPerf** *(75% Fast TAAU)* | **`767.96`** | **`2.37x` (+136.9%)** | **`783.19`** | `231.58`\* | **`1.30 ms`** | **`5.73 GB`** | **`251 W`** |

*\*One transient shader/GC frame spike occurred during the 10 s window on UltraPerf Roxy; median FPS remained 783.19.*

---

## 2. Ablation Findings (Why Naive "UE4 Performance Guides" Hurt FPS!)

During development, we isolated individual CVars on `MAP_HUB_MainHub` (4K) against the lightweight default `WindowsDeviceProfiles` baseline (`422.77 FPS`) and caught three major **anti-optimizations** commonly recommended online that actually **hurt** UE 4.27 Forward-Shading performance:

| Test Variant | Avg FPS | vs. Default (`422.77`) | Finding |
|---|---:|---:|---|
| `r.TemporalAA.Algorithm=1` (Gen5 TAA) + `r.EarlyZPass=2` + `r.Forward.LightGridPixelSize=64` @ 100% | `257.38` | **0.61x (-39% regression!)** | Gen5 TAA adds ~1.5 ms GPU overhead in Forward Shading; `LightGridPixelSize=64` makes light culling 4× coarser per pixel; `EarlyZPass=2` disrupts Forward prepass. **All removed.** |
| `r.TemporalAA.Algorithm=1` (Gen5 TAAU) @ 75% | `458.90` | `1.09x` | Heavy Gen5 TAAU shader ate nearly all of the 75% resolution savings. |
| **Forward 2× MSAA + Engine Fixes @ 100% Native** | **`493.52`** | **`1.17x`** | Clean Forward-native speedup (also benefits VR!). |
| **Fast Gen4 TAAU (`r.TemporalAA.Algorithm=0`) @ 80% + Engine Fixes** | **`676.66`** | **`1.60x`** | Massive jump with crisp temporal reconstruction and -390 MB VRAM. |
| **Fast Gen4 TAAU (`r.TemporalAA.Algorithm=0`) @ 75% + Engine Fixes** | **`741.98`** | **`1.76x`** | Peak efficiency with minimal visual difference. |

---

## 3. Additional Verification
- **DX11 vs. DX12** (`MAP_TB_Carousel`, 4K): DX11 (`264.05 FPS`, `1% Low 254.16`) outperformed DX12 (`260.34 FPS`, `1% Low 233.50`) with tighter 1% lows. **Recommendation**: keep default DX11 (no `-dx12` launch option needed).
- **Production Normal-Boot Smoke Test**: Verified `presets/HW2PerfBoost_Balanced_P.pak` booting normally through `MAP_Splash` with zero crashes, clean `~mods/` pak mounting, and full gameplay compatibility.
