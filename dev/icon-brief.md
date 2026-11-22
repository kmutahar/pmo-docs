# Plugin icon

A maintainer document, not shipped with the skill. The icon is final: there is nothing left to design or commission.

## What exists

- `skills/pmo-docs/.claude-plugin/icon.png`: the icon, 512 x 512 PNG (RGBA, no embedded colour profile, so sRGB), about 158 KiB.
- `dev/icon.svg`: the editable master (1024 x 1024 viewBox). Layered documents with task ticks, a board card, a target node and a green progress arrow on a dark blue rounded square with transparent corners.

`plugin.json` sets no `icon` key, so the plugin uses the default path above.

## Rules it meets (checked by `claude plugin validate`)

| Item | Requirement |
|---|---|
| Format | PNG or JPEG (SVG and WebP are not accepted). |
| Shape | Square. |
| Size | 512 to 2048 pixels on each side. |
| File size | Under 256 KiB (the plugin directory limit). |
| Colour | sRGB, no other embedded profile. |
| Location and name | `skills/pmo-docs/.claude-plugin/icon.png`, lower case. |

`tests/test_plugin.py` checks that the file is a PNG, square, 512 to 2048 pixels and under 256 KiB.

## Listing icon is locked

The file becomes the listing icon only once, the first time the plugin is saved or submitted in the developer portal. Changing it afterwards does not change the listing.

## Changing it

Edit `dev/icon.svg`, render it at 1024 x 1024 with the command below, then scale the PNG to 512 x 512 (a 1024 render can pass 256 KiB). Run `python3 -m unittest tests.test_plugin` and `claude plugin validate skills/pmo-docs` (no warnings).

```
google-chrome --headless --screenshot=skills/pmo-docs/.claude-plugin/icon.png --window-size=1024,1024 --default-background-color=00000000 "file://$(pwd)/dev/icon.svg"
```

Keep the rules that make it read when small: one simple shape, no text, no thin lines, no imitation of another company's logo, and it must look good on both white and near-black pages. Commit as `chore:` so it stays out of the changelog.
