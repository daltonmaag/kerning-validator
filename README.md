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

Run the tool on one or more [UFOs](https://unifiedfontobject.org/). It will compile them using [ufo2ft](https://github.com/googlefonts/ufo2ft/) and use [uharfbuzz](https://github.com/harfbuzz/uharfbuzz/) to ensure that the kerning define din the sources makes it into the final font.

## License

`kerning-validator` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
