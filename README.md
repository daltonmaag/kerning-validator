This is a partial rewrite of https://github.com/daltonmaag/kerning-validator/ to work on variable fonts. The point is to ensure that the old ufo2ft kern writer behaves correctly and the kerning in the sources and the final font matches across all master locations.

Run like:

```sh
uv run compile-font.py font.designspace output.ttf
uv run test-kerning.py font.designspace output.ttf
```
