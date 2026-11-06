from __future__ import annotations

import unittest

from formal_benchmark import (
    CORRUPTIONS,
    FORMAL_ROTATION_DEGREES,
    FORMAL_TRANSLATION_STEPS,
    formal_corrupt_scene,
    make_formal_base_scene,
)

from revealrepair_core import Box, Scene, evaluate, hard_constraints, solve_beam


class FormalBenchmarkTests(unittest.TestCase):
    def test_varied_base_scenes_are_valid(self) -> None:
        families = set()
        exhibit_counts = set()
        for seed in range(3000, 3009):
            scene, labels, metadata = make_formal_base_scene(seed)
            result = evaluate(scene, labels)
            self.assertTrue(result.hard_valid)
            self.assertAlmostEqual(result.schedule_loss, 0.0)
            families.add(metadata["route_family"])
            exhibit_counts.add(metadata["exhibit_count"])
        self.assertGreaterEqual(len(families), 2)
        self.assertGreaterEqual(len(exhibit_counts), 2)

    def test_off_grid_corruptions_worsen_schedule(self) -> None:
        base, labels, _ = make_formal_base_scene(3001)
        for severity in (1, 2, 3):
            for index, corruption in enumerate(CORRUPTIONS):
                corrupted, _, metadata = formal_corrupt_scene(
                    base,
                    labels,
                    corruption,
                    severity,
                    700_000 + severity * 100 + index,
                )
                result = evaluate(corrupted, labels)
                self.assertTrue(result.hard_valid)
                self.assertGreater(result.schedule_loss, 0.0)
                self.assertTrue(metadata["off_grid"])

    def test_attributed_search_reduces_an_off_grid_compound_fault(self) -> None:
        base, labels, _ = make_formal_base_scene(3002)
        corrupted, _, _ = formal_corrupt_scene(
            base, labels, "compound", 2, 700_204
        )
        before = evaluate(corrupted, labels)
        repaired = solve_beam(
            "revealrepair_attributed",
            corrupted,
            labels,
            attributed=True,
            max_depth=3,
            beam_width=8,
            max_evaluations=480,
            translation_steps=FORMAL_TRANSLATION_STEPS,
            rotation_degrees=FORMAL_ROTATION_DEGREES,
        )
        self.assertTrue(repaired.evaluation.hard_valid)
        self.assertLess(repaired.evaluation.schedule_loss, before.schedule_loss)
        self.assertLessEqual(repaired.edit_count, 3)

    def test_route_clearance_checks_between_route_samples(self) -> None:
        scene = Scene(
            scene_id="continuous_clearance_test",
            room=[0.0, 4.0, 0.0, 4.0],
            route=[[0.5, 2.0, 1.62], [3.5, 2.0, 1.62]],
            objects=[
                Box(
                    object_id="obstacle",
                    kind="partition",
                    center=[2.0, 2.0, 1.0],
                    size=[0.2, 0.8, 2.0],
                    movable=False,
                )
            ],
            exhibit_order=[],
            protected_order=[],
        )
        valid, _, path_violations, _, _ = hard_constraints(scene)
        self.assertFalse(valid)
        self.assertGreater(path_violations, 0)


if __name__ == "__main__":
    unittest.main()
