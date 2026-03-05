# Claude Skills

Custom Claude Code skills for the Rho team.

## Skills

### `figma-to-email-html`
Converts a Figma email design into production-ready, table-based HTML for HubSpot.

**Triggers automatically when you:**
- Paste a Figma URL and ask to convert it to HTML
- Say "build this email" or "convert this to HubSpot HTML"

**Includes:**
- `SKILL.md` — skill instructions loaded by Claude
- `hubspot-upload.py` — uploads Figma image assets directly to HubSpot File Manager

**Setup required:**
- Add your HubSpot Private App token to `~/.env`:
  ```
  HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-...
  ```
- Install dependencies: `pip3 install requests`
