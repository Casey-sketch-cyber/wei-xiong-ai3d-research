# M03 confirmatory transform QA amendment

Status: frozen after input-only visual QA and before any confirmatory model
inference.

The first hash-ranked object's contact sheet showed that the prespecified
high-edge implementation (radius-2 blur, Canny 120/240, and dilation) produced
an almost blank foreground for a low-contrast object. That would confound
severity with an empty-image failure and is classified as a non-monotonic
transform implementation under Section 3 of the implementation addendum.

The high-edge transform is replaced by a deterministic silhouette-only
abstraction:

1. convert the fixed alpha mask to a binary mask;
2. erode it once with a 5x5 square kernel;
3. subtract the eroded mask from the original mask;
4. draw the resulting inner silhouette boundary in RGB value 20 on white; and
5. reattach the unchanged alpha mask.

This replacement removes all internal texture and line detail while retaining
a non-empty, recognizable outer shape. Edge-low and edge-medium are unchanged.
No model output, reconstruction, or evaluation metric was inspected when this
amendment was made.
