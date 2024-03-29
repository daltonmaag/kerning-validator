# SPDX-FileCopyrightText: 2022-present Dalton Maag Ltd <info@daltonmaag.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import functools
import itertools
import os
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Sequence, Set, Tuple

import fontTools.feaLib as feaLib
import tqdm
import ufo2ft
import uharfbuzz as hb
from fontTools import unicodedata
from fontTools.misc.fixedTools import otRound
from fontTools.ttLib import TTFont
from fontTools.ufoLib.kerning import lookupKerningValue
from ufo2ft.featureCompiler import parseLayoutFeatures
from ufo2ft.featureWriters.kernFeatureWriter import KernFeatureWriter, unicodeBidiType
from ufo2ft.util import DFLT_SCRIPTS, classifyGlyphs
from ufoLib2 import Font

from .language_tags import LANG_SYS_TAGS_TO_BCP47

# GID_PREFIX is an arbitrary value > U+10FFF to shift codepoints by, to avoid
# HarfBuzz doing any processing on them.
GID_PREFIX = 0x80000000

# Shapers hate this one mixing of bidi types in a kerning pair.
BAD_BIDIS = {"L", "R"}

PairIterable = Iterable[Tuple[str, Optional[str], Tuple[str, str]]]
GlyphProperties = Dict[str, Set[str]]


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ufo", nargs="+", type=Path)
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
        "--round",
        action="store_true",
        help="Round source kerning with otRound to reduce noise.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write the compiled fonts to a directory, for inspection.",
    )
    parser.add_argument(
        "--log-output-dir",
        type=Path,
        help="Write error logs to a directory.",
    )
    parser.add_argument(
        "--debug-feature-file",
        type=argparse.FileType("w"),
        help="Write the feature file to the given path",
    )
    parsed_args = parser.parse_args(args)

    output_dir: Path | None = parsed_args.output_dir
    progress_bar: bool = parsed_args.progress
    should_round: bool = parsed_args.round
    debug_feature_file: StringIO | None = parsed_args.debug_feature_file
    stepwise: bool = parsed_args.stepwise
    log_output_dir: Path | None = parsed_args.log_output_dir
    ufo_paths: list[Path] = parsed_args.ufo
    for ufo_path in ufo_paths:
        ufo = open_ufo(ufo_path)
        if output_dir is not None:
            output_font = output_dir / ufo_path.with_suffix(".ttf").name
        else:
            output_font = None
        if log_output_dir is not None:
            output_log = log_output_dir / ufo_path.with_suffix(".txt").name
        else:
            output_log = None
        validate_kerning(
            ufo,
            progress_bar,
            should_round,
            stepwise,
            debug_feature_file,
            output_font,
            output_log,
        )


def open_ufo(path: str | os.PathLike[str]) -> Font:
    path = Path(path)
    if path.suffix == ".ufo":
        return Font.open(path)
    elif path.suffix == ".json":
        return Font.json_load(path)
    raise argparse.ArgumentTypeError("Unrecognized format.")


def validate_kerning(
    ufo: Font,
    progress_bar: bool,
    should_round: bool,
    stepwise: bool,
    debug_feature_file: StringIO | None,
    output_font: Path | None,
    output_log: Path | None,
) -> None:
    # Clear out glyphs to speed up compile.
    clear_ufo(ufo)

    # Compile font with just the kerning feature writer to speed up the compile.
    tt_font: TTFont = ufo2ft.compileTTF(
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

    # Test pairs not just with the "default" language, but also with all the
    # others that are defined for the script (scouring `GSUB` and `GPOS`
    # tables), to ensure the kerning is registered for all languages.
    language_systems: dict[str, set[str | None]] = {}
    gsub = tt_font.get("GSUB")
    if gsub is not None:
        for script_record in gsub.table.ScriptList.ScriptRecord:
            for lang_sys_record in script_record.Script.LangSysRecord:
                language_systems.setdefault(script_record.ScriptTag, {None}).add(
                    LANG_SYS_TAGS_TO_BCP47.get(lang_sys_record.LangSysTag, None)
                )
    gpos = tt_font.get("GPOS")
    if gpos is not None:
        for script_record in gpos.table.ScriptList.ScriptRecord:
            for lang_sys_record in script_record.Script.LangSysRecord:
                language_systems.setdefault(script_record.ScriptTag, {None}).add(
                    LANG_SYS_TAGS_TO_BCP47.get(lang_sys_record.LangSysTag, None)
                )

    # Drop the GSUB table now to stop HarfBuzz from applying any substitutions
    # later in the comparison loop. It must only use what it's given.
    if "GSUB" in tt_font:
        del tt_font["GSUB"]
    tt_font_blob = BytesIO()
    tt_font.save(tt_font_blob)
    if output_font is not None:
        output_font.write_bytes(tt_font_blob.getvalue())
    if output_log is not None:
        log_output = open(output_log, "w")
    else:
        log_output = sys.stdout  # type: ignore
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
    hb_advance_width: int = hb_face.upem

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

    glyphToFirstGroup: dict[str, str] = {}
    glyphToSecondGroup: dict[str, str] = {}
    for group, groupMembers in ufo.groups.items():
        if group.startswith("public.kern1."):
            for glyph in groupMembers:
                glyphToFirstGroup[glyph] = group
        elif group.startswith("public.kern2."):
            for glyph in groupMembers:
                glyphToSecondGroup[glyph] = group

    # Plan: iterate over every combination of kern1 and kern2 glyph (standalone
    # or member of group), but, to simulate real-world-application itemization
    # runs, only if both are of the same script or at least one is a "common"
    # script. Some glyphs may be associated with more than one script (e.g.
    # U+0951 DEVANAGARI STRESS SIGN UDATTA), so repeat the pair for all of these
    # scripts. Also test the pair with each language other than the default one
    # that has been defined for OpenType Layout.
    for script, language, (first, second) in report_progress(
        iterate_script_and_pairs(
            first_glyphs, second_glyphs, glyph_scripts, glyph_bidis, language_systems
        )
    ):
        reference_value: float = lookupKerningValue(
            (first, second),
            ufo.kerning,
            ufo.groups,
            glyphToFirstGroup=glyphToFirstGroup,
            glyphToSecondGroup=glyphToSecondGroup,
        )
        if should_round:
            reference_value = otRound(reference_value)
        direction = unicodedata.script_horizontal_direction(script, "LTR")

        first_gid = glyph_id[first]
        second_gid = glyph_id[second]
        hb_buf = hb.Buffer()
        hb_buf.script = script
        hb_buf.direction = direction
        if language is not None:
            hb_buf.language = language
        hb_buf.add_codepoints((first_gid, second_gid))
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
        kerning_value: int = (
            hb_buf.glyph_positions[0].x_advance
            + hb_buf.glyph_positions[1].x_advance
            - 2 * hb_advance_width
        )
        if kerning_value != reference_value:
            print(
                f"{script=} {language=} {direction=}: {first} {second} should be {reference_value} but is {kerning_value}",
                file=log_output,
            )
            if stepwise:
                sys.exit(1)

    if log_output is not sys.stdout:
        log_output.close()


def clear_ufo(ufo: Font) -> None:
    for glyph in ufo:
        glyph.clearContours()
        glyph.clearComponents()
    # Ditch everything might interfere with the GPOS table,
    # we only want to test kerning as applied by the KernFeatureWriter
    undesirable_features = {"kern", "mark", "mkmk", "curs", "dist"}
    features: feaLib.ast.FeatureFile = parseLayoutFeatures(ufo)  # Resolve includes
    features.statements = [
        statement
        for statement in features.statements
        if not (
            isinstance(statement, feaLib.ast.FeatureBlock)
            and statement.name in undesirable_features
        )
    ]
    ufo.features.text = features.asFea()


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


def classify_glyphs(font: TTFont) -> tuple[GlyphProperties, GlyphProperties]:
    cmap = font.getBestCmap()
    gsub = font.get("GSUB")

    font_scripts = determine_font_scripts(cmap)
    scripts_for_copdepoint = functools.partial(
        script_extensions_for_codepoint, known_scripts=font_scripts
    )
    scripts = classifyGlyphs(scripts_for_copdepoint, cmap, gsub)
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


def determine_font_scripts(cmap: Mapping[int, str]) -> set[str]:
    """Returns a set of scripts the font is determined to support.

    This is done by looking at all defined codepoints in a font and
    remembering the script of any of the codepoints if it is associated with
    just one script. This would remember the script of U+0780 THAANA LETTER
    HAA (Thaa) but not U+061F ARABIC QUESTION MARK (multiple scripts).
    """
    single_scripts: set[str] = set()
    for codepoint in cmap.keys():
        scripts = unicodedata.script_extension(chr(codepoint))
        if len(scripts) == 1:
            single_scripts.update(scripts)
    return single_scripts


def script_extensions_for_codepoint(uv: int, known_scripts: set[str]) -> set[str]:
    # If there are no detected scripts, consider everything common.
    if not known_scripts:
        return {"Zyyy"}
    else:
        return {
            x
            for x in unicodedata.script_extension(chr(uv))
            if x in known_scripts or x in DFLT_SCRIPTS
        }


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
    language_systems: dict[str, set[str | None]],
) -> PairIterable:
    # Imitate real world text itemization by filtering out pairs that wouldn't
    # occur next to each other in the same run.
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
                script = first_script
            elif first_script in DFLT_SCRIPTS:
                script = second_script
            elif second_script in DFLT_SCRIPTS:
                script = first_script
            else:
                continue

            # NOTE: Language systems are keyed by OpenType Script Tags, but
            # scripts here are Unicode script codes. Collect all languages that
            # are defined for any Script Tag (e.g. `taml` and `tml2`) just to be
            # thorough.
            languages = {
                language
                for tag in unicodedata.ot_tags_from_script(script)
                for language in language_systems.get(tag, (None,))
            }
            assert languages
            for language in languages:
                yield script, language, (first, second)


if __name__ == "__main__":
    main()
