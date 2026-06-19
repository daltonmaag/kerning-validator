from __future__ import annotations

import argparse
import io
import itertools
from collections import defaultdict
from pathlib import Path

import uharfbuzz as hb
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib import TTFont
from fontTools.ufoLib.kerning import lookupKerningValue
from fontTools.unicodedata import (
    bidirectional,
    script as primary_script,
    script_horizontal_direction,
)
from ufo2ft.util import DFLT_SCRIPTS, classifyGlyphs
from ufoLib2 import Font
from tqdm import tqdm

RTL_BIDI_TYPES = {"R", "AL"}
LTR_BIDI_TYPES = {"L", "AN", "EN"}
AMBIGUOUS_BIDIS = {"R", "L"}

# GID_PREFIX is an arbitrary value > U+10FFF to shift codepoints by, to avoid
# HarfBuzz doing any processing on them.
GID_PREFIX = 0x80000000


def get_glyph_id(font: hb.Font, codepoint: int, user_data: None) -> int:
    """Return the glyph ID for a codepoint, where the codepoint is actually the
    GID_PREFIX + glyph ID according to the font's glyph order.

    This makes it possible to select glyphs by just their glyph ID instead of
    replicating the logic to shape from Unicode codepoints to glyph ID.

    NOTE: This returns ID 0 (.notdef) for all codepoints we didn't prepare
    ourselves, hopefully no designer kerned .notdef against anything.
    """
    if codepoint >= GID_PREFIX:
        return codepoint - GID_PREFIX
    return 0


def unicodeBidiType(uv):
    """Return "R" for characters with RTL direction, or "L" for LTR (whether
    'strong' or 'weak'), or None for neutral direction.
    """
    char = chr(uv)
    bidiType = bidirectional(char)
    if bidiType in RTL_BIDI_TYPES:
        return "R"
    elif bidiType in LTR_BIDI_TYPES:
        return "L"
    else:
        return None


GlyphProperties = dict[str, str]


def classify_glyphs(
    font: TTFont, designspace: DesignSpaceDocument
) -> tuple[GlyphProperties, GlyphProperties]:
    cmap = font.getBestCmap()
    gsub = font.get("GSUB")

    extraSubstitutions = defaultdict(set)
    for rule in designspace.rules:
        for left, right in rule.subs:
            extraSubstitutions[left].add(right)

    scripts: dict[str, set[str]] = classifyGlyphs(
        primary_script, cmap, gsub, extraSubstitutions
    )
    glyph_scripts = {
        name: script for script, glyphs in scripts.items() for name in glyphs
    }

    bidis: dict[str, set[str]] = classifyGlyphs(
        unicodeBidiType, cmap, gsub, extraSubstitutions
    )
    glyph_bidis = {name: bidi for bidi, glyphs in bidis.items() for name in glyphs}

    return glyph_scripts, glyph_bidis


parser = argparse.ArgumentParser()
parser.add_argument("designspace", type=DesignSpaceDocument.fromfile)
parser.add_argument("font", type=Path)
parsed_args = parser.parse_args()

designspace: DesignSpaceDocument = parsed_args.designspace
name2tag = {a.name: a.tag for a in designspace.axes}
name2axis = {a.name: a for a in designspace.axes}
designspace.loadSourceFonts(Font.open)
default_source = designspace.findDefault()

font = TTFont(parsed_args.font)
glyph_order = font.getGlyphOrder()
glyph_id: dict[str, int] = {v: k + GID_PREFIX for k, v in enumerate(glyph_order)}
gid_range = range(len(glyph_order))
glyph2script, glyph2bidi = classify_glyphs(font, designspace)

# Drop the GSUB table now to stop HarfBuzz from applying any substitutions
# later in the comparison loop. It must only use what it's given.
if "GSUB" in font:
    del font["GSUB"]

font_blob = io.BytesIO()
font.save(font_blob)
buf = io.BytesIO(font_blob.getvalue())
face = hb.Face(buf.getvalue())
hb_advance_width: int = face.upem

pairs = []
for first_name, second_name in itertools.product(glyph_order, glyph_order):
    first_bidi = glyph2bidi.get(first_name)
    second_bidi = glyph2bidi.get(second_name)
    bidis = {first_bidi, second_bidi}
    if bidis == AMBIGUOUS_BIDIS:
        continue  # TODO: This probably skips RTL kerning against numbers
    pairs.append((first_name, second_name))

for source in designspace.sources:
    if source.layerName is not None:
        continue  # Intermediate sources provide no kerning.

    assert source.font
    kerning = source.font.kerning
    groups = source.font.groups
    glyphToFirstGroup = {}
    glyphToSecondGroup = {}
    for group, groupMembers in groups.items():
        if group.startswith("public.kern1."):
            for glyph in groupMembers:
                glyphToFirstGroup[glyph] = group
        elif group.startswith("public.kern2."):
            for glyph in groupMembers:
                glyphToSecondGroup[glyph] = group

    user_location = designspace.map_backward(source.location)
    user_location = {name2tag[k]: v for k, v in user_location.items()}

    hb_font = hb.Font(face)
    funcs = hb.FontFuncs()
    funcs.set_nominal_glyph_func(get_glyph_id, None)
    hb_font.funcs = funcs
    hb_font.set_variations(user_location)

    print("Checking", user_location)
    buffer = hb.Buffer()
    for first_name, second_name in tqdm(pairs):
        expected = lookupKerningValue(
            (first_name, second_name),
            kerning,
            groups,
            glyphToFirstGroup=glyphToFirstGroup,
            glyphToSecondGroup=glyphToSecondGroup,
        )

        first_script = glyph2script.get(first_name, "Zyyy")
        second_script = glyph2script.get(second_name, "Zyyy")
        scripts = {first_script, second_script}
        if first_script == second_script:
            script = first_script
        elif first_script in DFLT_SCRIPTS:
            script = second_script
        elif second_script in DFLT_SCRIPTS:
            script = first_script
        else:
            script = first_script
        direction = script_horizontal_direction(script, "LTR")

        buffer.clear_contents()
        first_gid, second_gid = glyph_id[first_name], glyph_id[second_name]
        buffer.add_codepoints([first_gid, second_gid])
        buffer.script = script
        buffer.direction = direction
        hb.shape(hb_font, buffer, None)

        # Sanity checks to ensure HarfBuzz doesn't do unexpected substitutions.
        # The returned buffer is ready for LTR rendering, so RTL glyphs are
        # stored "backwards" with advance widths reversed.
        shaped_names = [
            i.codepoint
            for i in (
                buffer.glyph_infos
                if direction == "LTR"
                else reversed(buffer.glyph_infos)
            )
        ]
        assert shaped_names == [first_gid - GID_PREFIX, second_gid - GID_PREFIX]

        glyph_positions = buffer.glyph_positions
        actual: int = (
            glyph_positions[0].x_advance
            + glyph_positions[1].x_advance
            - 2 * hb_advance_width
        )
        if actual != expected:
            print(
                f"{source.name} ({first_name}, {second_name}): "
                f"font kerns {actual}, source resolves {expected}"
            )
        # if first_name == "period" and second_name == "Za-deva":
        #     breakpoint()
