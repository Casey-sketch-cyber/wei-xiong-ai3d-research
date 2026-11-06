# Photo baseline stratification audit

Photo F-score@0.05 median: `0.236823`.

| style | low-group volume | high-group volume | low-group delta F | high-group delta F | top-quartile delta F |
|---|---:|---:|---:|---:|---:|
| edge | 0.299 | 0.365 | +0.103 | +0.010 | -0.049 |
| flat | 0.293 | 0.707 | +0.089 | +0.012 | -0.018 |
| low_detail | 0.282 | 0.329 | +0.089 | -0.004 | -0.060 |
| sketch | 0.121 | 0.393 | +0.164 | +0.021 | -0.040 |
| watercolor | 0.258 | 0.427 | +0.110 | +0.041 | -0.014 |

The volumetric contraction persists in the high-quality half, but the aggregate F-score gain is concentrated in the low-quality photo half. In the top photo-quality quartile, the mean F-score change is negative for every style.
