# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import io
import base64
import importlib.resources
import mimetypes
import tempfile
import pathlib

import jinja2
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer


def _material_icon(name):
    return f'<span class="material-icons">{name}</span>'


def _make_qrcode(data):
    bio = io.BytesIO()
    qr = qrcode.QRCode()
    qr.add_data(data)
    img = qr.make_image(
        image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer()
    )
    img.save(bio, format="png")
    encoded = base64.b64encode(bio.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _file_to_data_url(filename):
    content_type, _ = mimetypes.guess_type(filename)
    with open(filename, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("utf-8")

    return f"data:{content_type};base64,{encoded}"


template = jinja2.Template(
    importlib.resources.read_text("wintertools.reportcard", "template.html")
)
template.globals["make_qrcode"] = _make_qrcode
template.globals["material_icon"] = _material_icon


with importlib.resources.path("wintertools.reportcard", "logo.svg") as src:
    template.globals["logo"] = _file_to_data_url(src)


def render_html(report, file=None):
    output = template.render(report=report)

    if isinstance(file, (str, pathlib.Path)):
        with open(file, "w") as fh:
            fh.write(output)
    elif file:
        file.write(output)

    return output


def render_image(report, file=None):
    with tempfile.NamedTemporaryFile as html_fh:
        render_html(report, file=html_fh)
        print(html_fh.name)

    # TODO: https://github.com/pyppeteer/pyppeteer
