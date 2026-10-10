# -*- coding: utf-8 -*-
"""
PSE - Projeto Simulador Evolutivo
Núcleo: constantes, helpers de interface, áudio procedural, estado do jogo
e caixa de diálogo estilo Pokémon FireRed.
"""
import csv
import math
import os
import random
import time
from array import array

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
DATA_CSV = os.path.join(BASE_DIR, "pse_dados.csv")

W, H = 1053, 674
FPS = 60

# --------------------------------------------------------------------- cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (40, 44, 60)
PANEL = (248, 248, 248)
BORDER = (48, 56, 80)
RED = (216, 80, 64)
BLUE = (72, 120, 200)
GREEN = (72, 176, 96)
YELLOW = (240, 200, 64)
ORANGE = (240, 140, 50)
GRAY = (120, 124, 136)
DARK = (20, 26, 40)
BASE_COL = {"A": (232, 96, 96), "T": (242, 202, 72), "C": (84, 152, 232),
            "G": (92, 192, 112), "U": (242, 162, 72)}

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e)
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ---------------------------------------------------------------------- fontes
def make_fonts():
    names = "dejavusansmono,couriernew,consolas,lucidaconsole,menlo,monospace"
    def f(size, bold=False):
        try:
            return pygame.font.SysFont(names, size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size + 6)
    return {"xs": f(14), "s": f(17), "m": f(21), "l": f(27, True),
            "xl": f(38, True), "title": f(66, True)}


def draw_text(surf, text, font, color, pos, anchor="topleft", shadow=None):
    img = font.render(text, True, color)
    r = img.get_rect()
    setattr(r, anchor, pos)
    if shadow:
        surf.blit(font.render(text, True, shadow), r.move(2, 2))
    surf.blit(img, r)
    return r


def wrap_text(text, font, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if font.size(test)[0] <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def draw_wrapped(surf, text, font, color, rect, line_gap=4):
    """Desenha texto com quebra de linha dentro de rect. Retorna o y final."""
    y = rect.y
    for ln in wrap_text(text, font, rect.w):
        surf.blit(font.render(ln, True, color), (rect.x, y))
        y += font.get_height() + line_gap
    return y


def clip_text(text, font, max_w):
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "...")[0] > max_w:
        text = text[:-1]
    return text + "..."


def draw_panel(surf, rect, fill=PANEL, border=BORDER, accent=RED, radius=10, width=4):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, border, rect, border_radius=radius)
    inner = rect.inflate(-width * 2, -width * 2)
    pygame.draw.rect(surf, accent, inner, border_radius=max(2, radius - 2))
    inner2 = inner.inflate(-4, -4)
    pygame.draw.rect(surf, fill, inner2, border_radius=max(2, radius - 4))
    return inner2


def draw_bar(surf, rect, value, maxv, color, back=(60, 64, 80)):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=5)
    w = int(rect.w * clamp(value / float(maxv), 0, 1))
    if w > 0:
        pygame.draw.rect(surf, color, (rect.x, rect.y, w, rect.h), border_radius=5)
    pygame.draw.rect(surf, WHITE, rect, 2, border_radius=5)


def draw_base(surf, font, letter, center, size=44, state=None):
    """Desenha um 'tijolinho' de base nitrogenada. Retorna o rect."""
    r = pygame.Rect(0, 0, size, size)
    r.center = center
    col = BASE_COL.get(letter, GRAY)
    pygame.draw.rect(surf, (16, 18, 28), r.move(0, 3), border_radius=8)
    pygame.draw.rect(surf, col, r, border_radius=8)
    if state == "hover":
        pygame.draw.rect(surf, WHITE, r.inflate(4, 4), 3, border_radius=9)
    elif state == "good":
        pygame.draw.rect(surf, GREEN, r.inflate(6, 6), 4, border_radius=10)
    elif state == "bad":
        pygame.draw.rect(surf, RED, r.inflate(6, 6), 4, border_radius=10)
    img = font.render(letter, True, (20, 20, 30))
    surf.blit(img, img.get_rect(center=r.center))
    return r


def draw_empty_slot(surf, center, size=44):
    r = pygame.Rect(0, 0, size, size)
    r.center = center
    pygame.draw.rect(surf, (70, 78, 104), r, 2, border_radius=8)
    return r


def row_centers(n, size=44, gap=6, y=300):
    total = n * size + (n - 1) * gap
    x0 = (W - total) // 2 + size // 2
    return [(x0 + i * (size + gap), y) for i in range(n)]


def draw_chart(surf, rect, series, xmax, ymax, font, xlabel=None, ylabel=None):
    """series: lista de dict(points=[...], color=(r,g,b), label='...')."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, DARK, rect, border_radius=6)
    pygame.draw.rect(surf, (90, 100, 130), rect, 2, border_radius=6)
    plot = pygame.Rect(rect.x + 50, rect.y + 30, rect.w - 70, rect.h - 56)
    for k in range(5):
        y = plot.bottom - plot.h * k / 4.0
        pygame.draw.line(surf, (44, 52, 76), (plot.x, y), (plot.right, y), 1)
        lab = ("%g" % (ymax * k / 4.0))
        draw_text(surf, lab, font, (150, 160, 190), (plot.x - 6, y), "midright")
    pygame.draw.line(surf, (150, 160, 190), plot.bottomleft, plot.bottomright, 2)
    pygame.draw.line(surf, (150, 160, 190), plot.bottomleft, plot.topleft, 2)
    for s in series:
        pts = s["points"]
        if len(pts) < 2:
            continue
        step = max(1, len(pts) // 400)
        coords = []
        for i in range(0, len(pts), step):
            x = plot.x + plot.w * i / float(max(1, xmax))
            y = plot.bottom - plot.h * clamp(pts[i] / float(ymax), 0, 1)
            coords.append((x, y))
        if len(coords) >= 2:
            pygame.draw.lines(surf, s["color"], False, coords, 3)
    lx = rect.x + 54
    for s in series:
        pygame.draw.rect(surf, s["color"], (lx, rect.y + 9, 14, 10), border_radius=3)
        r = draw_text(surf, s["label"], font, (210, 216, 232), (lx + 20, rect.y + 6))
        lx = r.right + 18
    if xlabel:
        draw_text(surf, xlabel, font, (150, 160, 190), (plot.right, rect.bottom - 6), "bottomright")
    if ylabel:
        draw_text(surf, ylabel, font, (150, 160, 190), (rect.right - 8, rect.y + 6), "topright")


def draw_lock(surf, center):
    x, y = center
    pygame.draw.circle(surf, (60, 60, 70), (x, y - 8), 8, 3)
    body = pygame.Rect(0, 0, 22, 16)
    body.center = (x, y + 4)
    pygame.draw.rect(surf, (20, 20, 30), body.inflate(4, 4), border_radius=4)
    pygame.draw.rect(surf, YELLOW, body, border_radius=3)
    pygame.draw.circle(surf, (20, 20, 30), (x, y + 4), 2)


def draw_check(surf, rect, checked):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, WHITE, r, border_radius=4)
    pygame.draw.rect(surf, BORDER, r, 3, border_radius=4)
    if checked:
        a = (r.x + 4, r.centery)
        b = (r.x + r.w * 0.42, r.bottom - 5)
        c = (r.right - 4, r.y + 5)
        pygame.draw.lines(surf, GREEN, False, [a, b, c], 4)


def draw_arrows(surf, rect, color=INK):
    """Setinhas < > nas laterais de rect (para seletores)."""
    r = pygame.Rect(rect)
    cy = r.centery
    pygame.draw.polygon(surf, color, [(r.x + 4, cy), (r.x + 14, cy - 7), (r.x + 14, cy + 7)])
    pygame.draw.polygon(surf, color, [(r.right - 4, cy), (r.right - 14, cy - 7), (r.right - 14, cy + 7)])


def gradient_bg(surf, top, bottom):
    for y in range(0, H, 4):
        c = lerp_color(top, bottom, y / float(H))
        pygame.draw.rect(surf, c, (0, y, W, 4))


# ------------------------------------------------------------------- áudio
SR = 22050


def _midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _osc(wave, ph):
    if wave == "square":
        return 1.0 if ph < 0.5 else -1.0
    if wave == "tri":
        return 4.0 * abs(ph - 0.5) - 1.0
    if wave == "saw":
        return 2.0 * ph - 1.0
    return math.sin(2 * math.pi * ph)


def synth(freq, dur, vol=0.25, wave="square", decay=True, sweep=0.0):
    n = max(1, int(SR * dur))
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        f = freq + sweep * (i / float(n))
        ph = (ph + f / SR) % 1.0
        if decay:
            env = (1.0 - i / float(n)) ** 1.5
        else:
            env = 1.0 if i < n - 150 else max(0.0, (n - i) / 150.0)
        if i < 60:
            env *= i / 60.0
        out[i] = _osc(wave, ph) * env * vol
    return out


def seq(notes):
    """notes: lista de (freq, dur, vol, wave)."""
    out = []
    for f, d, v, w in notes:
        out.extend(synth(f, d, v, w))
    return out


def noise(dur, vol=0.25):
    n = int(SR * dur)
    return [random.uniform(-1, 1) * (1 - i / float(n)) ** 2 * vol for i in range(n)]


def to_bytes(samples, channels=1):
    buf = array("h")
    for s in samples:
        v = int(clamp(s, -1.0, 1.0) * 32767)
        buf.append(v)
        if channels == 2:
            buf.append(v)
    return buf.tobytes()


def build_sfx():
    s = {}
    s["blip"] = synth(900, 0.02, 0.07, "square")
    s["select"] = synth(660, 0.05, 0.12, "square")
    s["confirm"] = seq([(523, 0.05, 0.14, "square"), (784, 0.08, 0.14, "square")])
    s["ok"] = seq([(523, 0.09, 0.2, "tri"), (659, 0.09, 0.2, "tri"),
                   (784, 0.09, 0.2, "tri"), (1047, 0.2, 0.2, "tri")])
    s["bad"] = seq([(220, 0.14, 0.18, "saw"), (165, 0.26, 0.18, "saw")])
    s["unlock"] = seq([(523, 0.07, 0.16, "square"), (659, 0.07, 0.16, "square"),
                       (784, 0.07, 0.16, "square"), (1047, 0.07, 0.16, "square"),
                       (1319, 0.16, 0.16, "square")])
    s["alert"] = seq([(880, 0.14, 0.16, "square"), (660, 0.14, 0.16, "square")] * 2)
    s["hit"] = noise(0.12, 0.3)
    s["zap"] = synth(900, 0.14, 0.14, "saw", sweep=-700)
    s["mutation"] = seq([(1200, 0.05, 0.14, "tri"), (1600, 0.05, 0.14, "tri"),
                         (1400, 0.05, 0.14, "tri"), (2000, 0.12, 0.14, "tri")])
    return s


def render_music(stage):
    """Pequeno loop chiptune de 16 colcheias que fica mais 'tecnológico'
    conforme o estágio da história avança."""
    bpm = 104
    step = 60.0 / bpm / 2.0
    n_step = int(SR * step)
    steps = 16
    total = n_step * steps
    mix = [0.0] * total
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    arp = [0, 1, 2, 1]
    lead = [None, 76, None, 72, None, 74, None, 71, None, 72, None, 76, None, 74, 72, None]
    cache = {}

    def tone(m, wave, dur, vol):
        k = (m, wave, round(dur, 3), vol)
        if k not in cache:
            cache[k] = synth(_midi(m), dur, vol, wave)
        return cache[k]

    def add(at, samples):
        base = at * n_step
        for i, v in enumerate(samples):
            j = base + i
            if j >= total:
                break
            mix[j] += v

    for s in range(steps):
        ch = chords[s // 4]
        add(s, tone(ch[arp[s % 4]] + 12, "tri", step * 0.95, 0.15))
        if stage >= 2 and s % 2 == 0:
            add(s, tone(ch[0] - 12, "square", step * 1.6, 0.06))
        if stage >= 2 and lead[s]:
            add(s, tone(lead[s], "square", step * 0.9, 0.05))
        if stage >= 3 and s % 2 == 1:
            add(s, tone(ch[2] + 24, "square", step * 0.5, 0.035))
    return mix


def render_hum():
    n = SR * 2
    out = []
    for i in range(n):
        t = i / float(SR)
        v = (0.5 * math.sin(2 * math.pi * 110 * t) + 0.25 * math.sin(2 * math.pi * 165 * t)
             + 0.15 * math.sin(2 * math.pi * 55 * t))
        trem = 0.75 + 0.25 * math.sin(2 * math.pi * 0.5 * t)
        out.append(v * trem * 0.12)
    return out


class Audio:
    def __init__(self):
        self.ok = False
        self.muted = False
        self.sfx = {}
        self.music_cache = {}
        self.cur_stage = 0
        self.ch = 1
        self.music_ch = None
        self.hum_ch = None
        try:
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init(SR, -16, 1, 512, allowedchanges=0)
                except TypeError:
                    pygame.mixer.init(SR, -16, 1, 512)
            info = pygame.mixer.get_init()
            self.ch = info[2] if info else 1
            pygame.mixer.set_reserved(2)
            self.music_ch = pygame.mixer.Channel(0)
            self.hum_ch = pygame.mixer.Channel(1)
            for name, samples in build_sfx().items():
                self.sfx[name] = self._snd(samples)
            self.hum = self._snd(render_hum())
            self.hum_ch.play(self.hum, loops=-1)
            self.hum_ch.set_volume(0.5)
            self.ok = True
        except Exception as exc:  # sem dispositivo de áudio, etc.
            print("[PSE] Áudio desativado:", exc)

    def _snd(self, samples):
        return pygame.mixer.Sound(buffer=to_bytes(samples, self.ch))

    def play(self, name):
        if self.ok and not self.muted and name in self.sfx:
            try:
                self.sfx[name].play()
            except Exception:
                pass

    def music(self, stage):
        if not self.ok or stage == self.cur_stage:
            return
        self.cur_stage = stage
        try:
            if stage not in self.music_cache:
                self.music_cache[stage] = self._snd(render_music(stage))
            self.music_ch.play(self.music_cache[stage], loops=-1)
            self.music_ch.set_volume(0.0 if self.muted else 0.45)
        except Exception as exc:
            print("[PSE] Música indisponível:", exc)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok:
            self.music_ch.set_volume(0.0 if self.muted else 0.45)
            self.hum_ch.set_volume(0.0 if self.muted else 0.5)
        return self.muted


# ------------------------------------------------------------ estado do jogo
class GameState:
    EXP_COST = 15

    def __init__(self):
        self.reset()

    def reset(self):
        self.integrity = 100
        self.budget = 100
        self.xp = 0
        self.done = set()        # dna, bank, exp, sim, creature, final
        self.exp_ok = set()      # ids de cenários concluídos
        self.fridge_uses = 0
        self.creature_spawned = False
        self.intro_done = False
        self.log = []
        self.stats = {"dna_ok": 0, "dna_total": 0, "bank_ok": 0, "bank_total": 0,
                      "mutations": 0, "exp_runs": 0, "sim_gens": 0}
        self.started = time.time()

    @property
    def level(self):
        return 1 + self.xp // 50

    @property
    def stage(self):
        if "creature" in self.done:
            return 3
        if "dna" in self.done and "bank" in self.done:
            return 2
        return 1

    def log_event(self, tipo, detalhe, resultado, acerto):
        """Registra a decisão do jogador (dados para futuros estudos/IA)."""
        row = {"tempo_s": int(time.time() - self.started), "tipo": tipo,
               "detalhe": detalhe, "resultado": resultado, "acerto": int(bool(acerto)),
               "nivel": self.level, "integridade": self.integrity, "recursos": self.budget}
        self.log.append(row)
        try:
            new = not os.path.exists(DATA_CSV)
            with open(DATA_CSV, "a", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(row.keys()))
                if new:
                    wr.writeheader()
                wr.writerow(row)
        except Exception:
            pass

    def objective(self, creature_alive=False):
        d = self.done
        if creature_alive:
            return "CONTENHA A CRIATURA! (ESPAÇO ataca de perto)"
        if self.stage == 1:
            if "dna" not in d:
                return "Analise o DNA no quadro (sala de análise genética)"
            return "Traduza códons no banco de dados (bancada das pastas)"
        if self.stage == 2:
            if "exp" not in d:
                return "Faça o experimento controlado (bancada dos tubos)"
            if "sim" not in d:
                return "Simule a evolução (microscópio, bancada de cima)"
            return "Algo se mexe no setor de cultivo..."
        if "final" not in d:
            return "Construa o Computador Evolutivo (computador principal)"
        return "Pesquisa concluída!"


# ----------------------------------------------------------------- cenas
class Scene:
    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def on_resume(self):
        pass


class Dialog:
    """Caixa de diálogo com efeito de máquina de escrever."""
    CPS = 55.0

    def __init__(self, game, lines, on_done=None):
        self.g = game
        self.lines = [l if isinstance(l, tuple) else (None, l) for l in lines]
        self.i = 0
        self.t = 0.0
        self.on_done = on_done
        self.finished = False

    @property
    def text(self):
        return self.lines[self.i][1]

    def full(self):
        return self.t >= len(self.text)

    def update(self, dt):
        if self.finished:
            return
        before = int(self.t)
        self.t += dt * self.CPS
        if (int(self.t) // 3) != (before // 3) and self.t < len(self.text):
            self.g.audio.play("blip")

    def handle(self, e):
        ok = False
        if e.type == pygame.KEYDOWN and e.key in CONFIRM_KEYS:
            ok = True
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            ok = True
        if ok:
            self.advance()

    def advance(self):
        if self.finished:
            return
        if not self.full():
            self.t = len(self.text) + 1
            return
        self.i += 1
        self.t = 0.0
        if self.i >= len(self.lines):
            self.finished = True
            if self.on_done:
                self.on_done()

    def draw(self, surf):
        if self.finished:
            return
        f = self.g.fonts
        speaker, text = self.lines[self.i]
        box = pygame.Rect(24, H - 178, W - 48, 154)
        inner = draw_panel(surf, box)
        if speaker:
            tw = f["s"].size(speaker)[0] + 28
            tag = pygame.Rect(box.x + 24, box.y - 20, tw, 32)
            tin = draw_panel(surf, tag, fill=(255, 238, 200), radius=8, width=3)
            draw_text(surf, speaker, f["s"], INK, tin.center, "center")
        remaining = int(self.t)
        y = inner.y + 14
        for ln in wrap_text(text, f["m"], inner.w - 44)[:4]:
            part = ln[:max(0, remaining)]
            remaining -= len(ln) + 1
            surf.blit(f["m"].render(part, True, INK), (inner.x + 20, y))
            y += f["m"].get_height() + 6
        if self.full() and int(time.time() * 2.5) % 2 == 0:
            cx, cy = inner.right - 26, inner.bottom - 20
            pygame.draw.polygon(surf, RED, [(cx - 8, cy - 6), (cx + 8, cy - 6), (cx, cy + 6)])
