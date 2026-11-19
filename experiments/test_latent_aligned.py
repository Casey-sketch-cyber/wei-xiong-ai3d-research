import unittest

import numpy as np
from PIL import Image

from experiments.latent_aligned import aligned_prediction, grid_cover


class LatentAlignedTest(unittest.TestCase):
    def test_grid_cover_expands_a_one_pixel_crack_and_partial_edge_blocks(self):
        mask = np.zeros((19, 22), dtype=bool)
        mask[10, 2:13] = True
        mask[18, 21] = True
        expected = np.zeros_like(mask)
        expected[8:16, :16] = True
        expected[16:, 16:] = True
        np.testing.assert_array_equal(grid_cover(mask), expected)

    def test_512_hides_the_whole_grid_block_and_keeps_the_original_composite(self):
        reference = np.full((512, 512, 3), 113, dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=bool)
        mask[10, 19] = True
        expanded = np.zeros_like(mask)
        expanded[8:16, 16:24] = True

        def model(damaged, inference_mask, seed):
            self.assertEqual(seed, 42)
            np.testing.assert_array_equal(inference_mask, expanded)
            self.assertTrue(np.all(damaged[expanded] == 0))
            np.testing.assert_array_equal(damaged[~expanded], reference[~expanded])
            return np.full_like(damaged, 217)

        result = aligned_prediction(model, reference, mask, 42)
        self.assertTrue(np.all(result[mask] == 217))
        np.testing.assert_array_equal(result[~mask], reference[~mask])
        self.assertTrue(np.all(reference == 113))

        expanded[:] = False
        expanded[8:12, 16:20] = True
        result = aligned_prediction(model, reference, mask, 42, stride=4)
        self.assertTrue(np.all(result[mask] == 217))
        np.testing.assert_array_equal(result[~mask], reference[~mask])

    def test_1024_has_no_bicubic_leakage_or_outside_hole_generation(self):
        first = np.full((512, 512, 3), 113, dtype=np.uint8)
        second = first.copy()
        second[8:12, 16:20] = [255, 0, 197]
        mask = np.zeros((512, 512), dtype=bool)
        mask[10, 19] = True
        expanded = np.zeros((1024, 1024), dtype=bool)
        expanded[16:24, 32:40] = True

        masked_source = first.copy()
        masked_source[8:12, 16:20] = 0
        context = np.array(Image.fromarray(masked_source).resize((1024, 1024), Image.Resampling.BICUBIC))
        expected_input = context.copy()
        expected_input[expanded] = 0
        context[expanded] = 217
        expected = np.array(Image.fromarray(context).resize((512, 512), Image.Resampling.BICUBIC))

        for reference, outside in ((first, 20), (second, 180)):
            with self.subTest(outside=outside):
                def model(damaged, inference_mask, seed):
                    np.testing.assert_array_equal(inference_mask, expanded)
                    np.testing.assert_array_equal(damaged, expected_input)
                    prediction = np.full_like(damaged, outside)
                    prediction[expanded] = 217
                    return prediction

                result = aligned_prediction(model, reference, mask, 42, inference_size=1024)
                np.testing.assert_array_equal(result[mask], expected[mask])
                np.testing.assert_array_equal(result[~mask], reference[~mask])

    def test_unaligned_1024_control_uses_the_nearest_mask(self):
        reference = np.full((512, 512, 3), 113, dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=bool)
        mask[10, 19] = True
        expected = np.repeat(np.repeat(mask, 2, axis=0), 2, axis=1)

        def model(damaged, inference_mask, seed):
            np.testing.assert_array_equal(inference_mask, expected)
            self.assertTrue(np.all(damaged[expected] == 0))
            return damaged

        result = aligned_prediction(model, reference, mask, 42, inference_size=1024, align=False)
        np.testing.assert_array_equal(result[~mask], reference[~mask])

    def test_rejects_wrong_image_mask_and_prediction_types(self):
        reference = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=bool)

        def invalid_output(damaged, inference_mask, seed):
            return damaged.astype(np.float32)

        with self.assertRaises(ValueError):
            grid_cover(mask.astype(np.uint8))
        with self.assertRaises(ValueError):
            aligned_prediction(invalid_output, reference[:, :511], mask, 42)
        with self.assertRaises(ValueError):
            aligned_prediction(invalid_output, reference, mask[:511], 42)
        with self.assertRaises(ValueError):
            aligned_prediction(invalid_output, reference, mask, 42)


if __name__ == "__main__":
    unittest.main()
