# kerning-validator

**Table of Contents**

- [Installation](#installation)
- [Use](#use)
- [License](#license)

## Installation

```console
pip install git+https://github.com/daltonmaag/kerning-validator
```

## Use

This is a developer tool to sanity-check the font compilation stack.

It tests ufo2ft's KernFeatureWriter (no manual `kern`, `dist`, `mark`, `mkmk`, `curs` features; too complicated to unparse), and thereby implicitly fontTools's font compilation and uharfbuzz's table packing code. The shaping is validated with the HarfBuzz code embedded into uharfbuzz, typically using the HarfBuzz shaping engine.

Run the tool on one or more [UFOs](https://unifiedfontobject.org/). It will compile them using [ufo2ft](https://github.com/googlefonts/ufo2ft/) and use [uharfbuzz](https://github.com/harfbuzz/uharfbuzz/) to ensure that the kerning defined in the sources makes it into the final font.

## License

`kerning-validator` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
