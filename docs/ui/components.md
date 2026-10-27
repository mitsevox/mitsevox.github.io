# Shared UI components

This is a vanilla JavaScript static site. Reusable interactive primitives live under
`assets/components/ui/`; they use exported factories and JSDoc `Props` types, without a
framework or bundler migration.

A primitive owns its DOM structure, selection/accessibility state, keyboard/focus behavior,
animations and shared styling hooks. Page modules supply content, data and callbacks. Define
that contract before adding another consumer. If the same interactive structure starts being
copied across pages, extract it and refactor its callers rather than maintaining another variant.
Existing unrelated controls can move when they need meaningful work; this is a design rule,
not a mechanical rewrite of every native input.

## Dropdown

`createDropdown(props)` in `assets/components/ui/dropdown.js` owns the complete trigger/menu
markup. `DropdownProps` and `DropdownOption` define the interface. `setValue` updates selection
and an optional independent trigger label. Options with `href` keep normal link navigation;
button options call `onSelect`. Text is rendered with `textContent`; console icons come from
the internal icon registry. The component supplies the same checkmark everywhere.

The internal controller handles roving keyboard focus, Escape/outside dismissal, reduced
motion, viewport containment, interruptible opening/closing animation and route cleanup.
Menus size to their contents with a viewport cap. Header game switching, hub filtering/sorting
and game target pickers are consumers of this same component.

Use `pageScope` for page-owned components. The shared shell's component lives for the shell's
lifetime. Menu status belongs in the destination view when it describes the target, rather
than being repeated as an extra badge inside every option.
