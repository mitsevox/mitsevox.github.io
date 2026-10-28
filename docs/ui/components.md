# Shared UI components

This is a vanilla JavaScript static site. Reusable presentation primitives live under
`assets/components/ui/`, with exported factories and JSDoc `Props` interfaces. There is no
framework, dependency or bundler migration. The existing CSS classes, typography, sizes,
colors, spacing and motion remain the visual contract.

## Component boundary

A component owns its markup, native control semantics, accessibility state, motion and
cleanup. A page supplies content and callbacks, mounts `node`, and passes its `pageScope`.
`componentScope` gives interactive instances an independent lifetime that also ends when
their page exits. Destroying a page cancels component listeners, frames, animations and timers;
late clipboard/report completions cannot update a departed view.

Define a component's interface before adding consumers. Do not duplicate a menu, search
field, progress track or copy overlay in route templates. Templates contain named `data-ui`
slots where controls belong. Ordinary document headings, lists and navigation links do not
need a wrapper merely to avoid native HTML. Feature-specific map drawing, chart math and
report validation remain in their existing feature modules.

## Inventory and interfaces

| Component | Interface | Consumers and preserved variants |
| --- | --- | --- |
| `dropdown.js` | `createDropdown(DropdownProps)` → `node`, `trigger`, `menu`, `setValue`, `open`, `close`, `destroy` | Header project picker, hub filter/sort, game-ID and disc-revision pickers. One option/checkmark and interruptible opening/closing implementation. |
| `progress-bar.js` | `createProgressBar({kind, variant, ariaLabel?, tooltip, scope?})` → `node`, `track`, `update(measure)`, `unavailable()`, `matched`, `destroy` | Code and Data, on both the hub and game pages. `page` keeps the colored legend, animated number and keyboard tooltip. `compact` keeps the hub layout **without** a legend or an extra tab stop inside its card link. |
| `count-summary.js` | `createCountSummary({kind, scope?})` → `node`, `update(counts)`, `destroy` | Functions and Files inventories. Shared Exact/Named rows, count animation, total and accessible progress values. |
| `search-field.js` | `createSearchField({label, placeholder, variant?, id?})` → `node`, `input`, `value`, `setValue` | Hub, map and wiki searches. `map`, `hub`, `wiki` retain their existing visual classes and native search input. Filtering/index lookup stays with the feature. |
| `commit-line.js` | `createCommitLine({repository, variant?, scope?})` → `node`, `update(commit)`, `date`, `destroy` | Hub cards and game identity. Shared title, commit/clock icons, relative time and timer cleanup. `page` is a link; `compact` is a non-link row inside the card's existing link. |
| `tooltip.js` | `createTooltip({id, variant?, scope?, onHide?})` → `node`, `show(content)`, `hide`, `anchor`, `destroy` | Map details, page-bar values and hub-bar values. `map` retains its formatted surface/below-pointer placement; `hub` retains the compact/above-pointer surface. One owner at a time; existing unrelated `aria-describedby` references are preserved. |
| `action.js` | `createAction({label?, ariaLabel?, href?, as?, id?, className?, icon?, hidden?, disabled?})` → native button or link | Dropdown actions, project cards, map hit targets/back/close buttons, reset/retry and copy actions. Links keep native modified-click behavior; buttons explicitly use `type="button"`. Supply an accessible name for icon-only actions. No new default button skin. |
| `segmented-control.js` | `createSegmentedControl({id, label, value, options, onChange?, scope?})` → `node`, `setValue`, `destroy` | The map's Code/Data switch. Preserves its sliding indicator, pressed state and native Tab/Enter/Space behavior. Programmatic selection does not invoke feature callbacks. |
| `code-block.js` | `mountCodeBlock({pre, scope?, writeText?})` → `node`, `button`, `destroy` | All wiki examples. Retains the generated code/language class and normal font; the Copy button overlays the top right on hover/focus, without consuming a line. Clipboard denial exposes the existing manual-copy fallback. |
| `contribution-link.js` | `createContributionLink({href?, variant?, hidden?})` → native link | Header and game-page callout. `header` and `callout` retain their existing label/icons. Project configuration still controls whether either is shown. |
| `range.js` | `createRange({id, label, min?, max?, value?})` → native range input | Timeline scrubber. Chart/history code still decides its value, bounds, description and pointer-to-time mapping. Native keyboard/touch behavior is retained. |

`icons.js` contains trusted site-owned glyphs. `motion.js` supplies count/fill animation;
new values invalidate queued old fills, including a transition to unavailable. Text supplied
to components is rendered as text, not interpreted as markup.

## Report and feature ownership

The primitives do not fetch reports, authorize producers, validate packages, choose targets,
calculate map geometry, truncate timelines or decide contribution policy. `hub.js`,
`progress.js`, `activity.js`, `identity.js` and `wiki.js` keep those responsibilities.

A progress measure is the existing validated `{total, linked, matched, fuzzy?}` view model.
Widths remain cumulative percentages of `total`; the component must not add stacked values
or substitute matched/fuzzy values for linked bytes. Missing fuzzy data hides that fill and
its page legend key. A zero total is unavailable, not a measured 0%.

`update(commit)` accepts `{title?, date?, url?}`. A page commit link only adopts URLs under
its configured repository's `/commit/` path. Invalid dates do not start a timer. The compact
row deliberately has no nested link, so the entire game card remains one navigation target.

For tooltips, `show({anchor, label, value?, x, y, onHide?})` transfers ownership and dismisses
the previous hover finish. Map geometry/coloring stays with the map renderer; the common
bar component owns its own lifted strip. Escape, resize, scroll and page exit dismiss
transient tooltip state.

## Dropdown behavior

`DropdownProps` and `DropdownOption` are defined beside the factory. `setValue` updates
selection and an optional independent trigger label. `href` options retain normal links;
button options invoke `onSelect`. Every option uses the same selection checkmark.

The controller handles roving keyboard focus, Escape/outside dismissal, reduced motion,
viewport containment and interruptible entry/exit animations. Width follows content with a
viewport cap. Menu status belongs in the destination view when it describes a target rather
than being repeated as an extra badge inside each option.

## Verification

`tests/ui-components.mjs` exercises shared values/variants, optional fuzzy data, unavailable
states, queued-motion cancellation, tooltip ownership, clipboard completion/failure,
relative-time cleanup and programmatic/user segment selection. `tests/dropdown.mjs` covers
selection, keyboard behavior, reduced motion and interrupted closing/reopening.

Use real browser checks for geometry, SVG artwork, focus, pointer behavior, native search and
range controls, and responsive layout. Compare hub/game dimensions, displayed values and
legend placement against the accepted design. Keep reporting-contract and ingestion tests
unchanged; moving presentation code is not authorization to relax data checks.
