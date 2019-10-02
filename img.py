"""\
Code for converting .IMG files from the Harry Potter PS1 games into usable
image files.
"""

import struct
import os
from typing import List, Tuple, Union, Optional

import numpy as np
from PIL import Image

# sizes in bytes
FULLSCREEN_SIZE = 262144
STORY_SIZE = 123392
TEXT_SIZE = 72192

# dimensions
FULLSCREEN_DIM = (512, 256)
STORY_DIM = (512, 240)
TEXT_DIM = (448, 160)

def linear_to_image_array(pixels:List[List[int]], size:Tuple[int,int]) -> np.ndarray:
    """\
Converts a linear array ( shape=(width*height, channels) ) into an array
usable by PIL ( shape=(height, width, channels) )."""
    a = np.array(pixels, dtype=np.uint8)
    split = np.split(pixels, [i*size[0] for i in range(1,size[1])])
    return np.array(split, dtype=np.uint8)

def bit_selector(number:int, start:int, end:int, normalise:bool=False) -> Union[int, float]:
    """\
Select bits between start and end. Bit 0 is the least significant bit."""
    val = (number>>start)&((2**(end-start+1))-1)
    if normalise:
        return val/((2**(end-start+1))-1)
    return val

def read_IMG(fp:str, filesize:Optional[int]=None) -> bytes:
    """\
Reads in the IMG file at fp, returning the contents as a bytes-type. If
filesize is non-None, a ValueError will be raised if the size in bytes
of the file does not match the value in filesize."""
    if filesize is not None:
        if os.path.getsize(fp) != filesize:
            raise ValueError("filesize does not match")

    with open(fp, "rb") as f:
        data = f.read()
    return data

def convert_IMG(data:bytes, size:Tuple[int,int], alpha:bool=False) -> Image.Image:
    """\
Convert a .IMG file into a PIL Image. The contents of the .IMG file
should be supplied as the bytes-type parameter 'data'. These files should
be 15-bit colour, with the first bit from left to right being the
discarded bit. This bit does change across the image, so it probably has
some purpose, but at the moment I don't know what it's for. As far as I
know, there is no metadata. Image dimensions will need to be determined
manually. The first byte from right to left is red, then green, then blue.

Set alpha=True if you want to use the discard bit as an alpha mask."""
    
    # read in the image file
##    with open(fp, "rb") as f:
##        data = f.read()

    # convert the data into a linear array of pixel values
    pixels = [] # type: List[List[int]]
    for i in range(0,len(data),2): # select two bytes at a time
        number = struct.unpack("H", data[i:i+2])[0]
        r = int(round(bit_selector(number, 0, 4, True)*255))
        g = int(round(bit_selector(number, 5, 9, True)*255))
        b = int(round(bit_selector(number, 10, 14, True)*255))
        pixel = [r,g,b]
        if alpha:
            pixel.append(int(bit_selector(number, 14, 15)*255))
        pixels.append(pixel)

    a = linear_to_image_array(pixels, size)
    img_type = "RGBA" if alpha else "RGB"
    return Image.fromarray(a, img_type)

def convert_palette_IMG(data:bytes, size:Tuple[int,int], second_palette:bool=False) -> Image.Image:
    """\
Convert a .IMG file that utilises a palette into a PIL Image. The first
512 bytes are 15-bit colours (the palette). After that, every value is
an 8-bit value that maps to the palette.

TODO: Second palette specifies whether the image has a second palette
available at the end of the file. This is used in things like the sky
images, as an "animation" palette for the lightning strike. Enabling
this will use the second palette instead of the primary palette."""

    # read in the palette
    palette = []
    for i in range(0, 512, 2):
        number = struct.unpack("H", data[i:i+2])[0]
        r = int(round(bit_selector(number, 0, 4, True)*255))
        g = int(round(bit_selector(number, 5, 9, True)*255))
        b = int(round(bit_selector(number, 10, 14, True)*255))
        colour = [r,g,b]
        palette += colour # the palette has to be flat, i.e. [r,g,b,r,g,b...]
        
    # read in the pixels
    pixels = []
    for i in range(512, len(data), 1):
        number = struct.unpack("B", data[i:i+1])[0]
        pixels.append(number)

    a = linear_to_image_array(pixels, size)
    img_type = "P"
    im = Image.fromarray(a, img_type)
    im.putpalette(palette)
    return im

def convert_fullscreen(fp:str, alpha:bool=False) -> Image.Image:
    """\
Converts an image that should occupy the whole screen. These have a file size
of 262144 bytes and dimensions of 512x256.
"""
    
    return convert_IMG(read_IMG(fp, FULLSCREEN_SIZE), FULLSCREEN_DIM, alpha)

def convert_LOAD(fp:str, alpha:bool=False) -> Image.Image:
    """\
Converts a loading screen image (LOADxx.IMG). This is an alias for
convert_fullscreen.
"""
    return convert_fullscreen(fp, alpha)

def convert_STORY(fp:str) -> Image.Image:
    """\
Converts a story image (STORYxxx.IMG).
"""
    return convert_palette_IMG(read_IMG(fp, STORY_SIZE), STORY_DIM)

def convert_TEXT(fp:str) -> Image.Image:
    """\
Converts a title text image (XX_TEXT.IMG).
"""
    return convert_palette_IMG(read_IMG(fp, TEXT_SIZE), TEXT_DIM)

def convert_to_IMG(im:Image.Image, fp:str):
    """\
Converts a PIL image into a non-palette IMG file.
"""
    # convert the IMG to RGB
    im = im.convert("RGB")

    # convert to numpy array
    a = np.array(im)
    
    # scale each channel to 5-bit
    scaled = np.round((a/255)*31).astype(np.uint8)

    # convert to raw bytes and write to file
    raw_data = b""
    for y in range(scaled.shape[0]):
        for x in range(scaled.shape[1]):
            n = scaled[y,x,2]
            n = n << 5
            n += scaled[y,x,1]
            n = n << 5
            n += scaled[y,x,0]

            raw_data += struct.pack("H", n)
            
    with open(fp, "wb") as f:
        f.write(raw_data)

def convert_to_palette_IMG(im:Image.Image, fp:str):
    """\
Converts a PIL image into a palette IMG file.
"""
    # convert the IMG to a palette
    im = im.convert("P", palette=Image.ADAPTIVE, colors=255)
    palette_bytes = im.palette.getdata()[1]
    palette = [(palette_bytes[i], palette_bytes[i+1], palette_bytes[i+2]) for i in range(0, len(palette_bytes), 3)]
    HP_palette = palette[::-1]
    
    # write the palette to the raw_data
    raw_data = b""
    for colour in HP_palette:
        n = colour[2]
        n = n << 5
        n += colour[1]
        n = n << 5
        n += colour[0]

        raw_data += struct.pack("H", n)

    # write the image to the raw_data
    pix = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            raw_data += struct.pack("B", HP_palette.index(palette[pix[x,y]]))

    with open(fp, "wb") as f:
        f.write(raw_data)
