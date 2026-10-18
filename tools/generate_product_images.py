"""
======================================================================
 tools/generate_product_images.py
======================================================================

WHY THIS SCRIPT EXISTS
    A portfolio project full of grey "no image" placeholders looks
    unfinished. This script draws a clean, consistent illustration for
    every product so the shop looks like a real shop.

    The pictures are plain SVG (vector) files, which means they stay
    sharp on any screen, weigh almost nothing, and need no image
    library at all.

WHAT IT DOES
    1. Draws one SVG per product into  static/images/products/
    2. Writes the file name back into the products table, so the shop
       starts showing the new pictures

HOW TO RUN IT
    python tools/generate_product_images.py

    Run it again any time you want to tweak the colours or shapes -
    it only ever touches these 12 illustration files, never the real
    photos you upload through the admin panel.

DESIGN NOTES
    * Canvas is 800x600 (4:3) to match the card size in style.css
    * Every icon is drawn in white line-art on a two-tone gradient
      taken from the product's category, so the shop looks coherent
    * Built from three reusable pieces: background(), badge() and a
      per-product icon() function
======================================================================
"""

import os
import sys
import xml.etree.ElementTree as ElementTree

# Allow "python tools/generate_product_images.py" from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, execute, query_all  # noqa: E402

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "images", "products"
)

CANVAS_W, CANVAS_H = 800, 600

# Two gradient tones per category. Light on the left, deeper on the
# right, so the cards feel bright but not washed out.
CATEGORY_THEME = {
    "mobiles-tablets":     ("#6366f1", "#4338ca"),
    "laptops-computers":   ("#0ea5e9", "#0369a1"),
    "audio":               ("#a855f7", "#7e22ce"),
    "home-kitchen":        ("#fb923c", "#c2410c"),
    "fashion":             ("#fb7185", "#be123c"),
    "books-stationery":    ("#f59e0b", "#b45309"),
    "default":             ("#818cf8", "#4f46e5"),
}

# The common line-art style, so all icons look like one family.
STROKE = 'stroke="#ffffff" stroke-width="7" stroke-linecap="round" ' \
         'stroke-linejoin="round" fill="none"'


def background(from_colour, to_colour):
    """The gradient panel plus two soft circles for a bit of depth."""
    return f'''
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="{from_colour}"/>
      <stop offset="100%" stop-color="{to_colour}"/>
    </linearGradient>
  </defs>
  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="url(#bg)"/>
  <circle cx="655" cy="118" r="168" fill="#ffffff" opacity="0.09"/>
  <circle cx="132" cy="512" r="132" fill="#ffffff" opacity="0.07"/>
  <circle cx="400" cy="300" r="196" fill="#ffffff" opacity="0.10"/>'''


def wrap(name, from_colour, to_colour, icon_svg):
    """Assemble one finished SVG file."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}"
     height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}"
     role="img" aria-label="{name} illustration">
  <title>{name}</title>{background(from_colour, to_colour)}
  <g transform="translate(400 300)">
{icon_svg}
  </g>
</svg>
'''


# ======================================================================
#  The icons. Each one draws around the centre (0,0) in roughly a
#  300x300 box, so they all line up optically.
# ======================================================================


def phone():
    return f'''    <g {STROKE}>
      <rect x="-72" y="-132" width="144" height="264" rx="24"/>
      <line x1="-30" y1="-108" x2="30" y2="-108"/>
      <circle cx="0" cy="108" r="11"/>
      <line x1="-46" y1="-58" x2="46" y2="-58"/>
      <line x1="-46" y1="-30" x2="46" y2="-30"/>
      <line x1="-46" y1="-2"  x2="20" y2="-2"/>
    </g>'''


def earbuds():
    return f'''    <g {STROKE}>
      <rect x="-96" y="18" width="192" height="104" rx="26"/>
      <line x1="-96" y1="70" x2="96" y2="70"/>
      <circle cx="-58" cy="42" r="9"/>
      <g>
        <path d="M-70 -18 a34 34 0 1 0 34 34 l14 -14 v-38 z"/>
        <path d="M70 -18 a34 34 0 1 1 -34 34 l-14 -14 v-38 z"/>
      </g>
      <line x1="-22" y1="-132" x2="22" y2="-132" opacity="0.7"/>
      <line x1="0" y1="-132" x2="0" y2="-108" opacity="0.7"/>
    </g>'''


def laptop():
    return f'''    <g {STROKE}>
      <rect x="-124" y="-122" width="248" height="164" rx="14"/>
      <line x1="-100" y1="-98" x2="-24" y2="-98"/>
      <line x1="-100" y1="-70" x2="10" y2="-70"/>
      <line x1="-100" y1="-42" x2="-46" y2="-42"/>
      <path d="M-124 42 h248 l30 52 a10 10 0 0 1 -9 15 h-290
               a10 10 0 0 1 -9 -15 z"/>
      <line x1="-42" y1="72" x2="42" y2="72" opacity="0.7"/>
    </g>'''


def desk_lamp():
    return f'''    <g {STROKE}>
      <path d="M-74 132 h148 a10 10 0 0 1 10 10 v10 h-168 v-10
               a10 10 0 0 1 10 -10 z"/>
      <line x1="0" y1="132" x2="0" y2="42"/>
      <path d="M0 42 l64 -74"/>
      <path d="M40 -104 l84 46 l-34 62 l-84 -46 z"/>
      <line x1="-30" y1="-26" x2="30" y2="-26" opacity="0.55"/>
      <line x1="-22" y1="2" x2="22" y2="2" opacity="0.55"/>
    </g>'''


def jacket():
    return f'''    <g {STROKE}>
      <path d="M-38 -122 l-72 34 l-34 96 l48 20 l22 -50 v146 h148
               v-146 l22 50 l48 -20 l-34 -96 l-72 -34 l-38 44 z"/>
      <path d="M-38 -122 l38 44 l38 -44"/>
      <line x1="0" y1="-78" x2="0" y2="122"/>
      <line x1="-22" y1="24" x2="22" y2="24" opacity="0.6"/>
    </g>'''


def book():
    return f'''    <g {STROKE}>
      <path d="M-96 -128 h150 a16 16 0 0 1 16 16 v244
               a12 12 0 0 0 -12 -12 h-154 z"/>
      <line x1="-96" y1="110" x2="70" y2="110" opacity="0.6"/>
      <line x1="70" y1="-128" x2="70" y2="126"/>
      <line x1="-64" y1="-78" x2="38" y2="-78" opacity="0.6"/>
      <line x1="-64" y1="-46" x2="38" y2="-46" opacity="0.6"/>
      <line x1="-64" y1="-14" x2="10" y2="-14" opacity="0.6"/>
    </g>'''


def shoe():
    return f'''    <g {STROKE}>
      <path d="M-136 68 v-40 c0 -12 10 -22 22 -22 l52 6 l46 -52
               c8 -9 20 -12 31 -8 l58 22 c26 10 43 30 43 56 v38
               a10 10 0 0 1 -10 10 h-232 a10 10 0 0 1 -10 -10 z"/>
      <path d="M-136 38 h252"/>
      <path d="M-34 12 l30 -34 M4 22 l30 -34" opacity="0.65"/>
    </g>'''


def coffee_maker():
    return f'''    <g {STROKE}>
      <rect x="-116" y="-134" width="232" height="66" rx="16"/>
      <circle cx="-64" cy="-101" r="13"/>
      <line x1="-20" y1="-101" x2="72" y2="-101"/>
      <path d="M-78 -68 v22 h86 v-22"/>
      <path d="M8 -46 v72"/>
      <path d="M-78 26 h172 a10 10 0 0 1 10 10 v78
               a20 20 0 0 1 -20 20 h-152 a20 20 0 0 1 -20 -20 v-78
               a10 10 0 0 1 10 -10 z"/>
      <path d="M104 52 h22 a26 26 0 0 1 0 52 h-22" opacity="0.7"/>
      <line x1="-58" y1="76" x2="90" y2="76" opacity="0.55"/>
    </g>'''


def notebooks():
    return f'''    <g {STROKE}>
      <rect x="-118" y="-96" width="176" height="216" rx="14"
            opacity="0.55"/>
      <rect x="-72" y="-116" width="176" height="216" rx="14"
            opacity="0.78"/>
      <rect x="-26" y="-136" width="176" height="216" rx="14"/>
      <line x1="110" y1="-104" x2="110" y2="48" opacity="0.6"/>
      <line x1="-2" y1="-84" x2="126" y2="-84" opacity="0.6"/>
      <line x1="-2" y1="-56" x2="126" y2="-56" opacity="0.6"/>
      <line x1="-2" y1="-28" x2="86" y2="-28" opacity="0.6"/>
    </g>'''


def speaker():
    return f'''    <g {STROKE}>
      <rect x="-98" y="-130" width="196" height="260" rx="40"/>
      <circle cx="0" cy="34" r="62"/>
      <circle cx="0" cy="34" r="26"/>
      <circle cx="0" cy="-76" r="24"/>
      <line x1="-30" y1="-128" x2="30" y2="-128" opacity="0.6"/>
    </g>'''


def monitor():
    return f'''    <g {STROKE}>
      <rect x="-148" y="-118" width="296" height="188" rx="14"/>
      <line x1="-120" y1="-86" x2="20" y2="-86" opacity="0.6"/>
      <line x1="-120" y1="-58" x2="60" y2="-58" opacity="0.6"/>
      <line x1="-120" y1="-30" x2="-10" y2="-30" opacity="0.6"/>
      <line x1="0" y1="70" x2="0" y2="112"/>
      <path d="M-70 130 h140 a10 10 0 0 0 10 -10 v-18 h-160 v18
               a10 10 0 0 0 10 10 z"/>
    </g>'''


def mug():
    return f'''    <g {STROKE}>
      <path d="M-88 -74 h150 v108 a44 44 0 0 1 -44 44 h-62
               a44 44 0 0 1 -44 -44 z"/>
      <path d="M62 -52 h26 a34 34 0 0 1 0 68 h-26" opacity="0.75"/>
      <line x1="-88" y1="-30" x2="62" y2="-30" opacity="0.5"/>
      <path d="M-34 -134 c-14 14 14 24 0 38" opacity="0.6"/>
      <path d="M6 -134 c-14 14 14 24 0 38" opacity="0.6"/>
      <line x1="-88" y1="112" x2="62" y2="112" opacity="0.5"/>
    </g>'''


# ======================================================================
#  Which picture belongs to which product. Keyed on the product slug,
#  which never changes - so this stays correct even after a rename.
# ======================================================================
ICON_FOR_SLUG = {
    "nova-x1-smartphone":     phone,
    "pulse-wireless-earbuds": earbuds,
    "vertex-14-laptop":       laptop,
    "lumen-desk-lamp":        desk_lamp,
    "classic-denim-jacket":   jacket,
    "the-practical-programmer": book,
    "aero-running-shoes":     shoe,
    "brew-master-coffee-maker": coffee_maker,
    "notebook-pack-of-5":     notebooks,
    "echo-bluetooth-speaker": speaker,
    "glow-led-monitor-24-inch": monitor,
    "zen-ceramic-mug-set":    mug,
}


def validate(svg_text):
    """
    Parse the SVG before we save it.

    A single typo in a path (a <line> missing its x2, say) produces a
    file that browsers silently refuse to draw, which shows up as a
    blank product card with no error message anywhere. Checking here
    turns that silent failure into a loud one.

    Returns None when the SVG is valid, or an error string when not.
    """
    try:
        root = ElementTree.fromstring(svg_text)
    except ElementTree.ParseError as error:
        return f"not valid XML - {error}"

    if not root.tag.endswith("svg"):
        return "the root element is not <svg>"

    # Every <line> needs two points, otherwise browsers draw nothing.
    for element in root.iter():
        if element.tag.endswith("line"):
            has_both_points = ("x1" in element.attrib and "x2" in element.attrib
                               and "y1" in element.attrib and "y2" in element.attrib)
            if not has_both_points:
                return "a <line> is missing x2/y2 coordinates"
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with app.app_context():
        products = query_all(
            """SELECT p.id, p.name, p.slug, c.slug AS category_slug
               FROM products p
               LEFT JOIN categories c ON c.id = p.category_id"""
        )

        if not products:
            print("\n  No products found. Run database/seed.sql first.\n")
            return 1

        print(f"\nDrawing {len(products)} product illustrations...\n")
        problems = 0

        for product in products:
            icon = ICON_FOR_SLUG.get(product["slug"])
            if icon is None:
                print(f"  --  {product['name']}: no icon mapped, skipped")
                continue

            theme = CATEGORY_THEME.get(
                product["category_slug"], CATEGORY_THEME["default"]
            )
            file_name = f"{product['slug']}.svg"
            svg = wrap(product["name"], theme[0], theme[1], icon())

            # Never write or reference a broken picture.
            error = validate(svg)
            if error:
                print(f"  XX  {file_name}: {error}  (not saved)")
                problems += 1
                continue

            path = os.path.join(OUTPUT_DIR, file_name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(svg)

            # Point the database at the new picture. We store only the
            # folder name; app.py adds static/images/ in front of it.
            execute("UPDATE products SET image = %s WHERE id = %s",
                    (f"products/{file_name}", product["id"]))
            print(f"  OK  {file_name}")

    print(f"\nDone. Pictures written to  static/images/products/")
    if problems:
        print(f"WARNING: {problems} picture(s) were skipped because they "
              f"were malformed.")
    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())