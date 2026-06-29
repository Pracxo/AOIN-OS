# Static Console Accessibility Checklist

## Headings

- Page title remains unique and describes the local static console.
- Navigation rail headings identify group navigation and view navigation.
- Each major panel keeps an accessible heading.

## Keyboard Navigation

- Skip link moves focus to the console content.
- Group, view, role, safety, and command controls are native buttons or links.
- Arrow keys move focus among group, view, and role controls.
- Section shortcut links target focusable sections.

## Focus States

- `:focus-visible` has a high-contrast outline.
- Focus styles are not removed from buttons or links.
- The focused element remains visible on narrow screens.

## Contrast

- Text and panel backgrounds maintain strong contrast.
- Muted text is used only for secondary context.
- Blocked, warning, and ready states use readable text plus shape or label.

## Aria Labels

- Top-level navigation has an aria label.
- View group controls expose pressed state.
- Section shortcut navigation has an aria label.
- Dynamic copy status uses polite live-region text.

## No Color-Only Status

- Status chips include text.
- Blocker badges include labels and messages.
- Safety cards include explicit boolean values.

## Responsive Layout

- The rail stacks above content on narrow screens.
- Group and view controls wrap into stable tracks.
- Checklist rows stack before text overflows.

## Reduced Cognitive Load

- Groups reduce the number of visible view choices.
- Section shortcuts expose the main journeys without scrolling through every
  panel.
- The safety blocker view collects no-go conditions in one place.

## Static Fallback

- Offline demo JSON remains the fallback.
- Non-local API origins remain blocked.
- The page does not require a build step or package install.

## No External Dependencies

- No external fonts, scripts, styles, icon kits, component frameworks, or
  network assets are required.
