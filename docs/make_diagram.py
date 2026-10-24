# make_diagram.py — draw the Hearthwatch architecture diagram as SVG.
# Pure text output: no drawing tool needed, and the diagram stays
# version-controlled next to the code it describes.

# Box layout: (x, y, width, height, title, lines of small text).
BOXES = [
    (20, 30, 170, 90, "Camera feed",
     ["Household camera", "640x360, ~10 fps", "or test-scene video"]),
    (230, 30, 200, 90, "Perception (OpenCV 5)",
     ["MOG2 motion", "Contours + HSV glow", "Centroid tracking"]),
    (470, 30, 200, 90, "Agent loop",
     ["Risk scoring", "Action tiers", "Re-observation"]),
    (700, 30, 170, 90, "Household",
     ["Open alerts", "Acknowledge", "False-alarm feedback"]),
    (230, 170, 200, 90, "Event store (in-memory)",
     ["Events + alert states", "Thresholds", "Feedback history"]),
    (470, 170, 200, 90, "Demo server (stdlib)",
     ["Single-page UI", "/api/run, /api/scenes", "Annotated video out"]),
    (700, 170, 170, 90, "AWS path (sketched)",
     ["ECS Fargate + ALB", "Same container", "Not yet executed*"]),
]

# Arrows between boxes, as (from-box-index, to-box-index, label).
ARROWS = [
    (0, 1, "frames"),
    (1, 2, "detections"),
    (2, 3, "alerts"),
    (3, 2, "feedback"),
    (2, 4, "events"),
    (2, 5, "status"),
    (5, 6, "deploy when account exists"),
]


# Draw one box with a title and small text lines.
def box_svg(x, y, w, h, title, lines):
    # The rectangle itself, with a light fill and dark border.
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
    out += 'fill="#eef4ff" stroke="#335" stroke-width="2" rx="8"/>\n'
    # The title, bold and centred.
    out += f'<text x="{x + w // 2}" y="{y + 24}" text-anchor="middle" '
    out += 'font-family="sans-serif" font-size="14" font-weight="bold">'
    out += f"{title}</text>\n"
    # The detail lines, centred below the title.
    for i, line in enumerate(lines):
        out += f'<text x="{x + w // 2}" y="{y + 46 + i * 18}" '
        out += 'text-anchor="middle" font-family="sans-serif" font-size="11">'
        out += f"{line}</text>\n"
    return out


# Draw one arrow between the centres of two boxes' facing edges.
def arrow_svg(b1, b2, label):
    # Start at the right edge of the first box, end at the left edge
    # of the second box (or below, for the feedback arrow).
    x1 = b1[0] + b1[2]
    y1 = b1[1] + b1[3] // 2
    x2 = b2[0]
    y2 = b2[1] + b2[3] // 2
    # The feedback arrow (household back to agent) goes underneath.
    if b1[3] == 170 or (b1[0] > b2[0]):
        x1 = b1[0] + b1[2] // 2
        y1 = b1[1] + b1[3]
        x2 = b2[0] + b2[2] // 2
        y2 = b2[1]
    out = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    out += 'stroke="#335" stroke-width="2" marker-end="url(#arrow)"/>\n'
    # The label sits at the arrow's midpoint, slightly above.
    out += f'<text x="{(x1 + x2) // 2}" y="{(y1 + y2) // 2 - 6}" '
    out += 'text-anchor="middle" font-family="sans-serif" font-size="11">'
    out += f"{label}</text>\n"
    return out


# Build the full SVG document and print it to stdout.
def main():
    print('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320">')
    # Arrowhead marker definition, reused by every arrow.
    print('<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
          'refX="9" refY="3" orient="auto">'
          '<path d="M0,0 L9,3 L0,6 Z" fill="#335"/></marker></defs>')
    for (x, y, w, h, title, lines) in BOXES:
        print(box_svg(x, y, w, h, title, lines))
    for (i, j, label) in ARROWS:
        print(arrow_svg(BOXES[i], BOXES[j], label))
    # Footnote explaining the asterisk on the AWS box.
    print('<text x="20" y="300" font-family="sans-serif" font-size="11" '
          'fill="#555">* AWS execution needs an account; a standard account '
          'needs a card on file, which the operator does not file. '
          'See aws-deploy/ECS-DEPLOY.md.</text>')
    print("</svg>")


# Run the generator when this file is executed directly.
if __name__ == "__main__":
    main()
