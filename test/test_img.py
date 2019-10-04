import unittest
import os
import shutil, tempfile

from PIL import Image

import img

test_dir = os.path.dirname(__file__)

class ImgTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

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
        self.assertImagesAreEqual(im, orig_im)

    def test_convert_palette_IMG(self):
        orig_im = Image.open(os.path.join(test_dir, "test.tif")).convert("RGB")
        im = img.convert_palette_IMG(img.read_IMG(os.path.join(test_dir, "test.testpimg")), orig_im.size).convert("RGB")
        self.assertImagesAreEqual(im, orig_im)

    def assertImagesAreEqual(self, im1, im2):
        self.assertEqual(im1.size, im2.size)

        im1_pix = im1.load()
        im2_pix = im2.load()
        for y in range(im1.size[1]):
            for x in range(im1.size[0]):
                self.assertEqual(im1_pix[x,y], im2_pix[x,y])

    def test_convert_to_IMG(self):
        im = Image.open(os.path.join(test_dir, "test.tif"))
        img.convert_to_IMG(im, os.path.join(self.temp_dir, "new.img"))
        self.assertFilesAreEqual(os.path.join(test_dir, "test.testimg"),
                                 os.path.join(self.temp_dir, "new.img"))

    def test_convert_to_palette_IMG(self):
        im = Image.open(os.path.join(test_dir, "test.tif"))
        img.convert_to_palette_IMG(im, os.path.join(self.temp_dir, "new.img"))
        self.assertFilesAreEqual(os.path.join(test_dir, "test.testpimg"),
                                 os.path.join(self.temp_dir, "new.img"))

    def assertFilesAreEqual(self, fp1, fp2, chunksize=4096):
        # check file sizes
        self.assertEqual(os.path.getsize(fp1), os.path.getsize(fp2))

        with open(fp1, "rb") as f1:
            with open(fp2, "rb") as f2:
                data1 = b"."
                data2 = b"."
                while data1 != b"": # don't need to check both since they're same size
                    data1 = f1.read(chunksize)
                    data2 = f2.read(chunksize)
                    self.assertEqual(data1, data2)
