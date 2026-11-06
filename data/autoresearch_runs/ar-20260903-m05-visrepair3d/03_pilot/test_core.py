from __future__ import annotations

import unittest

from revealrepair_core import (
    corrupt_scene,
    evaluate,
    hard_constraints,
    make_base_scene,
    solve_beam,
)


class RevealRepairCoreTests(unittest.TestCase):
    def test_base_scene_satisfies_schedule_and_constraints(self) -> None:
        scene, labels = make_base_scene(1000)
        result = evaluate(scene, labels)
        self.assertTrue(result.hard_valid)
        self.assertAlmostEqual(result.schedule_loss, 0.0, places=8)
        self.assertAlmostEqual(result.satisfaction, 1.0, places=8)

    def test_corruptions_are_hard_valid_and_worsen_schedule(self) -> None:
        base, labels = make_base_scene(1001)
        for index, corruption in enumerate(
            ["premature_reveal", "missed_reveal", "back_facing", "target_displacement", "compound"]
        ):
            corrupted, _ = corrupt_scene(base, labels, corruption, 1, 4000 + index)
            self.assertTrue(hard_constraints(corrupted)[0])
            self.assertGreater(evaluate(corrupted, labels).schedule_loss, 0.0)

    def test_attributed_solver_improves_compound_case(self) -> None:
        base, labels = make_base_scene(1002)
        corrupted, _ = corrupt_scene(base, labels, "compound", 1, 5000)
        before = evaluate(corrupted, labels)
        repaired = solve_beam(
            "revealrepair_attributed",
            corrupted,
            labels,
            attributed=True,
            max_depth=2,
            beam_width=8,
            max_evaluations=500,
        )
        self.assertTrue(repaired.evaluation.hard_valid)
        self.assertLess(repaired.evaluation.schedule_loss, before.schedule_loss)


if __name__ == "__main__":
    unittest.main()
