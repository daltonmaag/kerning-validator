# SPDX-FileCopyrightText: 2022-present Dalton Maag Ltd <info@daltonmaag.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import itertools
from io import BytesIO
from typing import Mapping, Sequence

import ufo2ft
import uharfbuzz as hb
from fontTools.ufoLib.kerning import lookupKerningValue
from ufoLib2 import Font


# GID_PREFIX is an arbitrary value > U+10FFF to shift codepoints by, to avoid
# HarfBuzz doing any processing on them.
GID_PREFIX = 0x80000000


def main(args: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("ufos", nargs="+", type=Font.open)
    parsed_args = parser.parse_args(args)

    ufo: Font
    for ufo in parsed_args.ufos:
        validate_kerning(ufo)


def validate_kerning(ufo: Font) -> None:
    clear_ufo(ufo)
    tt_font = ufo2ft.compileTTF(ufo, useProductionNames=False)
    tt_font_blob = BytesIO()
    tt_font.save(tt_font_blob)
    glyph_id: dict[str, int] = {
        v: GID_PREFIX + k for k, v in enumerate(tt_font.glyphOrder)
    }

    hb_blob = hb.Blob(tt_font_blob.getvalue())
    hb_face = hb.Face(hb_blob)
    hb_font = hb.Font(hb_face)
    funcs = hb.FontFuncs.create()
    funcs.set_nominal_glyph_func(get_glyph_id, None)
    hb_font.funcs = funcs
    # We overwrite the font functions, so HarfBuzz defaults to using the font's
    # UPM as every glyph's width. That's fine, we just want the kerning value.
    hb_advance_width = hb_face.upem

    first_glyphs, second_glyphs = bucket_kerned_glyphs(ufo.kerning.keys(), ufo.groups)
    first_glyphs.intersection_update(glyph_id)
    second_glyphs.intersection_update(glyph_id)

    for first, second in itertools.product(sorted(first_glyphs), sorted(second_glyphs)):
        reference_value = lookupKerningValue((first, second), ufo.kerning, ufo.groups)

        first_gid = glyph_id[first]
        second_gid = glyph_id[second]
        hb_buf = hb.Buffer()
        hb_buf.add_codepoints((first_gid, second_gid))
        hb_buf.guess_segment_properties()
        hb.shape(hb_font, hb_buf, None)

        first_glyph_advance = hb_buf.glyph_positions[0].x_advance
        first_glyph_kerning = first_glyph_advance - hb_advance_width
        if first_glyph_kerning != reference_value:
            print(
                first,
                second,
                "should be",
                reference_value,
                "but is",
                first_glyph_kerning,
            )


def clear_ufo(ufo: Font) -> None:
    for glyph in ufo:
        glyph.clearContours()
        glyph.clearComponents()


def get_glyph_id(font: hb.Font, codepoint: int, user_data: None) -> int:
    """Return the glyph ID for a codepoint, where the codepoint is actually the
    GID_PREFIX + glyph ID according to the font's glyph order.

    This makes it possible to select glyphs by just their glyph ID instead of
    replicating the logic to shape from Unicode codepoints to glyph ID.
    """
    assert codepoint >= GID_PREFIX, codepoint
    return codepoint - GID_PREFIX


def bucket_kerned_glyphs(
    kerning: Sequence[tuple[str, str]], groups: Mapping[str, list[str]]
) -> tuple[set[str], set[str]]:
    first_glyphs: set[str] = set()
    second_glyphs: set[str] = set()

    for first, second in kerning:
        if first in groups:
            first_glyphs.update(groups[first])
        else:
            first_glyphs.add(first)
        if second in groups:
            second_glyphs.update(groups[second])
        else:
            second_glyphs.add(second)

    return first_glyphs, second_glyphs


if __name__ == "__main__":
    main()
