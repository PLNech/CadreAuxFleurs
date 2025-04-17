
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glitch_unicode_flowers_v10.py

- Citation principale centrée en jaune.
- Fragments de la prochaine citation dispersés hors centre.
- Glitch autour.
- Superposition d’ASCII fleurs MONOSPACE uniquement.
- Effet vague : densité de fleurs croissante.
- Explosion florale soudaine en fin de cycle.
- Chaque citation dure 96 s (30 frames × 3.2 s).
- 95% de chances de rester dans le même poème.
- Auteur et titre affichés FIXES (pas de clignotement) : auteur en haut gauche, titre en bas droite.
- Pool unicode redivisé : UNICODE_POOL pour bruit, FLOWERS pour fleurs exotiques
"""
import json, random, sys, time

# ── CONFIG ────────────────────────────────────────────────────────────────
POEM_FILE       = "poemes.json"
WIDTH, HEIGHT   = 50, 15             # dimensions du canvas
total_duration  = 6.0               # durée de chaque citation (sec)
FRAMES          = 30
DELAY           = total_duration / FRAMES  # 3.2s par frame
GLITCH_PROB     = 0.18               # probabilité de glitch
FRAG_PROB       = 0.05               # probabilité de fragments de next ligne
MAX_FLOWER_PROB = 0.15               # densité max de fleurs à la fin
STAY_PROB       = 0.95               # 95% reste dans même poème
EXPLOSION_FRAME = FRAMES - 3         # Frame où commence l'explosion florale

UNICODE_POOL    = [                  # pool de bruit visuel (anciens symboles)
    '◻', '◼', '◇', '◆', '○', '●', '□', '■',
    '▢', '▣', '▤', '▥', '▦', '▧', '▨', '▩',
    '▪', '▫', '⬛', '⬜', '◉', '◌', '◍', '◊'
]

# Pool de fleurs graphiques variées (exotiques)
FLOWERS = [
    '⁕', '⚘', '𓁗', '𓁘', '𓆷', '𓆸', '𓆻',
    '𓇖', '𓇗', '𓇘', '𓇙', '𓇬', '𓋇', '𓋈',
    '🌻', '🎕', '🎴', '💮', '🥀'
]

# ANSI escapes
ANSI_CLEAR      = "\033[H\033[J"
ANSI_YELLOW     = "\033[93m"
ANSI_MAGENTA    = "\033[95m"
ANSI_RESET      = "\033[0m"

# ASCII art pour fin
END_NOTICE = r"""
Bonne Fête des Fleurs!
      _,-._
     / \_/ \
    >-(_)-<
     \_/ \_/
       `-'
"""

# ── HELPERS ───────────────────────────────────────────────────────────────

def clear():
    sys.stdout.write(ANSI_CLEAR)
    sys.stdout.flush()

def load_poems():
    with open(POEM_FILE, encoding="utf-8") as f:
        data = json.load(f)
    poems = []
    for poem in data.get("poems", []):
        lines = [l.strip() for l in poem.get("text", "\n").splitlines() if l.strip()]
        if not lines:
            continue
        poems.append({
            'author': poem.get('author',''),
            'title' : poem.get('title',''),
            'lines' : lines
        })
    return poems

def pick_next(poems, pi, li):
    if random.random() < STAY_PROB:
        return pi, (li + 1) % len(poems[pi]['lines'])
    new_pi = random.randrange(len(poems))
    return new_pi, random.randrange(len(poems[new_pi]['lines']))

def random_canvas(w, h):
    return [''.join(random.choice(UNICODE_POOL) for _ in range(w)) for _ in range(h)]

def overlay_flowers(tokens, frame_idx):
    h, w = len(tokens), len(tokens[0])
    frac = (frame_idx + 1) / FRAMES
    density = MAX_FLOWER_PROB * (frac ** 2)

    if frame_idx >= EXPLOSION_FRAME:
        density = 0.4 + (frame_idx - EXPLOSION_FRAME) / 3 * 0.4  # 0.4 → 0.8 progressive

    for y in range(h):
        for x in range(w):
            if random.random() < density:
                flower = random.choice(FLOWERS)
                tokens[y][x] = f"{ANSI_MAGENTA}{flower}{ANSI_RESET}"
    return tokens

def render_frame(base, curr, nxt, frame_idx, author, title):
    h, w = len(base), len(base[0])
    mid = h // 2
    curr_txt = curr[:w]
    nxt_txt  = nxt[:w]
    start = max(0, (w - len(curr_txt)) // 2)
    end   = start + len(curr_txt)
    reveal = int(len(nxt_txt) * ((frame_idx + 1) / FRAMES))

    # construire tokens
    tokens = []
    for y, row in enumerate(base):
        row_t = []
        for x, ch in enumerate(row):
            if y == mid and start <= x < end:
                row_t.append(f"{ANSI_YELLOW}{curr_txt[x-start]}{ANSI_RESET}")
            elif y != mid and x < reveal and random.random() < FRAG_PROB:
                row_t.append(f"{ANSI_YELLOW}{nxt_txt[x]}{ANSI_RESET}")
            elif random.random() < GLITCH_PROB:
                row_t.append(random.choice(UNICODE_POOL))
            else:
                row_t.append(ch)
        tokens.append(row_t)

    # superposer fleurs
    tokens = overlay_flowers(tokens, frame_idx)

    # auteur (top-left) et titre (bottom-right)
    auth = author[:w]
    for i, c in enumerate(auth): tokens[0][i] = f"{ANSI_MAGENTA}{c}{ANSI_RESET}"
    tit = title[:w]
    start_t = max(0, w - len(tit))
    for i, c in enumerate(tit): tokens[h-1][start_t + i] = f"{ANSI_MAGENTA}{c}{ANSI_RESET}"

    return [''.join(row) for row in tokens]

def animate(poems):
    pi = random.randrange(len(poems))
    li = random.randrange(len(poems[pi]['lines']))
    while True:
        curr = poems[pi]['lines'][li]
        auth = poems[pi]['author']
        title= poems[pi]['title']
        npi, nli = pick_next(poems, pi, li)
        nxt  = poems[npi]['lines'][nli]
        base = random_canvas(WIDTH, HEIGHT)
        for f in range(FRAMES):
            frame = render_frame(base, curr, nxt, f, auth, title)
            clear()
            print('\n'.join(frame))
            time.sleep(DELAY)
        pi, li = npi, nli

def main():
    poems = load_poems()
    try:
        animate(poems)
    except KeyboardInterrupt:
        clear()
        print(ANSI_MAGENTA + END_NOTICE + ANSI_RESET)

if __name__ == "__main__":
    main()

