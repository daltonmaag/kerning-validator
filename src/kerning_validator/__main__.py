# SPDX-FileCopyrightText: 2022-present Dalton Maag Ltd <info@daltonmaag.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import itertools
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import Callable, Dict, Iterable, Mapping, Sequence, Set, Tuple

import tqdm
import ufo2ft
import uharfbuzz as hb
from fontTools import unicodedata
from fontTools.ttLib import TTFont
from fontTools.ufoLib.kerning import lookupKerningValue
from ufo2ft.featureWriters.kernFeatureWriter import KernFeatureWriter, unicodeBidiType
from ufo2ft.util import DFLT_SCRIPTS, classifyGlyphs
from ufoLib2 import Font

# GID_PREFIX is an arbitrary value > U+10FFF to shift codepoints by, to avoid
# HarfBuzz doing any processing on them.
GID_PREFIX = 0x80000000

# Inserted between two pairs to stop features from applying, but keep the
# kerning.
ZWNJ_CODEPOINT = 0x200C
SPACE_CODEPOINT = 0x0020

# Shapers hate this one mixing of bidi types in a kerning pair.
BAD_BIDIS = {"L", "R"}

PairIterable = Iterable[Tuple[str, Tuple[str, str]]]
GlyphProperties = Dict[str, Set[str]]


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ufos", nargs="+", type=Font.open)
    parser.add_argument(
        "--stepwise",
        action="store_true",
        help="Stop after the first failure.",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Report progress.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write the compiled fonts to a directory, for inspection.",
    )
    parser.add_argument(
        "--debug-feature-file",
        type=argparse.FileType("w"),
        help="Write the feature file to the given path",
    )
    parsed_args = parser.parse_args(args)

    output_dir: Path | None = parsed_args.output_dir
    progress_bar: bool = parsed_args.progress
    debug_feature_file: StringIO | None = parsed_args.debug_feature_file
    stepwise: bool = parsed_args.stepwise
    ufo: Font
    for ufo in parsed_args.ufos:
        validate_kerning(ufo, output_dir, progress_bar, debug_feature_file, stepwise)


def validate_kerning(
    ufo: Font,
    output_dir: Path | None,
    progress_bar: bool,
    debug_feature_file: StringIO | None,
    stepwise: bool,
) -> None:
    # Clear out glyphs to speed up compile.
    clear_ufo(ufo)

    # Compile font with just the kerning feature writer to speed up the compile.
    tt_font = ufo2ft.compileTTF(
        ufo,
        useProductionNames=False,
        featureWriters=[KernFeatureWriter],
        debugFeatureFile=debug_feature_file,
    )
    if progress_bar:
        print("Compiled TTF")

    glyphOrder = tt_font.getGlyphOrder()
    glyph_id: dict[str, int] = {v: GID_PREFIX + k for k, v in enumerate(glyphOrder)}

    glyph_scripts, glyph_bidis = classify_glyphs(tt_font)

    # Drop the GSUB table now to stop HarfBuzz from applying any substitutions
    # later in the comparison loop. It must only use what it's given.
    del tt_font["GSUB"]
    tt_font_blob = BytesIO()
    tt_font.save(tt_font_blob)
    if output_dir is not None:
        assert ufo.reader is not None
        output_font = output_dir / Path(ufo.reader.path).with_suffix(".ttf").name
        output_font.write_bytes(tt_font_blob.getvalue())
    if progress_bar:
        print("Saved TTF")

    hb_blob = hb.Blob(tt_font_blob.getvalue())
    hb_face = hb.Face(hb_blob)
    hb_font = hb.Font(hb_face)
    funcs = hb.FontFuncs.create()
    funcs.set_nominal_glyph_func(get_glyph_id, None)
    hb_font.funcs = funcs
    # We overwrite the font functions, so HarfBuzz defaults to using the font's
    # UPM as every glyph's width. That's fine, we just want the kerning value.
    hb_advance_width = hb_face.upem

    first_glyphs, second_glyphs = bucket_kerned_glyphs(
        ufo.kerning.keys(), ufo.groups, glyph_scripts
    )
    first_glyphs.intersection_update(glyph_id)
    second_glyphs.intersection_update(glyph_id)

    if progress_bar:
        report_progress: Callable[[PairIterable], PairIterable] = lambda gen: tqdm.tqdm(
            list(gen)
        )
    else:
        report_progress = lambda gen: gen

    # Plan: iterate over every combination of kern1 and kern2 glyph (standalone
    # or member of group), but, to simulate real-world-application itemization
    # runs, only if both are of the same script or at least one is a "common"
    # script. Some glyphs may be associated with more than one script (e.g.
    # U+0951 DEVANAGARI STRESS SIGN UDATTA), so repeat the pair for all of these
    # scripts.
    for script, (first, second) in report_progress(
        iterate_script_and_pairs(
            first_glyphs, second_glyphs, glyph_scripts, glyph_bidis
        )
    ):
        reference_value = lookupKerningValue((first, second), ufo.kerning, ufo.groups)
        direction = unicodedata.script_horizontal_direction(script)

        first_gid = glyph_id[first]
        second_gid = glyph_id[second]
        hb_buf = hb.Buffer()
        hb_buf.script = script
        hb_buf.direction = direction
        # Insert a ZWNJ inbetween to stop (most?) features from applying.
        hb_buf.add_codepoints((first_gid, ZWNJ_CODEPOINT, second_gid))
        hb.shape(hb_font, hb_buf, None)

        # Sanity checks to ensure HarfBuzz doesn't do unexpected substitutions.
        # The returned buffer is ready for LTR rendering, so RTL glyphs are
        # stored "backwards" with advance widths reversed.
        glyph_infos = (
            hb_buf.glyph_infos if direction == "LTR" else reversed(hb_buf.glyph_infos)
        )
        shaped_names = [tt_font.getGlyphName(i.codepoint) for i in glyph_infos]
        assert shaped_names == [first, second], shaped_names

        # The kerning value is added to the advance width of either glyph
        # depending on direction.
        kerning_value = (
            hb_buf.glyph_positions[0].x_advance
            + hb_buf.glyph_positions[1].x_advance
            - 2 * hb_advance_width
        )
        if kerning_value != reference_value:
            print(
                f"{script=} {direction=}: {first} {second} should be {reference_value} but is {kerning_value}"
            )
            if stepwise:
                sys.exit(1)


def clear_ufo(ufo: Font) -> None:
    for glyph in ufo:
        glyph.clearContours()
        glyph.clearComponents()


def get_glyph_id(font: hb.Font, codepoint: int, user_data: None) -> int:
    """Return the glyph ID for a codepoint, where the codepoint is actually the
    GID_PREFIX + glyph ID according to the font's glyph order.

    This makes it possible to select glyphs by just their glyph ID instead of
    replicating the logic to shape from Unicode codepoints to glyph ID.

    ZWNJ is a special case inserted to stop features from being applied, but
    keep kerning. It doesn't matter to HarfBuzz whether it exists so we just
    return GID 0. HarfBuzz also inserts a zero-width space codepoint somewhere.
    There might be other codepoints that HarfBuzz inserts at some point, just
    pass them back as is.
    """
    if codepoint == SPACE_CODEPOINT or codepoint == ZWNJ_CODEPOINT:
        return 0
    if codepoint >= GID_PREFIX:
        return codepoint - GID_PREFIX
    return codepoint


def classify_glyphs(font: TTFont) -> tuple[GlyphProperties, GlyphProperties]:
    cmap = font.getBestCmap()
    gsub = font["GSUB"]

    scripts = classifyGlyphs(script_extensions_for_codepoint, cmap, gsub)
    glyph_scripts: GlyphProperties = {}
    for script, glyphs in scripts.items():
        for name in glyphs:
            glyph_scripts.setdefault(name, set()).add(script)

    bidis = classifyGlyphs(unicodeBidiType, cmap, gsub)
    glyph_bidis: GlyphProperties = {}
    for bidi, glyphs in bidis.items():
        for name in glyphs:
            glyph_bidis.setdefault(name, set()).add(bidi)

    return glyph_scripts, glyph_bidis


def script_extensions_for_codepoint(uv: int) -> set[str]:
    return unicodedata.script_extension(chr(uv))


def bucket_kerned_glyphs(
    kerning: Sequence[tuple[str, str]],
    groups: Mapping[str, list[str]],
    glyph_scripts: GlyphProperties,
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

    # Skip unreachable glyphs, i.e. those without a codepoint and not reachable
    # via substitution. This includes accidentally kerned glyphs that are only
    # used as components.
    first_glyphs.intersection_update(glyph_scripts)
    second_glyphs.intersection_update(glyph_scripts)

    return first_glyphs, second_glyphs


def iterate_script_and_pairs(
    first_glyphs: set[str],
    second_glyphs: set[str],
    glyph_scripts: GlyphProperties,
    glyph_bidis: GlyphProperties,
) -> PairIterable:
    for first, second in itertools.product(sorted(first_glyphs), sorted(second_glyphs)):
        # Skip pairs with mixed bidirectionality. BiDi segmentation in
        # applications ensures that bidi mixing won't typically occur.
        pair_bidis: set[str] = {
            *glyph_bidis.get(first, []),
            *glyph_bidis.get(second, []),
        }
        if pair_bidis.issuperset(BAD_BIDIS):
            continue

        # Skip pairs that mix explicit scripts (implicit scripts like Zyyy are
        # fine), because in real-world applications, text is segmented into text
        # runs for each script. Cross-script kerning is therefore never applied.
        # A glyph might be member of multiple scripts for reasons, though, so
        # ensure we hit all combinations.
        first_scripts = glyph_scripts[first]
        second_scripts = glyph_scripts[second]
        for first_script, second_script in itertools.product(
            first_scripts, second_scripts
        ):
            if first_script == second_script:
                yield first_script, (first, second)
            elif first_script in DFLT_SCRIPTS:
                yield second_script, (first, second)
            elif second_script in DFLT_SCRIPTS:
                yield first_script, (first, second)
            else:
                continue


if __name__ == "__main__":
    main()
