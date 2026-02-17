# Brand Assets for Home Assistant

This folder contains brand assets to be submitted to the [home-assistant/brands](https://github.com/home-assistant/brands) repository.

## Submission Instructions

1. Convert the SVG icons in `custom_components/intervals_icu_gear/icons/` to PNG format
2. Create the following files in `intervals_icu_gear/`:
   - `icon.png` (256x256 pixels)
   - `icon@2x.png` (512x512 pixels)
   - `dark_icon.png` (256x256 pixels) - optional
   - `dark_icon@2x.png` (512x512 pixels) - optional

3. Fork https://github.com/home-assistant/brands
4. Copy the `intervals_icu_gear/` folder to `custom_integrations/intervals_icu_gear/`
5. Submit a PR

## Tools for Conversion

- [RedKetchup Image Resizer](https://redketchup.io/image-resizer) - Online SVG to PNG
- Inkscape: `inkscape icon.svg -w 256 -h 256 -o icon.png`
- ImageMagick: `convert -background none icon.svg -resize 256x256 icon.png`

## Requirements

- PNG format only
- Properly compressed/optimized
- Transparent background preferred
- Trimmed (no extra whitespace)

