# Astrea Design System

Status: Stage 1 baseline for Lovable and implementation.

Brand source of truth: the client Jubilee Repository, especially pages 4-5, plus the supplied Astrea standard/banner.

## 1. Visual character

The site should feel:
- classical;
- restrained;
- institutional;
- historical;
- status-oriented;
- slightly traditional/old-fashioned where appropriate.

It should not look like a modern SaaS landing page or an AI-generated occult fantasy.

Avoid:
- neon;
- arbitrary gold palettes;
- heavy gradients;
- glassmorphism;
- excessive animation;
- generic Masonic stock symbolism;
- invented heraldry;
- decorative clutter.

## 2. Brand palette

Official print references from the client material:
- Pantone 485 C — accent red;
- Pantone Cool Gray 6 C — light neutral gray;
- Pantone Cool Gray 10 C — dark neutral gray;
- Pantone Process Black C — primary black;
- white.

For web implementation use the following working approximations, while the Pantone references remain the brand source of truth:

```text
brand-red:        #DA291C
cool-gray-6:      #A7A8AA
cool-gray-10:     #63666A
process-black:    #2D2926
white:            #FFFFFF
```

These values are implementation approximations for screens, not replacements for the official Pantone specification.

Semantic roles:

```text
--color-bg-primary       process-black
--color-bg-secondary     near-black/charcoal derived from process-black
--color-surface          dark neutral surface
--color-text-primary     white
--color-text-secondary   cool-gray-6
--color-text-muted       cool-gray-10 / adjusted for accessible contrast
--color-accent           brand-red
--color-border           cool-gray-10 with restrained opacity
```

Red is an accent, not a background default. It should be used sparingly for active states, important rules, key buttons and small identity details.

## 3. Contrast and accessibility

The visual identity may be dark, but text contrast must remain practical.

- Long-form body copy should not use low-contrast gray on black.
- Muted text must still meet readable contrast targets.
- Red should not be the only indicator of state or error.
- Focus states must be clearly visible for keyboard users.

## 4. Typography

The client reference on page 5 establishes a classical serif/antiqua direction.

Use two functional roles:

### Display / headings
A classical Cyrillic-capable serif with historical character. It should feel editorial and dignified, not ornamental or gothic.

### Body / UI
A highly readable Cyrillic-capable text face for paragraphs, forms, tables and admin UI.

Exact font families are selected during the Lovable prototype review. Do not choose a decorative typeface solely because it appears 'Masonic'.

Recommended hierarchy:
- H1: large serif, restrained tracking, strong vertical spacing;
- H2/H3: serif;
- body: readable text face, generous line-height;
- navigation/buttons/forms: text face or restrained small serif depending on legibility.

## 5. Layout

Public site:
- generous margins;
- strong vertical rhythm;
- limited content width for long reading;
- clear sectional separation;
- thin rules/borders rather than large decorative cards;
- asymmetry may be used in hero composition, but content reading remains orderly.

Do not use a dense dashboard/card-grid aesthetic on public pages.

Admin panel may be more utilitarian while retaining the same colors and typography tokens.

## 6. Header

Desktop header:
- restrained height;
- Astrea name/mark on the left;
- primary navigation;
- one clear 'Вступить' action;
- dark background;
- no oversized sticky effects.

Mobile:
- compact logo/name;
- accessible menu trigger;
- no horizontal overflow.

## 7. Hero

Primary visual asset: client-supplied Astrea standard/banner.

Direction:
- dark background;
- standard positioned left or right depending on final crop;
- subtle controlled backlight/glow behind the standard;
- no fake smoke, flames, temple interiors or invented mystical effects;
- copy remains short and formal;
- one primary CTA to the candidate/join section.

The standard should look like a real historic object, not a fantasy illustration.

## 8. Buttons and links

Primary action:
- red accent;
- restrained rectangular geometry;
- minimal radius;
- no pill-button SaaS style.

Secondary action:
- transparent/dark surface;
- light border/text;
- red only on hover/focus where appropriate.

Text links should have a clear hover/focus treatment without excessive animation.

## 9. Cards

News/video cards should be editorial rather than app-like:
- image;
- date/category metadata;
- serif title;
- short excerpt;
- subtle border or spacing separation.

Avoid deep shadows and floating-card effects.

## 10. Candidate form

The form is a core product surface and must feel trustworthy rather than ceremonial.

- clear multi-section structure;
- readable labels above fields;
- visible required markers;
- concise help/error text;
- calm spacing;
- photo upload with clear constraints;
- consent section visually separated;
- mobile-first usability.

Do not decorate the form with symbolic imagery that competes with completion.

## 11. Admin UI

Admin is functional first:
- same token palette;
- high readability;
- compact but not cramped tables;
- clear status labels;
- candidate data treated visually as private information;
- destructive actions visually distinct and confirmation-protected.

## 12. Motion

Use motion only for orientation and feedback:
- short hover/focus transitions;
- restrained content reveal if used;
- no parallax dependency;
- no long cinematic intro;
- respect `prefers-reduced-motion`.

## 13. Imagery

Priority order:
1. approved client assets;
2. historical/documentary materials supplied or approved by the client;
3. neutral supporting photography if explicitly approved.

Do not generate or insert pseudo-Masonic imagery as filler.

## 14. Lovable instruction

Lovable is a design/prototyping implementation aid, not the source of brand decisions.

When prompting Lovable:
- explicitly provide the palette above;
- explicitly prohibit generic SaaS/occult styling;
- use the supplied standard as the hero focal point;
- keep layout classical and editorial;
- preserve accessibility and mobile behavior;
- do not invent additional symbols or brand colors.
