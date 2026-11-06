# M05 novelty-scan protocol

Snapshot date: 2026-09-03 (Asia/Shanghai)

## Candidate claim under test

The original generic visibility-repair claim was rejected during screening.
The surviving candidate is a post-hoc, fixed-route repair task for existing
AI-generated exhibition layouts. Given a route and a signed, trajectory-indexed
schedule that states when each exhibit should remain hidden, become visible,
or is unconstrained, the method diagnoses premature reveal and missed reveal,
attributes violations to blocking geometry or orientation, and searches over
bounded local object or partition translations and yaw changes, ranking signed
schedule loss before final-state edit cost while preserving collision, route
clearance, room bounds, and protected spatial relations.

The claim is deliberately narrower than each of the following established
areas: visibility-aware layout optimization, virtual cinematography with
positive/negative visibility constraints, route optimization under visual
objectives, and sparse local repair of generated indoor scenes.

## Search families

1. Direct task: visibility-aware, viewability-aware, or occlusion-aware 3D
   layout repair and minimal-change scene refinement.
2. Text-conditioned 3D scenes: scene synthesis, planning, layout refinement,
   physical/semantic constraint correction, and LLM/VLM-based optimization.
3. Exhibition applications: museum/gallery layout, exhibit placement, visitor
   paths, sight lines, visual accessibility, and display optimization.
4. Classical interior layout: furniture arrangement with visibility,
   accessibility, circulation, and functional constraints.
5. Robotics/graphics adjacency: object rearrangement to reveal targets,
   next-best-view/viewpoint planning, and ray-based coverage optimization.
6. Evaluation/data: scene-error correction benchmarks, procedural corruption,
   minimum-edit repair, and objective viewability metrics.
7. Narrative reveal adjacency: positive/negative visibility constraints across
   shots, visibility-transition planning, serial vision, progressive reveal,
   route-conditioned perception profiles, and curatorial route alignment.

## Sources and evidence levels

- Discovery: Semantic Scholar Graph API, OpenAlex API, Crossref API, arXiv, and
  targeted web search.
- Metadata validation: DOI records plus publisher/proceedings metadata.
- Technical validation: official paper HTML/PDF, author project page, or
  official code repository. Search snippets alone cannot establish novelty.

## Inclusion rules

- Include work that optimizes object position/orientation, observer/camera
  trajectories, line of sight, occlusion, navigation, spatial relations, or
  minimum edit cost in 2D/3D layouts.
- Include preprints through the snapshot date and older foundational graphics
  work; do not impose a recent-year cutoff.
- Retain near misses from adjacent communities because they can invalidate a
  mechanism-level claim even when the application differs.

## Exclusion rules

- Pure image de-occlusion, 3D reconstruction visibility weighting, or text
  layout work is excluded after recording why it is not a task match.
- Studies that only evaluate subjective museum experience are context, not a
  method match, unless they optimize geometric layout or sight lines.

## Decision labels

- `BLOCKS`: same task and materially same repair mechanism/contribution.
- `STRONG_OVERLAP`: same task with a different optimization mechanism, or the
  same mechanism in a closely substitutable task.
- `PARTIAL_OVERLAP`: shares one or more objectives/constraints but not the full
  task definition.
- `CONTEXT`: useful background without threatening the candidate claim.

The final wording will be `no direct match found in this scan`, never an
absolute claim that nobody has done it.
