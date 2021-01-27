import unittest

from sot.bbox import BBox


class TestBBox(unittest.TestCase):
    def setUp(self) -> None:
        self.bbox = BBox(10, 20, 300, 400)
    
    def test_negative_width(self):
        with self.assertRaises(AssertionError):
            BBox(100, 100, -10, 200)
    
    def test_negative_height(self):
        with self.assertRaises(AssertionError):
            BBox(100, 100, 10, -200)
    
    def test_center(self):
        self.assertEqual(self.bbox.center.tolist(), [160, 220])
    
    def test_size(self):
        self.assertEqual(self.bbox.size.tolist(), [300, 400])
    
    def test_corners_calculation(self):
        self.assertEqual(self.bbox.as_corners().tolist(), [10, 20, 310, 420])
    
    def test_x_y_width_height_calculation(self):
        self.assertEqual(self.bbox.as_xywh().tolist(), [10, 20, 300, 400])
    
    def test_negative_width_scale_factor(self):
        with self.assertRaises(AssertionError):
            self.bbox.rescale(-0.5, 2)
    
    def test_negative_height_scale_factor(self):
        with self.assertRaises(AssertionError):
            self.bbox.rescale(0.5, -2)
    
    def test_upscale_twice(self):
        scale = 2
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=False)
        
        self.assertEqual(bbox_rescaled.size.tolist(), [600, 800])
    
    def test_downscale_twice(self):
        scale = 0.5
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=False)
        
        self.assertEqual(bbox_rescaled.size.tolist(), [150, 200])
    
    def test_no_scale_change(self):
        scale = 1
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=False)
        
        self.assertEqual(bbox_rescaled.size.tolist(), [300, 400])

    def test_upscale_twice_inplace(self):
        scale = 2
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=True)
        
        self.assertTrue(bbox_rescaled is None)
        self.assertEqual(self.bbox.size.tolist(), [600, 800])

    def test_downscale_twice_inplace(self):
        scale = 0.5
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=True)
        
        self.assertTrue(bbox_rescaled is None)
        self.assertEqual(self.bbox.size.tolist(), [150, 200])

    def test_no_scale_change_inplace(self):
        scale = 1
        bbox_rescaled = self.bbox.rescale(scale, scale, in_place=True)
        
        self.assertTrue(bbox_rescaled is None)
        self.assertEqual(self.bbox.size.tolist(), [300, 400])
    
    def test_repr(self):
        self.assertEqual(self.bbox.__repr__(), 'BBox(10,20,300,400)')
        

if __name__ == '__main__':
    unittest.main()