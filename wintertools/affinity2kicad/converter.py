# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from wintertools.affinity2kicad.bitmap2component import bitmap2component
import os.path
import multiprocessing

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
        print("Converting outline.")
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
            print(f"Added rect to Edge.Cuts ({x:.1f}, {y:.1f}, {width:.1f}, {height:.1f}).")

    def convert_drills(self):
        print("Converting drills.")

        circles = list(self.doc.query_all("#Drill circle"))

        for el in circles:
            x = self.doc.to_mm(el.get("screen_cx"))
            y = self.doc.to_mm(el.get("screen_cy"))
            d = self.doc.to_mm(float(el.get("screen_r")) * 2)

            self.pcb.add_drill(x, y, d)

        print(f"Converted {len(circles)} drills.")

    def convert_layers(self):
        print("Converting cosmestic layers.")
        p = multiprocessing.Pool()

        with p:
            mods = p.starmap(
                convert_layer,
                [(self.doc, self._tmpdir, src, dst) for src, dst in LAYERS.items()],
            )

        for mod in filter(None, mods):
            self.pcb.add_mod(mod, self.centroid[0], self.centroid[1], relative=False)

    @property
    def centroid(self):
        return self.bbox[0] + (self.bbox[2] / 2), self.bbox[1] + (self.bbox[3] / 2)


def convert_layer(doc, tmpdir, src_layer_name, dst_layer_name):
    png_filename = os.path.join(tmpdir, f"output-{dst_layer_name}.png")
    mod_filename = os.path.join(tmpdir, f"output-{dst_layer_name}.kicad_mod")
    layers = list(LAYERS.keys()) + ["EdgeCuts", "Drill"]

    if not doc.hide_all_layers(ids=layers, but=src_layer_name):
        print(f"Layer {src_layer_name} not found.")
        return

    print(f"Rendering {dst_layer_name}.")

    doc.recolor(src_layer_name)
    doc.render(png_filename)

    # For debugging, write out the SVG for the layer as well.
    with open(os.path.join(tmpdir, f"output-{dst_layer_name}.svg"), "w") as fh:
        fh.write(doc.tostring().decode("utf-8"))

    bitmap2component(
        src=png_filename,
        dst=mod_filename,
        layer=dst_layer_name,
        invert=True,
        dpi=doc.dpi,
    )

    print(f"Converted {dst_layer_name}.")

    return mod_filename
