# Hunyuan3D 2.1 pilot report

- Successful shapes: 144 / 144
- Watertight rate: 0.396
- Strict mesh volume is reported only for watertight outputs; convex-hull envelope volume covers all valid meshes.
- Styles with median convex-hull volume ratio below 0.8: 0 / 5
- Median convex-hull ratio seed difference: 0.018

## Relative-to-photo aggregate

| style      |   n |   objects |   seeds |   volume_ratio_valid_n |   mean_volume_ratio |   median_volume_ratio |   mean_volume_ratio_ci_low |   mean_volume_ratio_ci_high |   pct_volume_ratio_below_0.8 |   convex_hull_volume_ratio_valid_n |   mean_convex_hull_volume_ratio |   median_convex_hull_volume_ratio |   mean_convex_hull_volume_ratio_ci_low |   mean_convex_hull_volume_ratio_ci_high |   pct_convex_hull_volume_ratio_below_0.8 |   mean_min_extent_ratio |   mean_delta_fscore_0.05 |   mean_delta_chamfer_l2 |
|:-----------|----:|----------:|--------:|-----------------------:|--------------------:|----------------------:|---------------------------:|----------------------------:|-----------------------------:|-----------------------------------:|--------------------------------:|----------------------------------:|---------------------------------------:|----------------------------------------:|-----------------------------------------:|------------------------:|-------------------------:|------------------------:|
| edge       |  24 |        12 |       2 |                      5 |              0.9962 |                1.0260 |                     0.6702 |                      1.2425 |                      20.0000 |                                 24 |                          0.9678 |                            1.0117 |                                 0.8402 |                                  1.0878 |                                  12.5000 |                  1.0143 |                   0.0025 |                 -0.0005 |
| flat       |  24 |        12 |       2 |                      7 |              0.7888 |                0.9066 |                     0.5361 |                      1.0180 |                      42.8571 |                                 24 |                          0.9433 |                            0.9987 |                                 0.8584 |                                  1.0092 |                                   8.3333 |                  0.9871 |                   0.0063 |                 -0.0008 |
| low_detail |  24 |        12 |       2 |                      8 |              0.8083 |                0.8825 |                     0.6093 |                      0.9418 |                      25.0000 |                                 24 |                          0.8968 |                            0.9580 |                                 0.8008 |                                  0.9733 |                                  12.5000 |                  0.9508 |                  -0.0162 |                  0.0029 |
| sketch     |  24 |        12 |       2 |                      7 |              0.7847 |                0.9465 |                     0.5712 |                      0.9897 |                      28.5714 |                                 24 |                          0.9321 |                            0.9852 |                                 0.8565 |                                  0.9857 |                                   8.3333 |                  0.9692 |                  -0.0002 |                 -0.0000 |
| watercolor |  24 |        12 |       2 |                      5 |              0.8387 |                0.9590 |                     0.4901 |                      1.0679 |                      20.0000 |                                 24 |                          0.9316 |                            0.9977 |                                 0.8388 |                                  0.9969 |                                   8.3333 |                  0.9626 |                  -0.0101 |                  0.0028 |

## Seed stability

| style      |   n |   mean_abs_convex_hull_ratio_seed_difference |   median_abs_convex_hull_ratio_seed_difference |   convex_hull_ratio_seed_correlation |
|:-----------|----:|---------------------------------------------:|-----------------------------------------------:|-------------------------------------:|
| edge       |  12 |                                       0.0805 |                                         0.0423 |                               0.9021 |
| flat       |  12 |                                       0.0389 |                                         0.0250 |                               0.9161 |
| low_detail |  12 |                                       0.0610 |                                         0.0184 |                               0.9161 |
| sketch     |  12 |                                       0.0237 |                                         0.0155 |                               0.7203 |
| watercolor |  12 |                                       0.0247 |                                         0.0119 |                               0.7133 |

Visual review of the geometry and official PBR outputs is required before a full rerun.

## Photo baseline comparison

{
  "median_hunyuan_photo_fscore": 0.3162360062787255,
  "median_triposr_photo_fscore": 0.2438764129737015,
  "objects_hunyuan_fscore_better": 9,
  "objects_compared": 12
}