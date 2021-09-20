# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from wintertools.affinity2kicad.bitmap2component import bitmap2component
from wintertools import tui
import itertools
import concurrent.futures
import os.path

LAYERS = {
    "FSilkS": "F.SilkS",
    "BSilkS": "B.SilkS",
    "FCu": "F.Cu",
    "BCu": "B.Cu",
    "FMask": "F.Mask",
    "BMask": "B.Mask",
}


class Converter:
    def __init__(self, doc, pcb):
        self.doc = doc
        self.pcb = pcb
        self.bbox = (0, 0, 0, 0)
        self._tmpdir = os.path.join(".", ".cache")
        os.makedirs(self._tmpdir, exist_ok=True)

    def convert(self, drills=True, layers=True):
        self.convert_outline()
        if drills:
            self.convert_drills()
        if layers:
            self.convert_layers()

    def convert_outline(self):
        rects = list(self.doc.query_all("#EdgeCuts rect"))

        if not rects:
            raise ValueError("No rect on EdgeCuts.")

        # First, find the largest rectangle. That one is our outline.
        bbox = [0, 0, 0, 0]

        for rect in rects:
            x = self.doc.to_mm(rect.get("screen_x"), 1)
            y = self.doc.to_mm(rect.get("screen_y"), 1)
            width = self.doc.to_mm(rect.get("screen_width"), 1)
            height = self.doc.to_mm(rect.get("screen_height"), 1)
            if width * height > bbox[2] * bbox[3]:
                bbox = [x, y, width, height]

        if bbox[0] != 0 or bbox[1] != 0:
            raise ValueError("Edge.Cuts x,y is not 0,0.")

        self.bbox = (
            self.pcb.page_width / 2 - bbox[2],
            self.pcb.page_height / 2 - bbox[3] / 2,
            bbox[2],
            bbox[3],
        )

        print(f"Outline is {bbox[2]:.2f} mm x {bbox[3]:.2f} mm.")

        # Now that the PCB offset is known, we can start building the PCB.
        self.pcb.offset = self.bbox[:2]
        self.pcb.start()
        self.pcb.add_horizontal_measurement(0, 0, self.bbox[2], 0)
        self.pcb.add_vertical_measurement(0, 0, 0, self.bbox[3])

        # Draw all of the rects onto the PCB
        for rect in rects:
            x = self.doc.to_mm(rect.get("screen_x"), 1)
            y = self.doc.to_mm(rect.get("screen_y"), 1)
            width = self.doc.to_mm(rect.get("screen_width"), 1)
            height = self.doc.to_mm(rect.get("screen_height"), 1)
            self.pcb.add_outline(x, y, width, height)
            print(
                f"Added {width:.1f} mm x {height:.1f} mm rectangle to Edge.Cuts at ({x:.1f} mm, {y:.1f} mm)."
            )

    def convert_drills(self):
        circles = list(self.doc.query_all("#Drill circle"))

        for el in circles:
            x = self.doc.to_mm(el.get("screen_cx"))
            y = self.doc.to_mm(el.get("screen_cy"))
            d = self.doc.to_mm(float(el.get("screen_r")) * 2)

            self.pcb.add_drill(x, y, d)

        print(f"Converted {len(circles)} drills.")

    def convert_layers(self):
        columns = tui.Columns(*["<10"] * len(LAYERS))
        columns.draw(*LAYERS.keys())
        results = [((0.4, 0.4, 0.4), "...") for _ in LAYERS]

        with concurrent.futures.ProcessPoolExecutor() as executor, tui.Updateable() as updateable:
            futures = [
                executor.submit(convert_layer, self.doc, self._tmpdir, src, dst)
                for src, dst in LAYERS.items()
            ]

            columns.draw(*itertools.chain(*results))
            updateable.update()

            for n, f in enumerate(concurrent.futures.as_completed(futures)):
                mod = f.result()

                if mod:
                    mod, cached = mod
                    self.pcb.add_mod(
                        mod, self.centroid[0], self.centroid[1], relative=False
                    )
                    if cached:
                        results[n] = ((0.5, 0.5, 1.0), "cached")
                    else:
                        results[n] = ((0.5, 1.0, 0.5), "done")
                else:
                    results[n] = ((0.4, 0.4, 0.4), "empty")

                columns.draw(*itertools.chain(*results))
                updateable.update()

    @property
    def centroid(self):
        return self.bbox[0] + (self.bbox[2] / 2), self.bbox[1] + (self.bbox[3] / 2)


def convert_layer(doc, tmpdir, src_layer_name, dst_layer_name):
    svg_filename = os.path.join(tmpdir, f"output-{dst_layer_name}.svg")
    png_filename = os.path.join(tmpdir, f"output-{dst_layer_name}.png")
    mod_filename = os.path.join(tmpdir, f"output-{dst_layer_name}.kicad_mod")

    doc = doc.copy()

    if not doc.remove_layers(keep=src_layer_name):
        return

    doc.recolor(src_layer_name)
    svg_text = doc.tostring()

    # See if the cached layer hasn't changed, if so, don't bother re-rendering.
    if os.path.exists(mod_filename) and os.path.exists(svg_filename):
        with open(svg_filename, "r") as fh:
            cached_svg_text = fh.read()

        if svg_text.strip() == cached_svg_text.strip():
            return mod_filename, True

    # No cached version, so render it and convert it.
    with open(svg_filename, "w") as fh:
        fh.write(svg_text)

    doc.render(png_filename)
    bitmap2component(
        src=png_filename,
        dst=mod_filename,
        layer=dst_layer_name,
        invert=True,
        dpi=doc.dpi,
    )

    return mod_filename, False
