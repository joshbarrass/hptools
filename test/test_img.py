import unittest
import os

from PIL import Image

import img

test_dir = os.path.dirname(__file__)

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

    def test_convert_IMG(self):
        orig_im = Image.open(os.path.join(test_dir, "test.tif")).convert("RGB")
        im = img.convert_IMG(img.read_IMG(os.path.join(test_dir, "test.testimg")), orig_im.size)

        self.assertEqual(im.size, orig_im.size)

        im_pix = im.load()
        orig_pix = orig_im.load()
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                self.assertEqual(im_pix[x,y], orig_pix[x,y])
