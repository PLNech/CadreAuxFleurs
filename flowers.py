#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glitch_unicode_flowers_v11.py - Enhanced

- Deux lignes de citation centrées en jaune.
- Fragments des deux prochaines citations dispersés hors centre.
- Glitch autour, diminuant progressivement.
- Superposition d’ASCII fleurs MONOSPACE uniquement, avec couleurs variées.
- Effet vague : densité de fleurs croissante selon une courbe douce.
- Explosion florale intégrée à la courbe de densité croissante.
- Chaque citation (paire de lignes) dure `duration` secondes.
- 95% de chances de rester dans le même poème.
- Auteur et titre affichés FIXES (pas de clignotement) : auteur en haut gauche, titre en bas droite.
- Pool unicode redivisé : UNICODE_POOL pour bruit, FLOWERS pour fleurs exotiques.
- Taille fixe respectée par rognage du contenu.
"""
import json
import random
import sys
import time
import argparse

# ── CONFIG ARGPARSE ───────────────────────────────────────────
parser = argparse.ArgumentParser(description="Affichage poétique glitché à base de fleurs.")
parser.add_argument("--width", type=int, default=50, help="Largeur du canvas")
parser.add_argument("--height", type=int, default=20, help="Hauteur du canvas")
parser.add_argument("--duration", type=float, default=30.0, help="Durée de chaque citation (en secondes)")
parser.add_argument("--frames", type=int, default=50, help="Nombre de frames par citation")
parser.add_argument("--max_flow", type=float, default=0.15, help="Densité maximale de fleurs à la fin (sur 1.0)")
parser.add_argument("--file", type=str, default="poemes.json", help="Fichier JSON contenant les poèmes")
args = parser.parse_args()

POEM_FILE       = args.file
WIDTH, HEIGHT   = args.width, args.height
FRAMES          = args.frames
total_duration  = args.duration
DELAY           = total_duration / FRAMES
GLITCH_PROB_MAX = 0.20 # Max glitch probability at the start
FRAG_PROB       = 0.05 # Probability for a fragment to appear in non-centered area
MAX_FLOWER_PROB = args.max_flow
STAY_PROB       = 0.95 # Probability to stay in the same poem for the next quote
FLOWER_DENSITY_POWER = 4.0 # Power for the flower density curve (higher = slower start, faster end)

# Ensure minimum height for two lines + author/title
if HEIGHT < 4:
    print("Warning: Height is less than 4, author/title/two lines might overlap heavily.", file=sys.stderr)
    # Minimum reasonable height to avoid immediate conflicts (auth/title at ends, lines in middle)
    # if h=3, auth at 0, lines at 0/1 or 1/2, title at 2 (conflicts)
    # if h=4, auth at 0, lines at 1/2, title at 3 (no conflicts)
    # Let's enforce a minimum height that makes visual sense
    if HEIGHT < 4:
         print("Error: Minimum height of 4 required for separate author/title/lines.", file=sys.stderr)
         sys.exit(1)


UNICODE_POOL    = [
    '◻', '◼', '◇', '◆', '○', '●', '□', '■',
    '◢', '◣', '◤', '◥', '▦', '▧', '▨', '▩',
    '▪', '▫', '⬛', '⬜', '◉', '◌', '◍', '◊'
]

FLOWERS = [
    '⁅', '⚘', '𓅗', '𓅘', '𓆷', '𓆸', '𓆻',
    '𓇖', '𓇗', '𓇘', '𓇙', '𓇬', '𓆇', '𓆈',
    # Add more exotic or interesting flower-like chars if needed, ensuring monospace where possible
    # '🌸', '🌼', '🌻', '🌺', '🥀', '🌷', '🏵️', '💮', '🌴', '🌵', '🎄', '🌳', '🌲', '🌿', '🍀', '🍁', '🍂', '🍃' # These are multi-byte and might not be monospace or cause issues
    # Sticking to more abstract/geometric ones for better compatibility
    '✿', '❀', '❁', '❃', '❊', '❋', '❄', '❅' # These are generally better behaved
]

ANSI_CLEAR      = "\033[H\033[J"
ANSI_YELLOW     = "\033[93m"
ANSI_MAGENTA    = "\033[95m"
ANSI_GREEN      = "\033[92m" # New color
ANSI_CYAN       = "\033[96m" # New color
ANSI_RESET      = "\033[0m"

FLOWER_COLORS = [ANSI_MAGENTA, ANSI_GREEN, ANSI_CYAN] # Pool of colors for flowers

END_NOTICE = r"""
Bonne Fête des Fleurs!
      _,-._
     / \_/ \
    >-(_)-<
     \_/ \_/
       -'
"""

# ── HELPERS ────────────────────────────────────────────
def clear():
    """Clears the terminal screen."""
    sys.stdout.write(ANSI_CLEAR)
    sys.stdout.flush()

def load_poems():
    """Loads poems from the specified JSON file."""
    try:
        with open(POEM_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Poem file '{POEM_FILE}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{POEM_FILE}'. Ensure it's valid JSON.", file=sys.stderr)
        sys.exit(1)

    poems = []
    for poem in data.get("poems", []):
        lines = [l.strip() for l in poem.get("text", "").splitlines() if l.strip()]
        # A poem needs at least two lines to be displayed as a pair
        if not lines or len(lines) < 2:
            # print(f"Warning: Skipping poem with insufficient lines: {poem.get('title', 'Untitled')}", file=sys.stderr)
            continue # Skip poems with less than 2 lines

        poems.append({
            'author': poem.get('author',''),
            'title' : poem.get('title',''),
            'lines' : lines
        })

    if not poems:
        print(f"Error: No valid poems with at least two lines found in '{POEM_FILE}'.", file=sys.stderr)
        sys.exit(1)

    return poems

def pick_next(poems, current_pi, current_li1):
    """Picks the next poem and the starting index for the next pair of lines."""
    num_poems = len(poems)
    current_poem_len = len(poems[current_pi]['lines'])

    if random.random() < STAY_PROB and current_poem_len >= 2:
        # Stay in the same poem, move to the next pair of lines
        # If current lines are i, i+1, next lines are (i+2)%len, (i+3)%len
        next_li1 = (current_li1 + 2) % current_poem_len
        return current_pi, next_li1
    else:
        # Switch to a new poem
        new_pi = random.randrange(num_poems)
        # Pick a random starting line index (li1). Ensure the poem has at least 2 lines.
        # The load_poems function already filters for poems with >= 2 lines.
        new_poem_len = len(poems[new_pi]['lines'])
        new_li1 = random.randrange(new_poem_len)
        return new_pi, new_li1

def random_canvas(w, h):
    """Creates a canvas filled with random unicode pool characters."""
    return [''.join(random.choice(UNICODE_POOL) for _ in range(w)) for _ in range(h)]

def overlay_flowers(tokens, frame_idx):
    """Overlays flowers with increasing density and varied colors."""
    h, w = len(tokens), len(tokens[0])
    frac = (frame_idx + 1) / FRAMES

    # Flower density follows a power curve for smoother ramp-up
    # frac is from 0 to 1. frac**power makes density grow slower initially, faster later.
    density = MAX_FLOWER_PROB * (frac ** FLOWER_DENSITY_POWER)

    for y in range(h):
        for x in range(w):
            # Ensure we don't overwrite Author/Title lines with low density flowers right away,
            # only overlay heavily towards the end. Or simply overlay everything?
            # Let's overlay everything for simplicity, as per the "Superposition" note.
            if random.random() < density:
                flower = random.choice(FLOWERS)
                color = random.choice(FLOWER_COLORS) # Pick a random color
                tokens[y][x] = f"{color}{flower}{ANSI_RESET}" # Overlay with color
    return tokens

def render_frame(base, curr1, curr2, nxt1, nxt2, frame_idx, author, title):
    """Renders a single frame of the animation."""
    h, w = len(base), len(base[0])
    tokens = [['' for _ in range(w)] for _ in range(h)]

    # --- Determine content for each cell based on frame_idx and probabilities ---
    # Glitch probability decreases over time (fading effect)
    current_glitch_prob = GLITCH_PROB_MAX * (1.0 - (frame_idx / FRAMES))

    # Fragments appear based on reveal progress
    reveal_chars = int(w * ((frame_idx + 1) / FRAMES))

    # Determine rows for centered lines (avoiding top/bottom where author/title go)
    # Place lines around the vertical center, shifted slightly up
    mid_row = h // 2
    line1_row = max(1, mid_row - 1) # Ensure not row 0 (author)
    line2_row = min(h - 2, mid_row)     # Ensure not row h-1 (title)
    # If height is small (like 4), this puts lines at 1 and 2, auth at 0, title at 3 (no overlap)
    # If height is 5, lines at 1 and 2, auth at 0, title at 4.
    # If height is > 5, lines are at mid-1 and mid.

    # --- Populate the base layer (base, glitch, fragments) ---
    # This layer fills all cells *unless* they will be explicitly overwritten by centered text
    curr1_txt_clipped = curr1[:w] # Clip text to canvas width
    curr2_txt_clipped = curr2[:w]
    nxt1_txt_clipped = nxt1[:w]
    nxt2_txt_clipped = nxt2[:w]


    for y in range(h):
        for x in range(w):
            # Check if this row is one of the centered text rows
            is_centered_line_row = (y == line1_row or y == line2_row)

            char_to_add = ""
            if not is_centered_line_row:
                # In non-centered rows, show fragments, glitch, or base
                if x < reveal_chars and (len(nxt1_txt_clipped) > 0 or len(nxt2_txt_clipped) > 0) and random.random() < FRAG_PROB:
                    # Add next fragment (choose randomly between line1 and line2 fragments if both exist)
                    if len(nxt1_txt_clipped) > 0 and (len(nxt2_txt_clipped) == 0 or random.random() < 0.5):
                         # Use modulo for index in case fragment line is shorter than reveal_chars
                         char_to_add = f"{ANSI_YELLOW}{nxt1_txt_clipped[x % len(nxt1_txt_clipped)]}{ANSI_RESET}"
                    elif len(nxt2_txt_clipped) > 0:
                         char_to_add = f"{ANSI_YELLOW}{nxt2_txt_clipped[x % len(nxt2_txt_clipped)]}{ANSI_RESET}"
                    else: # Fallback if somehow fragment logic fails
                         char_to_add = base[y][x]

                elif random.random() < current_glitch_prob:
                    # Add glitch
                    char_to_add = random.choice(UNICODE_POOL)
                else:
                    # Add base character
                    char_to_add = base[y][x]
            else:
                 # In centered rows initially use base (will be overlaid later)
                 char_to_add = base[y][x] # Placeholder

            tokens[y][x] = char_to_add # Place the determined character

    # --- Overlay Centered Lines (on top of base/glitch/fragments) ---
    # Calculate centering positions for the current lines
    start1 = max(0, (w - len(curr1_txt_clipped)) // 2)
    end1   = start1 + len(curr1_txt_clipped)
    start2 = max(0, (w - len(curr2_txt_clipped)) // 2)
    end2   = start2 + len(curr2_txt_clipped)

    # Place curr1
    if line1_row >= 0 and line1_row < h:
        for x in range(start1, end1):
             # Ensure x is within bounds of tokens row
             if x < w:
                 tokens[line1_row][x] = f"{ANSI_YELLOW}{curr1_txt_clipped[x-start1]}{ANSI_RESET}"

    # Place curr2
    if line2_row >= 0 and line2_row < h:
        for x in range(start2, end2):
             # Ensure x is within bounds of tokens row
             if x < w:
                 tokens[line2_row][x] = f"{ANSI_YELLOW}{curr2_txt_clipped[x-start2]}{ANSI_RESET}"

    # --- Overlay Author/Title (on top of everything so far) ---
    auth_row = 0
    title_row = h - 1

    # Place author (top-left)
    if auth_row >= 0 and auth_row < h:
        auth_txt_clipped = author[:w] # Clip author to width
        for i, c in enumerate(auth_txt_clipped):
             # Ensure i is within bounds of tokens row
             if i < w:
                 tokens[auth_row][i] = f"{ANSI_MAGENTA}{c}{ANSI_RESET}"

    # Place title (bottom-right)
    if title_row >= 0 and title_row < h:
        tit_txt_clipped = title[:w] # Clip title to width
        start_t = max(0, w - len(tit_txt_clipped)) # Align to the right
        for i, c in enumerate(tit_txt_clipped):
             # Ensure start_t + i is within bounds of tokens row
             if start_t + i < w:
                tokens[title_row][start_t + i] = f"{ANSI_MAGENTA}{c}{ANSI_RESET}"

    # --- Overlay Flowers (on top of everything else) ---
    tokens = overlay_flowers(tokens, frame_idx)

    # --- Join tokens into strings for printing ---
    return [''.join(row) for row in tokens]

def animate(poems):
    """Runs the main animation loop."""
    pi = random.randrange(len(poems))
    # Ensure initial li1 allows for a second line in the poem
    li1 = random.randrange(len(poems[pi]['lines']))

    while True:
        # Get the current pair of lines
        curr1 = poems[pi]['lines'][li1]
        li2 = (li1 + 1) % len(poems[pi]['lines'])
        curr2 = poems[pi]['lines'][li2]
        auth = poems[pi]['author']
        title= poems[pi]['title']

        # Determine the *next* pair of lines (for fragments)
        npi, nli1 = pick_next(poems, pi, li1)
        nli2 = (nli1 + 1) % len(poems[npi]['lines'])
        nxt1 = poems[npi]['lines'][nli1]
        nxt2 = poems[npi]['lines'][nli2]

        # Generate a new random base canvas for this cycle
        base = random_canvas(WIDTH, HEIGHT)

        for f in range(FRAMES):
            frame = render_frame(base, curr1, curr2, nxt1, nxt2, f, auth, title)
            clear()
            print('\n'.join(frame))
            time.sleep(DELAY)

        # Update to the next poem and starting line for the next cycle
        pi, li1 = npi, nli1

def main():
    """Main function to load poems and start animation."""
    poems = load_poems()
    try:
        animate(poems)
    except KeyboardInterrupt:
        # Clear the screen and print the end notice on interrupt
        clear()
        print(ANSI_MAGENTA + END_NOTICE + ANSI_RESET)
        sys.exit(0)

if __name__ == "__main__":
    main()