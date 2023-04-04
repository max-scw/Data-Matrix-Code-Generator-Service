import treepoem
import uuid
import pathlib as pl
from typing import List, Union, Dict, Any
from PIL import Image, EpsImagePlugin
import warnings
import sys

from DMCText import DMCMessageBuilder
# mm to point conversion: 2.8346 pt per mm


class DMCGenerator:
    def __init__(self, message: Union[str, List[str]] = None, modul_size_pt: int = 4) -> None:
        self.message = ''.join([c for c in message if c.isascii()])
        self.n_compressed_ascii_chars = self.count_compressed_ascii_characters(self.message)
        self.modul_size_pt = modul_size_pt

    def __repr__(self):
        return f"DMCGenerator({self.message}"

    @staticmethod
    def tuple_subtract(t1: tuple, t2: tuple) -> tuple:
        return tuple(map(lambda i, j: i - j, t1, t2))

    @staticmethod
    def tuple_add(t1: tuple, t2: tuple) -> tuple:
        return tuple(map(lambda i, j: i + j, t1, t2))

    @staticmethod
    def tuple_multiply(t1: tuple, factor: Union[int, float]) -> tuple:
        return tuple(map(lambda i: factor * i, t1))

    def generate(self,
                 n_quiet_zone_moduls: Union[int, None] = None,
                 use_rectangular: bool = False,
                 file_path: Union[str, pl.Path, None] = None
                 ) -> Union[Image.Image, pl.Path]:
        # options Barcode Writer in Pure Postscript (BWIPP)
        # https://github.com/bwipp/postscriptbarcode/wiki/Data-Matrix
        # TODO: how to specify the modul size in pts?

        if use_rectangular:
            barcode_type = 'datamatrixrectangularextension'
            options = {'version': self.compact_rectangular_dmc_format()}
        else:
            barcode_type = 'datamatrix'
            options = None
        # create Data-Matrix-Code and convert image to binary black/white pixels (using pillow PIL)
        dmc_image = treepoem.generate_barcode(barcode_type=barcode_type,
                                              data=self.message,
                                              options=options
                                              ).convert('1')
        # add quiet zone for final image of the code
        img = self.add_quiet_zone(dmc_image, n_quiet_zone_moduls)

        if file_path is None:
            return img
        else:
            return self.save_image(img, file_path)

    @staticmethod
    def save_image(img: Image.Image, file_path: Union[str, pl.Path] = None) -> pl.Path:
        # current working directory as default input
        if file_path is None:
            file_path = pl.Path().cwd()

        if file_path.is_dir():
            # generate random file name
            filename = str(uuid.uuid4())
            file_path /= filename

        # get/check extension
        if file_path.suffix == '':
            file_path = file_path.with_suffix(".png")

        # save image
        img.save(file_path)
        return file_path

    def compact_rectangular_dmc_format(self):
        # determine most compact rectangular format

        binary_capacity = [3, 8, 14, 20, 30, 47, 54, 70, 78]
        height = [8, 8, 12, 12, 16, 16, 20, 20, 22, 24]
        width = [18, 32, 26, 36, 36, 48, 44, 48, 48]
        # original
        # binary_capacity = [3, 8, 14, 20, 30, 47]
        # height = [8, 8, 12, 12, 16, 16]
        # length = [18, 32, 26, 36, 36, 48]
        n_rows, n_cols = 0, 0
        for cap, n_rows, n_cols in zip(binary_capacity, height, width):
            if cap >= self.n_compressed_ascii_chars:
                break
        if n_rows > 16:
            warnings.warn('Data-matrix code rectangular extended (DMRE) version used. '
                          'Not all DMC-readers can handle this shape.')

        # print(f'{n_chars} => {n_rows}x{n_cols}')
        return f'{n_rows}x{n_cols}'

    @staticmethod
    def count_compressed_ascii_characters(msg: str) -> int:
        n = 0
        last_char_was_reduced = False
        for i in range(len(msg)):
            if not last_char_was_reduced and (msg[i].isnumeric() and msg[i - 1].isnumeric()):
                last_char_was_reduced = True
            else:
                n += 1
                last_char_was_reduced = False
        return n

    @staticmethod
    def determine_modul_size_from_image(img: Image) -> int:
        # find starting point / starting offset
        offset = 0
        for i in range(min(img.size)):
            if img.getpixel((i, i)) != 255:  # white
                offset = i
                break

        # find first switch between black and white
        modul_size = 0
        for i in range(img.width - offset):
            if img.getpixel((offset + i, offset)) != 0:  # black
                modul_size = i
                break

        return modul_size

    def add_quiet_zone(self, img: Image.Image, n_quiet_zone_moduls: int = 2) -> Image.Image:
        # add quiet zone (pad image)
        if n_quiet_zone_moduls:
            # size in pt
            sz_quiet_zone = int(n_quiet_zone_moduls * self.modul_size_pt)
            # create empty, larger image
            quiet_zone_size = (sz_quiet_zone, sz_quiet_zone)
            new_image_size = self.tuple_add(img.size, self.tuple_multiply(quiet_zone_size, 2))
            # print(new_image_size)
            img_pad = Image.new('1', new_image_size, (255,))
            # add dmc to empty, larger image
            coordinates = quiet_zone_size + self.tuple_add(img.size, quiet_zone_size)
            img_pad.paste(img, coordinates)
        else:
            img_pad = img
        return img_pad


if __name__ == "__main__":
    if sys.platform.startswith("win") and EpsImagePlugin.gs_windows_binary is False:
        # This is a workaround if pillow cannot find ghostscript
        path_to_gs = pl.Path(r"C:\Program Files\gs")
        if path_to_gs.exists():
            # folder is named to ghostscript version
            path_to_gs = list(path_to_gs.glob("gs*"))[0] / "bin"
            # find if 86 / 64-bit version is installed
            path_to_gs = list(path_to_gs.glob("gswin*c.exe"))[0]
        EpsImagePlugin.gs_windows_binary = path_to_gs / path_to_gs
    # TODO: strip point in material number

    message_string = DMCMessageBuilder({"S": 123456, "V": "123H48999"}).get_message_string(use_message_envelope=True, use_format_envelope=False)
    img = DMCGenerator(message_string).generate(use_rectangular=False)
    img.show()
    img = DMCGenerator(message_string).generate(use_rectangular=True)
    img.show()
