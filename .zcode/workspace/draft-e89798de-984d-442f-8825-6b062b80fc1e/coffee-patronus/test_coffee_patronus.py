"""Tests for the procedural coffee patronus renderer. Run with: python -m unittest"""
import unittest

import numpy as np

import coffee_patronus as cp

SMALL = dict(scale=0.25, quality=0.3)


def luminance(img):
    return img.astype(np.float64).mean(axis=2)


class NoiseTests(unittest.TestCase):
    def setUp(self):
        self.lat = cp.make_lattice(3)
        rng = np.random.default_rng(0)
        self.x = rng.uniform(3.0, 40.0, 4000)
        self.y = rng.uniform(3.0, 40.0, 4000)

    def test_perlin_is_bounded_and_centred(self):
        n = cp.perlin_d(self.x, self.y, self.lat)[0]
        self.assertLess(np.abs(n).max(), 1.0)
        self.assertLess(abs(n.mean()), 0.05)

    def test_perlin_derivatives_match_finite_differences(self):
        _, nx, ny = cp.perlin_d(self.x, self.y, self.lat)
        h = 1e-5
        value = lambda x, y: cp.perlin_d(x, y, self.lat)[0]
        fd_x = (value(self.x + h, self.y) - value(self.x - h, self.y)) / (2 * h)
        fd_y = (value(self.x, self.y + h) - value(self.x, self.y - h)) / (2 * h)
        self.assertLess(np.abs(nx - fd_x).max(), 1e-5)
        self.assertLess(np.abs(ny - fd_y).max(), 1e-5)

    def test_fbm_is_bounded(self):
        self.assertLess(np.abs(cp.fbm(self.x, self.y, self.lat, 4)).max(), 1.0)


class RasterTests(unittest.TestCase):
    def test_deposit_conserves_weight_and_drops_outside_points(self):
        buf = np.zeros((20, 30))
        cp.deposit(buf, [5.3, 12.7, -4.0, 35.0, 12.2], [4.2, 18.1, 3.0, 10.0, -3.0], [1.0, 2.0, 5.0, 7.0, 9.0])
        self.assertAlmostEqual(buf.sum(), 3.0, places=9)

    def test_deposit_splits_weight_between_neighbouring_pixels(self):
        buf = np.zeros((4, 4))
        cp.deposit(buf, [1.5], [1.5], [1.0])
        self.assertAlmostEqual(buf[1, 1], 0.25, places=9)
        self.assertAlmostEqual(buf[2, 2], 0.25, places=9)
        self.assertAlmostEqual(buf.sum(), 1.0, places=9)

    def test_deposit_broadcasts_scalar_weight(self):
        buf = np.zeros((4, 4))
        cp.deposit(buf, [[1.0, 2.0], [1.0, 2.0]], [[1.0, 1.0], [2.0, 2.0]], 0.5)
        self.assertAlmostEqual(buf.sum(), 2.0, places=9)

    def test_gaussian_blur_keeps_energy_for_a_point_source(self):
        img = np.zeros((500, 500))
        img[250, 250] = 1.0
        for sigma in (3.0, 60.0):
            with self.subTest(sigma=sigma):
                out = cp.gaussian_blur(img, sigma)
                # edge padding adds a little mass for wide kernels, hence the 1% tolerance
                self.assertAlmostEqual(out.sum(), 1.0, delta=0.01)
                # the block down/upsample may shift wide kernels by one pixel
                peak = np.unravel_index(out.argmax(), out.shape)
                self.assertLessEqual(max(abs(peak[0] - 250), abs(peak[1] - 250)), 1)

    def test_spline_passes_through_control_points_with_even_spacing(self):
        ctrl = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [200.0, 100.0]])
        curve = cp.spline_curve(ctrl, 1.0)
        for p in ctrl:
            self.assertLess(np.hypot(*(curve - p).T).min(), 0.6)
        spacing = np.hypot(*np.diff(curve, axis=0).T)
        self.assertLess(spacing.max(), 1.02)
        self.assertGreater(spacing.min(), 0.5)

    def test_ribbon_curl_bulges_sideways_and_reaches_the_tail(self):
        rng = np.random.default_rng(0)
        pts = cp.ribbon_points(rng, (0.0, 0.0), [("w", 0.0, 100.0), ("l", 40.0, 1, 1.0), ("w", 0.0, 200.0)])
        self.assertEqual(pts.shape[1], 2)
        self.assertGreater(np.abs(pts[:, 0]).max(), 40.0)      # a straight route would stay at x = 0
        self.assertAlmostEqual(pts[-1, 1], 200.0, delta=1.0)


class GeometryTests(unittest.TestCase):
    def test_cup_body_covers_the_wall_but_not_the_opening(self):
        g = cp.Geometry(270, 480)
        X, Y = cp.pixel_grid(g)
        cover = cp.cup_body_coverage(g, X, Y)
        self.assertAlmostEqual(cover[int(g.ytop + 0.5 * g.Hc * g.ce), int(g.cx)], 1.0, places=6)
        self.assertAlmostEqual(cover[int(g.ytop - 0.5 * g.R * g.se), int(g.cx)], 0.0, places=6)
        self.assertEqual(cover[5, 5], 0.0)
        self.assertEqual(cover[-5, -5], 0.0)

    def test_surface_projects_the_front_of_the_rim_below_its_centre(self):
        g = cp.Geometry(270, 480)
        back = g.surface(np.array([1.5 * np.pi]), np.array([1.0]))
        front = g.surface(np.array([0.5 * np.pi]), np.array([1.0]))
        self.assertGreater(front[2], 0.0)
        self.assertLess(back[2], 0.0)
        self.assertGreater(front[1], g.ytop)
        self.assertLess(back[1], g.ytop)


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blue = cp.render("blue", **SMALL)
        cls.mixed = cp.render("mixed", **SMALL)
        cls.coffee = cp.render("coffee", **SMALL)
        cls.g = cp.Geometry(cls.blue.shape[1], cls.blue.shape[0])

    def test_output_is_uint8_rgb_of_the_requested_size(self):
        self.assertEqual(self.blue.shape, (480, 270, 3))
        self.assertEqual(self.blue.dtype, np.uint8)

    def test_render_is_deterministic_for_a_seed(self):
        self.assertTrue(np.array_equal(self.blue, cp.render("blue", **SMALL)))

    def test_rim_and_coffee_surface_are_lit_while_corners_stay_dark(self):
        lum = luminance(self.blue)
        g = self.g
        rim = lum[int(g.ytop), int(g.cx - g.R)]
        surface = lum[int(g.ytop), int(g.cx)]
        corner = min(lum[:20, :20].max(), lum[:20, -20:].max(), lum[-20:, :20].max(), lum[-20:, -20:].max())
        self.assertLess(corner, 30.0)
        self.assertGreater(rim, corner + 20.0)
        self.assertGreater(surface, corner + 20.0)

    def test_every_palette_lights_the_cup_above_the_background(self):
        for img in (self.blue, self.mixed, self.coffee):
            lum = luminance(img)
            g = self.g
            box = lum[int(g.ytop - 0.3 * g.R):int(g.ytop + g.Hc), int(g.cx - 0.9 * g.R):int(g.cx + 0.9 * g.R)]
            self.assertGreater(box.mean(), luminance(img)[:40, :40].mean() * 3.0 + 10.0)

    def test_blue_palette_is_cold_and_coffee_palette_is_warm(self):
        g = self.g
        box = (slice(int(g.ytop - 2.0 * g.R), int(g.ytop + g.Hc)), slice(int(g.cx - g.R), int(g.cx + g.R)))
        warm_rgb = self.coffee[box].reshape(-1, 3).mean(axis=0)
        cold_rgb = self.blue[box].reshape(-1, 3).mean(axis=0)
        # the ramps converge to near-white at the top, so compare the averages with a modest margin
        self.assertGreater(cold_rgb[2] / cold_rgb[0], 1.25)    # B / R of the blue ramp
        self.assertGreater(warm_rgb[0] / warm_rgb[2], 1.25)    # R / B of the coffee ramp
        self.assertFalse(np.array_equal(self.blue, self.coffee))
        self.assertFalse(np.array_equal(self.blue, self.mixed))


if __name__ == "__main__":
    unittest.main()
