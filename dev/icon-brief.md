# Plugin icon: brief for a designer

A maintainer document, not shipped with the skill. It tells a designer what to make and what the validator accepts. The icon is for the `pmo-docs` plugin, a project office kept in plain files and run by an AI coding agent.

## What exists now

A placeholder (drawn once by a script that is no longer in the repo): a white clipboard with a checklist (two ticked boxes, one empty) on a dark blue rounded square. It passes the validator. Replace it when a designer's version is ready. The file to replace is:

```
skills/pmo-docs/.claude-plugin/icon.png
```

## Hard requirements (checked by `claude plugin validate`)

| Item | Requirement |
|---|---|
| Format | PNG or JPEG. SVG and WebP are **not** accepted. PNG is preferred (sharp edges, transparency). |
| Shape | Square, same width and height. |
| Size | Between 512 and 2048 pixels on each side. Deliver 1024 x 1024 so it stays sharp when scaled down. |
| File size | Under 2 MB. A flat-colour icon is usually under 100 KB. |
| Location | `skills/pmo-docs/.claude-plugin/icon.png` (the plugin's `.claude-plugin/` folder), or any path set as `icon` in `skills/pmo-docs/.claude-plugin/plugin.json`. |
| Colour | sRGB. No embedded colour profile other than sRGB. |
| Name | `icon.png`, lower case. |

`tests/test_plugin.py` checks that the file is a PNG, square, 512 to 2048 pixels and under 2 MB.

A note from the validator: the file may become the listing icon only once, the first time the plugin is saved or submitted in the developer portal. Changing it afterwards does not change the listing icon. So get the design right before the first submission.

## What the icon should say

The plugin keeps project facts in lists (tasks, risks, decisions), turns them into reports, and checks them. Good ideas: a checklist, a clipboard, a board with rows, a folded page with a tick. Calm, trustworthy, plain. Avoid robots, sparkles, brains and chat bubbles: the product is not about chatting, and it must not look like an Anthropic or Claude mark.

Rules:
- One simple shape that reads at 32 x 32 pixels. If detail disappears at that size, remove it.
- No text and no letters. The name is shown next to the icon, and text becomes unreadable when small.
- No photographs, gradients that rely on subtle shades, or thin lines (under 3% of the width).
- Do not copy or imitate the logo of Anthropic, Claude, GitHub or any other company.
- Keep the artwork inside a safe area: leave at least 10% empty margin on every side, because listings may crop it into a circle or a rounded square.
- Work on a flat square. Either fill the whole square with the background colour (listings may round the corners themselves), or give it rounded corners with a transparent outside. Say which you chose.
- It must look good on both a white and a near-black page. A filled background square does that; a transparent icon needs a check on both.

## Colours in the placeholder (a starting point, not a rule)

| Use | Colour |
|---|---|
| Background | `#1F4E79` (dark blue) |
| Board | `#FFFFFF` |
| Clip | `#9FC5E8` |
| Tick | `#2E8B57` (green) |
| Lines | `#B7C4D1` |

Keep contrast high: the main shape against the background at least 4.5 to 1, so it is readable and accessible.

## What to deliver

1. `icon.png`, 1024 x 1024, PNG, sRGB, under 2 MB.
2. The editable source (SVG, Figma or similar), so the icon can be changed later.
3. One line saying whether the corners are filled or rounded with transparency.
4. A preview at 512, 128, 64 and 32 pixels on a white and on a dark background, to show it holds up when small.
4. Confirmation that the artwork is original or licensed for use in an MIT-licensed open source project, with the licence of any font or stock element. The repository is public, so the icon is public too.

## How to install the delivered file

1. Replace `skills/pmo-docs/.claude-plugin/icon.png` with the new file.
2. Run `python3 -m unittest tests.test_plugin` (checks format, shape, size) and `claude plugin validate skills/pmo-docs` (must show no warnings).
3. Commit it as `chore: add the plugin icon` or `docs: ...` (it is not a user-facing change, so `chore` keeps it out of the changelog).
