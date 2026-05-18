# Indian Railways wheel logo as inline SVG — no external URL needed
INDIAN_RAILWAYS_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" height="{size}">
  <!-- Outer circle -->
  <circle cx="50" cy="50" r="46" fill="none" stroke="#f26522" stroke-width="5"/>
  <!-- Inner circle (hub) -->
  <circle cx="50" cy="50" r="12" fill="#f26522"/>
  <!-- 8 spokes -->
  <line x1="50" y1="4"  x2="50" y2="38" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="50" y1="62" x2="50" y2="96" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="4"  y1="50" x2="38" y2="50" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="62" y1="50" x2="96" y2="50" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="17" y1="17" x2="41" y2="41" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="59" y1="59" x2="83" y2="83" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="83" y1="17" x2="59" y2="41" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <line x1="17" y1="83" x2="41" y2="59" stroke="#f26522" stroke-width="4" stroke-linecap="round"/>
  <!-- Rim dots at spoke ends -->
  <circle cx="50" cy="4"  r="4" fill="#f26522"/>
  <circle cx="50" cy="96" r="4" fill="#f26522"/>
  <circle cx="4"  cy="50" r="4" fill="#f26522"/>
  <circle cx="96" cy="50" r="4" fill="#f26522"/>
  <circle cx="17" cy="17" r="4" fill="#f26522"/>
  <circle cx="83" cy="83" r="4" fill="#f26522"/>
  <circle cx="83" cy="17" r="4" fill="#f26522"/>
  <circle cx="17" cy="83" r="4" fill="#f26522"/>
</svg>
"""

def get_logo(size=80):
    return INDIAN_RAILWAYS_LOGO_SVG.replace("{size}", str(size))
