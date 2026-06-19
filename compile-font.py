from __future__ import annotations

import argparse

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.feaLib import ast
from ufo2ft import compileVariableTTF
from ufo2ft.featureCompiler import parseLayoutFeatures
from ufo2ft.featureWriters.kernFeatureWriter2 import KernFeatureWriter
from ufoLib2 import Font


def clear_ufo(ufo: Font) -> None:
    for layer in ufo.layers:
        for glyph in layer:
            glyph.clearContours()
            glyph.clearComponents()
    # Ditch everything might interfere with the GPOS table,
    # we only want to test kerning as applied by the KernFeatureWriter
    undesirable_features = {"kern", "mark", "mkmk", "curs", "dist"}
    features: ast.FeatureFile = parseLayoutFeatures(ufo)  # Resolve includes
    features.statements = [
        statement
        for statement in features.statements
        if not (
            isinstance(statement, ast.FeatureBlock)
            and statement.name in undesirable_features
        )
    ]
    ufo.features.text = features.asFea()


parser = argparse.ArgumentParser()
parser.add_argument("input", type=DesignSpaceDocument.fromfile)
parser.add_argument("output")
parsed_args = parser.parse_args()
ds: DesignSpaceDocument = parsed_args.input
ds.loadSourceFonts(Font.open)
for source in ds.sources:
    assert source.font
    clear_ufo(source.font)
target: str = parsed_args.output

font = compileVariableTTF(
    ds, useProductionNames=False, featureWriters=[KernFeatureWriter]
)
font.save(target)
