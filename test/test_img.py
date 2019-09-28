import unittest

import img

class ImgTests(unittest.TestCase):
    def test_bit_selector(self):
        n = 0b111100101000
        self.assertEqual(img.bit_selector(n, 0, 3), 8)
        self.assertEqual(img.bit_selector(n, 4, 5), 2)
        self.assertEqual(img.bit_selector(n, 8, 11), 15)

    def test_linear_to_image_array_1D(self):
        pix = [1,2,3,4,5,6]
        a = img.linear_to_image_array(pix, (2, 3))
        self.assertEqual(a.shape, (3, 2))
        for i in range(3):
            for j in range(2):
                self.assertEqual(a[i,j], i*2+j+1)

    def test_linear_to_image_array_3D(self):
        pix = [[1,1,1], [2,2,2],
               [3,3,3], [4,4,4],
               [5,5,5], [6,6,6]]
        a = img.linear_to_image_array(pix, (2, 3))
        self.assertEqual(a.shape, (3, 2, 3))
        for i in range(3):
            for j in range(2):
                print(a[i,j])
                print(i+j+1)
                self.assertTrue(list(a[i,j]) == [2*i+j+1]*3)
