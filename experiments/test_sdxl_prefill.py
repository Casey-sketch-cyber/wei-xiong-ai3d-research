import unittest

import numpy as np

from experiments.latent_aligned import aligned_prediction, grid_cover
from experiments.models import _diffusion_input, load_model


class PrefillTest(unittest.TestCase):
    def test_black_and_gray_only_replace_the_hidden_pixels(self):
        image = np.full((24, 24, 3), (45, 108, 175), dtype=np.uint8)
        mask = np.zeros((24, 24), dtype=bool)
        mask[4:12, 5:13] = True
        for color, value in (("black", 0), ("gray", 128)):
            with self.subTest(color=color):
                damaged = _diffusion_input(image, mask, color)
                np.testing.assert_array_equal(damaged[mask], value)
                np.testing.assert_array_equal(damaged[~mask], image[~mask])
        np.testing.assert_array_equal(image[mask], np.tile([45, 108, 175], (64, 1)))

    def test_ring_is_exactly_eight_pixels_from_corner_or_interior_hole(self):
        for edge in (0, 9):
            with self.subTest(edge=edge):
                image = np.full((32, 32, 3), (50, 210, 60), dtype=np.uint8)
                mask = np.zeros(image.shape[:2], dtype=bool)
                mask[edge:edge + 8, edge:edge + 8] = True
                ring = np.zeros_like(mask)
                ring[max(0, edge - 8):edge + 16, max(0, edge - 8):edge + 16] = True
                ring &= ~mask
                image[ring] = (10, 77, 237)
                image[mask] = (223, 39, 125)
                damaged = _diffusion_input(image, mask, "ring")
                np.testing.assert_array_equal(damaged[mask], np.tile([10, 77, 237], (64, 1)))
                np.testing.assert_array_equal(damaged[~mask], image[~mask])

    def test_ring_uses_no_hidden_reference_color_and_score_hole_controls_composite(self):
        image = np.full((512, 512, 3), 46, dtype=np.uint8)
        mask = np.zeros(image.shape[:2], dtype=bool)
        mask[9, 19] = True
        aligned = grid_cover(mask)
        changed = image.copy()
        changed[aligned] = 209
        for color in ("gray", "ring"):
            with self.subTest(color=color):
                seen = []

                def model(damaged, expanded, seed):
                    self.assertEqual(seed, 2026)
                    np.testing.assert_array_equal(expanded, aligned)
                    prefilled = _diffusion_input(damaged, expanded, color)
                    seen.append(prefilled)
                    return np.full_like(damaged, 10)

                for reference in (image, changed):
                    result = aligned_prediction(model, reference, mask, 2026)
                    np.testing.assert_array_equal(result[mask], 10)
                    np.testing.assert_array_equal(result[~mask], reference[~mask])
                np.testing.assert_array_equal(seen[0], seen[1])

    def test_empty_ring_fails_and_nonexperiment_configs_reject_prefill(self):
        with self.assertRaisesRegex(ValueError, "No visible pixels"):
            _diffusion_input(np.zeros((16, 16, 3), np.uint8), np.ones((16, 16), bool), "ring")
        with self.assertRaisesRegex(ValueError, "requires SDXL"):
            load_model("lama", "cpu", None, strength=0.99, init_prefill="ring")
        with self.assertRaisesRegex(ValueError, "strength 0.99"):
            load_model("sdxl", "cpu", None, init_prefill="gray")


if __name__ == "__main__":
    unittest.main()
