#! /usr/bin/env python
import sys
import pathlib
from PIL import Image, ImageEnhance
import numpy as np


### DEPENDENCIES (pip requirements)
# numpy==1.21.2
# Pillow==8.3.1


def dodge(front, back):
    # formula from http://www.adobe.com/devnet/pdf/pdfs/blend_modes.pdf
    result = back*256.0/(256.0-front)
    result[result > 255] = 255
    result[front == 255] = 255
    return result.astype('uint8')


class ImageSet:

    def __init__(self, pathname) -> None:
        self.pathname = pathname
        self.metal = None
        self.occlusion = None
        self.diffuse = None
        self.emissive = None
        self.normal = None

    @property
    def img_attr(self):
        return ('metal', 'occlusion', 'diffuse', 'emissive', 'normal')

    def update_img(self, imagepath):
        image_pathtext = f"{imagepath}"
        for attr in self.img_attr:
            if attr in image_pathtext:
                setattr(self, attr, image_pathtext)

    def merge_metal(self):
        metal = Image.open(self.metal)
        occlusion = Image.open(self.occlusion)
        r, _g, b, a = metal.split()
        _r, g, _b, _a = occlusion.split()
        enhancer = ImageEnhance.Brightness(a)
        dim_a = enhancer.enhance(0.7)
        result = Image.merge('RGBA', (r, g, b, dim_a))
        output = self.metal.replace("_metal", "_mo")
        result.save(output)

    def dodge_emissions(self):
        diffuse = Image.open(self.diffuse)
        emissive = Image.open(self.emissive)
        num_dif = np.asarray(diffuse)
        num_em = np.asarray(emissive)
        num_result = dodge(num_em, num_dif)
        result = Image.fromarray(num_result)
        result.save(self.diffuse.replace("_diffuse", ""))

    def swap_normal(self):
        normal = Image.open(self.normal)
        # normal order in the tuple is red, green, blue, alpha -- RGBA
        b, a, r, g = normal.split()
        a.paste('white', [0, 0, a.size[0], a.size[1]])
        result = Image.merge('RGBA', (r, g, b, a))
        output = self.normal.replace(".png", "_swapped.png")
        result.save(output)

    def fixup(self):
        assert all([getattr(self, attr, None) for attr in self.img_attr])
        self.merge_metal()
        self.dodge_emissions()
        self.swap_normal()



def main(_j, convertpath=None, *args, **kwargs):
    while not convertpath:
        convertpath = input("Please specify the subfolder to convert: ")
    base_path = pathlib.Path(pathlib.os.path.join('.', convertpath))
    assert base_path.is_dir()
    img_groups = {}
    for dirname in base_path.glob('*'):
        if dirname.suffix or not dirname.is_dir():
            continue
        retext = f"{dirname.name}".lower().replace(" ", "_")
        rename = f"dosktastic_{retext}"
        dirname.rename(pathlib.os.path.join(base_path, rename))
    for dirname in base_path.rglob('dosktastic*'):
        if dirname.suffix or not dirname.is_dir():
            continue
        dirtext = f"{dirname.stem}"
        for objfile in dirname.rglob('*.[of]b[jx]'):
            fbxname = f"{objfile.name}"
            rename = fbxname.replace(objfile.stem, dirtext)
            objfile.rename(pathlib.os.path.join(f"{objfile.parent}", rename))
        img_groups[dirtext] = ImageSet(dirtext)
        for objfile in dirname.rglob('*.png'):
            pngname = f"{objfile.name}"
            rename = pngname.replace("THIS_MODEL", dirtext)
            newname = pathlib.os.path.join(f"{objfile.parent}", rename)
            objfile.rename(newname)
            img_groups[dirtext].update_img(newname)
    for img_set in img_groups.values():
        img_set.fixup()


if __name__ == "__main__":
    main(*sys.argv)
