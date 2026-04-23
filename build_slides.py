#!/usr/bin/env python3
import json, subprocess, sys

PRES_ID = "1dfUESOWN4W5ImnHSPgoCMDLTHfyXuSvxOr3Qp90ZQCc"
PROJ = "myee-gws"

TOKEN = subprocess.check_output(
    ["/Users/myee/Documents/google-cloud-sdk/bin/gcloud", "auth", "print-access-token"],
    text=True
).strip()

IMGS = {
    "cv_list": "1e0dDUW9oCJ1xpLFczWLaIMkiEgoqUpbP",
    "std_ver": "1BF7mfPzix_7UyaY8I2pgaObmj-Bn_7p-",
    "roll_detail": "1tXAz8ilcxzMuISUvOFDeqCg2gs_os-hj",
    "lifecycle": "1bS1pYicCEFnyNAwZeA5QGfiJTKK1rZK_",
    "errata": "1HnkL6od1TAfq20NIzBrB3fsMfIr4VwMp",
}

def img_url(key):
    return f"https://lh3.googleusercontent.com/d/{IMGS[key]}"

def emu(inches):
    return int(inches * 914400)

# Slide dimensions (widescreen 16:9)
W = emu(13.333)
H = emu(7.5)

# Colors
BG = {"red": 0.047, "green": 0.047, "blue": 0.047}  # #0C0C0C
CARD_BG = {"red": 0.102, "green": 0.102, "blue": 0.102}  # #1A1A1A
RED = {"red": 0.933, "green": 0, "blue": 0}  # #EE0000
WHITE = {"red": 0.91, "green": 0.91, "blue": 0.91}  # #E8E8E8
GRAY = {"red": 0.54, "green": 0.54, "blue": 0.54}  # #8A8A8A
BLUE = {"red": 0.302, "green": 0.639, "blue": 1.0}  # #4DA3FF
GREEN = {"red": 0.498, "green": 0.749, "blue": 0.373}  # #7FBF5F
ORANGE = {"red": 1.0, "green": 0.549, "blue": 0.353}  # #FF8C5A
DARK_RED = {"red": 0.165, "green": 0.059, "blue": 0.059}  # #2A0F0F

def text_style(color=WHITE, size=18, bold=False, font="Red Hat Text"):
    s = {
        "foregroundColor": {"opaqueColor": {"rgbColor": color}},
        "fontSize": {"magnitude": size, "unit": "PT"},
        "fontFamily": font,
    }
    if bold:
        s["bold"] = True
    return s

def create_slide_request(slide_id, layout="BLANK"):
    return {
        "createSlide": {
            "objectId": slide_id,
            "slideLayoutReference": {"predefinedLayout": layout},
        }
    }

def set_bg(slide_id, color=BG):
    return {
        "updatePageProperties": {
            "objectId": slide_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": color}}
                }
            },
            "fields": "pageBackgroundFill",
        }
    }

def add_textbox(page_id, obj_id, x, y, w, h, text, style=None, align="START", para_spacing=0):
    reqs = [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {"width": {"magnitude": emu(w), "unit": "EMU"}, "height": {"magnitude": emu(h), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(x), "translateY": emu(y), "unit": "EMU"},
                },
            }
        },
        {
            "insertText": {"objectId": obj_id, "text": text, "insertionIndex": 0}
        },
    ]
    if style:
        reqs.append({
            "updateTextStyle": {
                "objectId": obj_id,
                "style": style,
                "textRange": {"type": "ALL"},
                "fields": "foregroundColor,fontSize,fontFamily,bold",
            }
        })
    reqs.append({
        "updateParagraphStyle": {
            "objectId": obj_id,
            "style": {"alignment": align, "spaceAbove": {"magnitude": para_spacing, "unit": "PT"}},
            "textRange": {"type": "ALL"},
            "fields": "alignment,spaceAbove",
        }
    })
    reqs.append({
        "updateShapeProperties": {
            "objectId": obj_id,
            "shapeProperties": {"shapeBackgroundFill": {"propertyState": "NOT_RENDERED"}},
            "fields": "shapeBackgroundFill",
        }
    })
    return reqs

def add_rect(page_id, obj_id, x, y, w, h, fill=CARD_BG, border_color=None, border_weight=0, corner_radius=0):
    req = {
        "createShape": {
            "objectId": obj_id,
            "shapeType": "ROUND_RECTANGLE",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": {"magnitude": emu(w), "unit": "EMU"}, "height": {"magnitude": emu(h), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(x), "translateY": emu(y), "unit": "EMU"},
            },
        }
    }
    update = {
        "updateShapeProperties": {
            "objectId": obj_id,
            "shapeProperties": {
                "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fill}}},
                "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": border_color or fill}}}, "weight": {"magnitude": max(border_weight, 0.5), "unit": "PT"}},
            },
            "fields": "shapeBackgroundFill,outline",
        }
    }
    return [req, update]

def add_image(page_id, obj_id, img_key, x, y, w, h):
    return [{
        "createImage": {
            "objectId": obj_id,
            "url": img_url(img_key),
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": {"magnitude": emu(w), "unit": "EMU"}, "height": {"magnitude": emu(h), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(x), "translateY": emu(y), "unit": "EMU"},
            },
        }
    }]

def add_arrow(page_id, obj_id, x1, y1, x2, y2, color=GRAY):
    return [
        {
            "createLine": {
                "objectId": obj_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": emu(abs(x2-x1)) or 1, "unit": "EMU"},
                        "height": {"magnitude": emu(abs(y2-y1)) or 1, "unit": "EMU"},
                    },
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(min(x1,x2)), "translateY": emu(min(y1,y2)), "unit": "EMU"},
                },
            }
        },
        {
            "updateLineProperties": {
                "objectId": obj_id,
                "lineProperties": {
                    "lineFill": {"solidFill": {"color": {"rgbColor": color}}},
                    "weight": {"magnitude": 2, "unit": "PT"},
                    "endArrow": "OPEN_ARROW",
                },
                "fields": "lineFill,weight,endArrow",
            }
        }
    ]

# ============================================================
# BUILD ALL SLIDES
# ============================================================
requests = []

# Delete the default blank slide
requests.append({"deleteObject": {"objectId": "p"}})

slides = [
    # Section 1: Introduction
    ("slide00", "Rolling Content Views", "Red Hat Satellite", "A faster path from sync to server\nfor development and test environments"),
    ("slide01", "Content management at scale", None, None),
    ("slide02", "What is a Content View?", None, None),
    # Section 2: Standard CV
    ("slide03", "Standard Content View", "The publish and promote cycle", None),
    ("slide04", "Promotion through lifecycle environments", None, None),
    ("slide05", "The version accumulation problem", None, None),
    ("slide06", "Full standard CV workflow", None, None),
    ("slide07", "When new errata arrive", "Standard CV", None),
    # Section 3: Rolling CV
    ("slide08", "Rolling Content Views", "New in Satellite 6.18", None),
    ("slide09", "Rolling CV: the publishing process", None, None),
    ("slide10", "Rolling CV: full workflow", None, None),
    ("slide11", "Rolling CV: when new errata arrive", None, None),
    # Section 4: Comparison
    ("slide12", "Feature comparison", None, None),
    ("slide13", "CVE response timeline", None, None),
    ("slide14", "The hybrid approach", "Recommended", None),
    # Section 5: Summary
    ("slide15", "Key takeaways", None, None),
    ("slide16", "Get started", None, None),
]

for sid, title, subtitle, body in slides:
    requests.append(create_slide_request(sid))
    requests.append(set_bg(sid))

    # Title
    requests.extend(add_textbox(sid, f"{sid}_t", 0.7, 0.4, 11.9, 0.8, title,
        text_style(WHITE, 36, True, "Red Hat Display"), "START"))

    if subtitle:
        requests.extend(add_textbox(sid, f"{sid}_st", 0.7, 1.2, 11.9, 0.5, subtitle,
            text_style(RED if "New" in (subtitle or "") else GRAY, 18, False, "Red Hat Display"), "START"))

# ---- SLIDE 0: Title slide ----
requests.extend(add_rect("slide00", "slide00_bar", 0, 0, 13.333, 0.08, RED))
requests.extend(add_textbox("slide00", "slide00_body", 0.7, 2.8, 11.9, 1.5,
    "A faster path from sync to server\nfor development and test environments",
    text_style(GRAY, 24, False, "Red Hat Text"), "START"))

# ---- SLIDE 1: Content management at scale ----
for i, (t, desc) in enumerate([
    ("Manual publishing", "Every content update requires an admin to publish a new Content View version."),
    ("Promotion pipeline", "Each version must be promoted through Library, Dev, QA, and Production one at a time."),
    ("Time lag", "Security patches can take 2-4 weeks to reach even dev servers through the standard workflow."),
]):
    x = 0.7 + i * 4.1
    requests.extend(add_rect("slide01", f"slide01_c{i}", x, 1.8, 3.7, 2.5, CARD_BG, {"red":0.165,"green":0.165,"blue":0.165}, 1))
    requests.extend(add_textbox("slide01", f"slide01_ct{i}", x+0.3, 2.0, 3.1, 0.5, t,
        text_style(WHITE, 16, True, "Red Hat Display"), "START"))
    requests.extend(add_textbox("slide01", f"slide01_cd{i}", x+0.3, 2.6, 3.1, 1.5, desc,
        text_style(GRAY, 13, False, "Red Hat Text"), "START"))

requests.extend(add_rect("slide01", "slide01_callout", 0.7, 4.8, 11.9, 1.2, DARK_RED, RED, 1))
requests.extend(add_textbox("slide01", "slide01_call_t", 1.0, 4.9, 11.3, 1.0,
    "Business impact: Organizations managing 500+ hosts report spending 4-8 hours per week on content view management. For dev and test environments that simply need the latest content, this overhead delivers no value.",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 13, False, "Red Hat Text"), "START"))

# ---- SLIDE 2: What is a Content View + screenshot ----
requests.extend(add_textbox("slide02", "slide02_desc", 0.7, 1.3, 5.5, 1.0,
    "A Content View is a curated, filterable collection of repository content. It controls which packages, errata, and modules are available to your hosts.",
    text_style(GRAY, 14, False, "Red Hat Text"), "START"))
requests.extend(add_textbox("slide02", "slide02_repos", 0.7, 2.5, 5.5, 2.0,
    "Repositories:\n\n  RHEL 10 BaseOS  -  4,015 packages\n  RHEL 10 AppStream  -  9,162 packages\n  Satellite Client 6  -  10 packages\n\n  Total: 13,187 packages  |  3,224 errata",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 13, False, "Red Hat Mono"), "START"))
# IMG: requests.extend(add_image("slide02", "slide02_img", "cv_list", 6.5, 1.3, 6.3, 3.8))
requests.extend(add_textbox("slide02", "slide02_cap", 6.5, 5.2, 6.3, 0.4,
    "Content Views in Red Hat Satellite 6.19",
    text_style({"red":0.35,"green":0.35,"blue":0.35}, 10, False, "Red Hat Text"), "CENTER"))

# ---- SLIDE 4: Promotion + lifecycle screenshot ----
requests.extend(add_textbox("slide04", "slide04_desc", 0.7, 1.3, 5.8, 0.8,
    "After publishing, Version 1.0 exists only in Library.\nIt must be manually promoted to each successive environment.",
    text_style(GRAY, 14, False, "Red Hat Text"), "START"))
# Lifecycle boxes
for i, (env, clr) in enumerate([("Library", GREEN), ("Development", BLUE), ("Testing", BLUE), ("Production", BLUE)]):
    x = 0.7 + i * 3.1
    requests.extend(add_rect("slide04", f"slide04_e{i}", x, 2.4, 2.7, 0.9, {"red":clr["red"]*0.15,"green":clr["green"]*0.15,"blue":clr["blue"]*0.15}, clr, 2))
    requests.extend(add_textbox("slide04", f"slide04_et{i}", x+0.1, 2.5, 2.5, 0.7, f"{env}\nv1.0",
        text_style(clr, 14, True, "Red Hat Display"), "CENTER"))
    if i < 3:
        requests.extend(add_arrow("slide04", f"slide04_a{i}", 0.7+i*3.1+2.7, 2.85, 0.7+(i+1)*3.1, 2.85, BLUE))
# IMG: requests.extend(add_image("slide04", "slide04_img", "lifecycle", 0.7, 3.8, 11.9, 3.2))

# ---- SLIDE 6: Full workflow + standard CV screenshot ----
# IMG: requests.extend(add_image("slide06", "slide06_img", "std_ver", 0.7, 1.3, 11.9, 4.5))
requests.extend(add_textbox("slide06", "slide06_cap", 0.7, 5.9, 11.9, 0.5,
    "RHEL10-Standard-CV: Version 1.0 with 13,186 packages and 2,842 errata promoted across Library, Development, Testing, Production",
    text_style({"red":0.35,"green":0.35,"blue":0.35}, 11, False, "Red Hat Text"), "CENTER"))
requests.extend(add_rect("slide06", "slide06_callout", 0.7, 6.3, 11.9, 0.8, DARK_RED, RED, 1))
requests.extend(add_textbox("slide06", "slide06_call_t", 1.0, 6.4, 11.3, 0.6,
    "4 manual admin actions per content update (publish + 3 promotions). Each promotion requires validation time.",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 12, False, "Red Hat Text"), "START"))

# ---- SLIDE 9: Rolling CV publishing + screenshot ----
requests.extend(add_textbox("slide09", "slide09_desc", 0.7, 1.3, 5.5, 1.2,
    "A Rolling Content View is created with a single flag.\nNo versions. No publishing. No promotion.\nIt always reflects the latest synced content.\n\nPublish  →  Not needed\nPromote  →  Not needed",
    text_style(GRAY, 14, False, "Red Hat Text"), "START"))
# IMG: requests.extend(add_image("slide09", "slide09_img", "roll_detail", 6.5, 1.0, 6.3, 4.2))
requests.extend(add_textbox("slide09", "slide09_cap", 6.5, 5.3, 6.3, 0.4,
    "RHEL10-Rolling-CV — no publish or promote buttons, content always current",
    text_style({"red":0.35,"green":0.35,"blue":0.35}, 10, False, "Red Hat Text"), "CENTER"))
requests.extend(add_rect("slide09", "slide09_callout", 0.7, 5.8, 11.9, 1.0,
    {"red":0.078,"green":0.165,"blue":0.059}, GREEN, 1))
requests.extend(add_textbox("slide09", "slide09_ct", 1.0, 5.9, 11.3, 0.8,
    "Rolling CVs live in Library only. They have no versions, no publish step, and no promotion cycle. When repositories sync, the rolling view automatically reflects the new content.",
    text_style(GREEN, 12, False, "Red Hat Text"), "START"))

# ---- SLIDE 10: Rolling CV metrics ----
for i, (val, label, clr) in enumerate([("0", "Manual steps", GREEN), ("0 min", "Admin time per update", GREEN), ("Instant", "Time to availability", BLUE)]):
    x = 0.7 + i * 4.1
    requests.extend(add_rect("slide10", f"slide10_m{i}", x, 2.0, 3.7, 2.0, CARD_BG, {"red":0.165,"green":0.165,"blue":0.165}, 1))
    requests.extend(add_textbox("slide10", f"slide10_mv{i}", x+0.2, 2.2, 3.3, 0.9, val,
        text_style(clr, 36, True, "Red Hat Display"), "CENTER"))
    requests.extend(add_textbox("slide10", f"slide10_ml{i}", x+0.2, 3.2, 3.3, 0.5, label,
        text_style(GRAY, 13, False, "Red Hat Text"), "CENTER"))

# ---- SLIDE 11: Errata comparison + screenshot ----
# IMG: requests.extend(add_image("slide11", "slide11_img", "errata", 0.7, 1.2, 5.5, 3.0))
# Standard side
requests.extend(add_rect("slide11", "slide11_std", 6.5, 1.2, 3.1, 5.0, {"red":0.165,"green":0.1,"blue":0.059}, ORANGE, 1.5))
requests.extend(add_textbox("slide11", "slide11_stdt", 6.7, 1.3, 2.7, 0.4, "Standard CV",
    text_style(ORANGE, 14, True, "Red Hat Display"), "CENTER"))
requests.extend(add_textbox("slide11", "slide11_stdb", 6.7, 1.8, 2.7, 4.0,
    "1. Publish new version\n2. Promote to Dev\n3. Validate (1-3 days)\n4. Promote to Testing\n5. Validate (3-7 days)\n6. Promote to Production\n\n~14 days",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 12, False, "Red Hat Text"), "START"))
# Rolling side
requests.extend(add_rect("slide11", "slide11_roll", 9.9, 1.2, 3.1, 5.0, {"red":0.078,"green":0.165,"blue":0.059}, GREEN, 1.5))
requests.extend(add_textbox("slide11", "slide11_rollt", 10.1, 1.3, 2.7, 0.4, "Rolling CV",
    text_style(GREEN, 14, True, "Red Hat Display"), "CENTER"))
requests.extend(add_textbox("slide11", "slide11_rollb", 10.1, 1.8, 2.7, 4.0,
    "Repository syncs.\nRolling CV auto-updates.\nHosts receive new errata.\n\n\n\nDay 0\nZero admin time",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 12, False, "Red Hat Text"), "START"))

# ---- SLIDE 12: Feature comparison table ----
headers = ["Feature", "Standard CV", "Rolling CV"]
rows = [
    ("Content updates", "Manual publish required", "Auto-updated on sync"),
    ("Versioning", "Explicit (v1.0, v1.1...)", "No versions, always latest"),
    ("Publishing", "Required for every update", "Not needed"),
    ("Promotion", "Must promote through envs", "Library only, no promotion"),
    ("Rollback", "Yes, promote previous", "No version history"),
    ("Admin overhead", "High (publish + promote)", "None"),
    ("Best for", "Production", "Dev / Test"),
]
for col, hdr in enumerate(headers):
    x = 0.7 + col * 4.1
    requests.extend(add_rect("slide12", f"slide12_h{col}", x, 1.3, 3.8, 0.5, {"red":0.165,"green":0.165,"blue":0.165}))
    requests.extend(add_textbox("slide12", f"slide12_ht{col}", x+0.2, 1.35, 3.4, 0.4, hdr,
        text_style(WHITE, 12, True, "Red Hat Display"), "START"))
for row, (feat, std, roll) in enumerate(rows):
    y = 1.9 + row * 0.65
    clr_bg = BG if row % 2 == 0 else CARD_BG
    for col, val in enumerate([feat, std, roll]):
        x = 0.7 + col * 4.1
        c = WHITE if col == 0 else (ORANGE if col == 1 and "Manual" in val or "Required" in val or "High" in val or "Must" in val else GREEN if col == 2 and ("Auto" in val or "Not" in val or "None" in val or "Library" in val) else GRAY)
        requests.extend(add_textbox("slide12", f"slide12_r{row}c{col}", x+0.2, y, 3.4, 0.55, val,
            text_style(c, 11, col==0, "Red Hat Text"), "START"))

# ---- SLIDE 14: Hybrid approach ----
# Dev lane
requests.extend(add_rect("slide14", "slide14_dev", 0.7, 1.8, 5.8, 2.2, {"red":0.078,"green":0.165,"blue":0.059}, GREEN, 1.5))
requests.extend(add_textbox("slide14", "slide14_devt", 1.0, 1.9, 5.2, 0.4, "Dev & Test lane",
    text_style(GREEN, 16, True, "Red Hat Display"), "START"))
requests.extend(add_textbox("slide14", "slide14_devb", 1.0, 2.5, 5.2, 1.2,
    "Rolling CV  →  Auto-updated  →  Dev & Test Hosts\n\nZero overhead. Content available immediately on sync.",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 13, False, "Red Hat Text"), "START"))

# Prod lane
requests.extend(add_rect("slide14", "slide14_prod", 0.7, 4.3, 5.8, 2.5, {"red":0.05,"green":0.13,"blue":0.25}, BLUE, 1.5))
requests.extend(add_textbox("slide14", "slide14_prodt", 1.0, 4.4, 5.2, 0.4, "Production lane",
    text_style(BLUE, 16, True, "Red Hat Display"), "START"))
requests.extend(add_textbox("slide14", "slide14_prodb", 1.0, 5.0, 5.2, 1.5,
    "Standard CV  →  Publish v N.0  →  Dev  →  QA  →  Prod\n\nVersioned, rollback-capable, staged promotion.",
    text_style({"red":0.69,"green":0.69,"blue":0.69}, 13, False, "Red Hat Text"), "START"))

# Guidance cards
for i, (env, desc, clr) in enumerate([
    ("Development", "Use Rolling CV.\nAlways latest. Zero overhead.", GREEN),
    ("Test / QA", "Rolling CV for latest, or\nStandard CV for reproducible envs.", {"red":0.373,"green":0.808,"blue":0.808}),
    ("Production", "Use Standard CV.\nVersion control, rollback, staged.", BLUE),
]):
    x = 7.0 + i * 0 # stack vertically
    y = 1.8 + i * 1.9
    requests.extend(add_rect("slide14", f"slide14_g{i}", 7.0, y, 5.8, 1.5, CARD_BG, clr, 2))
    requests.extend(add_textbox("slide14", f"slide14_gt{i}", 7.3, y+0.15, 5.2, 0.4, env,
        text_style(clr, 14, True, "Red Hat Display"), "START"))
    requests.extend(add_textbox("slide14", f"slide14_gd{i}", 7.3, y+0.6, 5.2, 0.8, desc,
        text_style(GRAY, 12, False, "Red Hat Text"), "START"))

# ---- SLIDE 15: Key takeaways ----
takeaways = [
    "Rolling CVs eliminate the publish and promote cycle for dev and test, removing all manual overhead.",
    "Content updates are available immediately upon repository sync. No waiting, no intervention.",
    "Hybrid approach: Rolling CVs for dev and test, Standard CVs for production.",
    "Available in Red Hat Satellite 6.18+. Supported via Web UI, Hammer CLI, API, and Ansible.",
]
for i, t in enumerate(takeaways):
    y = 1.5 + i * 1.3
    requests.extend(add_rect("slide15", f"slide15_c{i}", 0.7, y, 11.9, 1.0, CARD_BG, {"red":0.165,"green":0.165,"blue":0.165}, 1))
    requests.extend(add_textbox("slide15", f"slide15_ct{i}", 1.2, y+0.15, 11.0, 0.7, t,
        text_style({"red":0.82,"green":0.82,"blue":0.82}, 14, False, "Red Hat Text"), "START"))

# Metrics
for i, (val, label) in enumerate([("30-60 min", "Saved per update"), ("Days → Minutes", "Patch availability"), ("4 of 6", "Steps eliminated")]):
    x = 0.7 + i * 4.1
    clr = RED if i == 0 else GREEN if i == 1 else BLUE
    requests.extend(add_rect("slide15", f"slide15_m{i}", x, 6.0, 3.7, 1.1, CARD_BG, {"red":0.165,"green":0.165,"blue":0.165}, 1))
    requests.extend(add_textbox("slide15", f"slide15_mv{i}", x+0.2, 6.05, 3.3, 0.55, val,
        text_style(clr, 22, True, "Red Hat Display"), "CENTER"))
    requests.extend(add_textbox("slide15", f"slide15_ml{i}", x+0.2, 6.6, 3.3, 0.4, label,
        text_style(GRAY, 11, False, "Red Hat Text"), "CENTER"))

# ---- SLIDE 16: Get started ----
steps = [
    ("Upgrade to Satellite 6.18 or later", "Rolling Content Views require Satellite 6.18+"),
    ("Identify dev and test Content Views", "Which environments simply need the latest content?"),
    ("Create Rolling Content Views", "Replace standard CVs for non-production environments"),
    ("Keep Standard CVs for production", "Maintain version control and staged rollouts"),
]
requests.extend(add_rect("slide16", "slide16_box", 0.7, 1.3, 7.5, 5.0, CARD_BG, RED, 2))
for i, (title, desc) in enumerate(steps):
    y = 1.6 + i * 1.1
    requests.extend(add_textbox("slide16", f"slide16_n{i}", 1.0, y, 0.5, 0.4, str(i+1),
        text_style(RED, 16, True, "Red Hat Display"), "CENTER"))
    requests.extend(add_textbox("slide16", f"slide16_t{i}", 1.6, y, 6.3, 0.35, title,
        text_style(WHITE, 14, True, "Red Hat Text"), "START"))
    requests.extend(add_textbox("slide16", f"slide16_d{i}", 1.6, y+0.4, 6.3, 0.35, desc,
        text_style(GRAY, 11, False, "Red Hat Text"), "START"))

# Resources
resources = ["Red Hat Satellite documentation", "Managing Content Views guide", "Satellite 6.18 release notes", "RH403 - Red Hat Satellite Administration"]
for i, r in enumerate(resources):
    y = 1.5 + i * 0.6
    requests.extend(add_textbox("slide16", f"slide16_r{i}", 8.8, y, 4.2, 0.5, f"•  {r}",
        text_style(GRAY, 12, False, "Red Hat Text"), "START"))

requests.extend(add_rect("slide16", "slide16_brand", 8.8, 5.5, 4.2, 0.8, RED))
requests.extend(add_textbox("slide16", "slide16_brandt", 8.8, 5.6, 4.2, 0.6, "Red Hat Satellite",
    text_style(WHITE, 18, True, "Red Hat Display"), "CENTER"))

# ============================================================
# SEND BATCH UPDATE
# ============================================================
import urllib.request

data = json.dumps({"requests": requests}).encode()
req = urllib.request.Request(
    f"https://slides.googleapis.com/v1/presentations/{PRES_ID}:batchUpdate",
    data=data,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "x-goog-user-project": PROJ,
    },
    method="POST",
)

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print(f"Success! {len(result.get('replies', []))} operations applied.")
    print(f"\nPresentation URL:\nhttps://docs.google.com/presentation/d/{PRES_ID}/edit")
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    print(f"Error {e.code}: {error_body[:2000]}")
    sys.exit(1)
