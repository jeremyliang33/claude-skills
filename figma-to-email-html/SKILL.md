---
name: figma-to-email-html
description: >
  Converts a Figma email design into production-ready, table-based HTML email code
  compatible with HubSpot and major email clients. Use this skill whenever a user
  provides a Figma URL and wants HTML email code — even if they just say "turn this
  into an email", "build this email", or "convert this design". Also trigger when
  the user mentions HubSpot email templates, email HTML, or wants to code up a
  Figma email frame. The skill handles the full workflow: inspecting the Figma file,
  generating email-safe HTML with inline styles, uploading images directly to HubSpot
  via API, setting up a local preview server, and verifying changes after every edit.
---

# Figma → HTML Email (with HubSpot Image Upload)

Convert a Figma email design into production-ready, table-based HTML for HubSpot (or any ESP),
including automatic image upload to HubSpot File Manager.

## Step 1: Understand the Figma File Structure

Start with `get_metadata` on the node from the URL to map the frame hierarchy. Email files often
contain extra elements (inbox preview mockups, subject line previews, annotation frames) that are
NOT part of the actual email — identify and ignore these. Ask the user to confirm which frame is
the real email if ambiguous.

Then call `get_design_context` on the specific email frame node ID to get full design details:
colors, typography, spacing, layout, and asset download URLs.

> ⚠️ Figma asset URLs expire after ~7 days. Upload images to HubSpot immediately (Step 2) so
> the email HTML uses permanent URLs.

## Step 2: Upload Images to HubSpot

Before writing the HTML, upload all image assets to HubSpot using the upload script at:
```
~/Documents/claude-skills/figma-to-email-html/hubspot-upload.py
```

The script reads the HubSpot token automatically from `~/.env` (no flag needed).

### Usage

```bash
python3 ~/Documents/claude-skills/figma-to-email-html/hubspot-upload.py \
  --urls <url1> <url2> <url3> ... \
  --folder "email-assets/YYYY/campaign-name"
```

### Folder naming convention
Ask the user for the destination folder path, or suggest one based on the Figma file name and
current date, e.g. `email-assets/2026/Q1/campaign-name`.

### What the script does
1. Extracts clean filenames automatically from the Figma asset URLs (URL-decodes percent-encoding)
2. Downloads each image from Figma's CDN
3. Uploads to HubSpot File Manager with `PUBLIC_INDEXABLE` access
4. Prints the permanent HubSpot CDN URL for each file

Use the returned HubSpot URLs (not the original Figma URLs) in all `<img src="">` attributes.

### Token setup (one-time)
The HubSpot Private App token lives at `~/.env`:
```
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```
- Create a dedicated Private App in HubSpot with only the `files` scope
- Never paste the token in chat or commit it to version control
- Only rotate if the token was accidentally exposed

## Step 3: Build Table-Based HTML

Email clients (Outlook especially) don't support modern CSS layout. Always use:
- `<table>` for layout, never flexbox or CSS Grid
- Inline `style=""` attributes on every element — no `<link>` stylesheets, minimal `<style>` in `<head>`
- `role="presentation"` on all layout tables
- `cellpadding="0" cellspacing="0" border="0"` on every table

### Standard Structure

```html
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
    table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
    img { -ms-interpolation-mode: bicubic; border: 0; display: block; }
    body { margin: 0; padding: 0; background-color: #f6f8f8; }
    a { text-decoration: none; }
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding:32px 0;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;">
          <!-- sections go here -->
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

### Images

Every `<img>` must have explicit `width=` and `height=` HTML attributes AND matching inline styles.
Always use the permanent HubSpot CDN URLs from Step 2 (never Figma's temporary URLs).

```html
<img src="https://39998325.fs1.hubspotusercontent-na1.net/hubfs/..." alt="Description"
     width="600" height="400" style="display:block;width:600px;height:400px;">
```

Always wrap clickable images in `<a>` tags.

### Inline Social Icons (Important Gotcha)

The global CSS reset `img { display: block; }` causes inline social icons to stack vertically.
Override on each element:

```html
<a href="..." style="display:inline-block;text-decoration:none;">
  <img src="..." width="16" height="16"
       style="display:inline-block;width:16px;height:16px;vertical-align:middle;border:0;">
</a>
```

### Font Stack

```
-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif
```

### Complex Hero Sections

If the Figma design has overlapping layers or absolute-positioned decorative elements, treat the
entire hero as a single exported image rather than trying to replicate it in HTML.

### HubSpot Tokens

```
{{ unsubscribe_link }}
{{ site_settings.company_name }}
{{ site_settings.company_street_address_1 }}
{{ site_settings.company_city }}, {{ site_settings.company_state }} {{ site_settings.company_zip }}
```

## Step 4: Set Up Preview Server

**Do not use Python's `http.server`** — PermissionError on macOS.

Use `npx serve` via `.claude/launch.json`:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "email-preview",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["serve", "/absolute/path/to/working/directory", "-p", "8787", "--no-clipboard"],
      "port": 8787
    }
  ]
}
```

Start with `preview_start`, then navigate to `http://localhost:8787/filename.html`.

## Step 5: Verify After Every Edit

Reload the preview and spot-check visually. For targeted checks use `preview_eval`:

```javascript
// Check divider colors
document.querySelectorAll('td[style*="border-top"]').map(el => el.style.borderTop)

// Check all links
document.querySelectorAll('a[href]').map(a => ({ text: a.textContent.trim(), href: a.href }))
```

## Common Patterns

### Horizontal Divider
```html
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr><td style="border-top:1px solid #D9DFDF;font-size:0;line-height:0;">&nbsp;</td></tr>
</table>
```

### Article Card (thumbnail + text)
```html
<table role="presentation" width="568" cellpadding="0" cellspacing="0" border="0" style="width:568px;">
  <tr>
    <td width="130" valign="top" style="width:130px;">
      <a href="https://..." style="display:block;">
        <img src="https://...hubspot..." alt="..." width="130" height="130"
             style="display:block;width:130px;height:130px;border-radius:8px;">
      </a>
    </td>
    <td width="24" style="width:24px;">&nbsp;</td>
    <td valign="middle" style="width:414px;">
      <p style="margin:0 0 10px 0;font-size:20px;font-weight:700;">Card Title</p>
      <p style="margin:0 0 14px 0;font-size:12px;">Body text.</p>
      <a href="https://..." style="font-size:12px;font-weight:700;color:#000;text-decoration:none;">CTA &#8594;</a>
    </td>
  </tr>
</table>
```

### Inline spacer
```html
<span style="display:inline-block;width:12px;line-height:12px;font-size:0;">&nbsp;</span>
```

## Checklist Before Handing Off

- [ ] All images uploaded to HubSpot — permanent CDN URLs used in HTML (no Figma temp URLs)
- [ ] All `<img>` tags have `width=`, `height=`, and matching inline `style` dimensions
- [ ] All links use real destination URLs (no `href="#"` placeholders)
- [ ] Font stack applied consistently
- [ ] Divider colors match spec
- [ ] Social icons render inline (not stacked)
- [ ] HubSpot tokens in footer
- [ ] Preview verified in browser
