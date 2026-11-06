# Figure role decision

## Decision

Figure 1 should be a framework / controlled benchmark figure only. It should not include the aggregate result panel.

The aggregate result panel should be Figure 2.

## Why

The checked JCDE sample paper `qwag035` uses Figure 1 as a proposed-framework figure: it shows the task objects, inputs, pipeline modules, prompts, masks, LoRA/DreamBooth, diffusion outputs, and the final edited 3D Gaussian Splatting result. It does not mix in the final performance charts. Later figures and tables carry the performance-evaluation evidence.

For M03, the analogous figure roles should be:

- Figure 1: controlled benchmark construction and reconstruction pipeline;
- Figure 2: aggregate volume / z-extent / F-score / metric-paradox results;
- Figure 3: selected metric-paradox examples or scatter/case analysis;
- Figure 4: robustness rerun.

## Revised Figure 1 structure

Panel A: matched inputs from the same object.

Panel B: same TripoSR pipeline.

Panel C: TripoSR mesh renders.

Panel D: paired diagnostics schematic only, listing volume ratio, z-extent ratio, Chamfer change, and F-score change.

Do not place `aggregate_main_results.png` inside Figure 1.
