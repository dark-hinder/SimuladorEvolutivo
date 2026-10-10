# -*- coding: utf-8 -*-
"""
PSE - Projeto Simulador Evolutivo
Mundo: laboratório explorável (visão de cima, estilo Pokémon FireRed),
estações de trabalho, diálogos, HUD e o evento da criatura.
"""
import math
import random

import pygame

from pse_core import *
from pse_scenes import DNAScene, BankScene, ExpScene, SimScene, PCScene

# limites do chão (posição dos pés do personagem)
X_MIN, X_MAX, Y_MIN, Y_MAX = 48, 1005, 178, 624

# (id, nome, retângulo no cenário 1053x674)
STATIONS = [
    dict(id="dna", name="Sala de análise genética", r=pygame.Rect(88, 302, 242, 148)),
    dict(id="bank", name="Banco de dados biológicos", r=pygame.Rect(668, 483, 242, 110)),
    dict(id="exp", name="Laboratório de experimentação", r=pygame.Rect(84, 483, 232, 110)),
    dict(id="scope", name="Cultivo e observação de organismos", r=pygame.Rect(220, 125, 232, 122)),
    dict(id="pc", name="Computador principal", r=pygame.Rect(668, 275, 242, 140)),
    dict(id="fridge", name="Armazenamento de amostras", r=pygame.Rect(872, 90, 108, 135)),
    dict(id="equip", name="Sala de equipamentos", r=pygame.Rect(42, 82, 95, 148)),
    dict(id="door", name="Saída", r=pygame.Rect(478, 628, 100, 46)),
]
SOLIDS = [s["r"] for s in STATIONS if s["id"] != "door"] + [pygame.Rect(148, 135, 56, 92)]

TUTORIAL = [
    ("Roberto (interfone)", "Bem-vindo ao laboratório, primo! Regra número um: não exploda nada. "
                            "Regra número dois: releia a regra número um."),
    ("Roberto (interfone)", "Use as setas ou WASD para andar e E ou ESPAÇO para interagir. A barra de "
                            "Integridade mostra a saúde do laboratório. Se zerar... bem, não zere."),
    ("Roberto (interfone)", "Comece pelo quadro de DNA, à esquerda. Eu o chamo de 'a parede que sabe tudo'."),
]

PROGRESS_LINES = {
    "dna": [("William", "Sequências analisadas, mutações caçadas. Eu faria isso dormindo... e quase fiz."),
            ("Roberto (interfone)", "Ótimo, primo! Agora vá ao banco de dados (bancada das pastas) e "
                                    "aprenda a ler o código genético.")],
    "bank": [("Roberto (interfone)", "Você traduz códons melhor que muito doutorando. Estudo concluído!")],
    "exp": [("Roberto (interfone)", "Controle de variáveis impecável. A ciência agradece. Agora observe uma "
                                    "população evoluir, no microscópio da bancada de cima.")],
    "sim": [("William", "Evolução ao vivo, sem esperar milhões de anos. Que conveniente."),
            ("William", "...Por que o setor de cultivo está fazendo esse barulho de gelatina?")],
    "creature": [("William", "Pronto... destruída. Pelo menos o gráfico dela ficou ótimo."),
                 ("Roberto (interfone)", "Excelente trabalho! Agora você está pronto para o projeto final: "
                                         "o Computador Evolutivo. Vá ao computador principal.")],
}
STAGE_LINES = {
    2: [("Sistema", "Fase PESQUISA: bancada de experimentação e área de cultivo desbloqueadas!")],
    3: [("Sistema", "Fase PROJETO: o Computador Evolutivo foi liberado no computador principal!")],
}
CREATURE_LINES = [
    ("Sistema", "ALERTA BIOLÓGICO! Anomalia genética detectada no setor de cultivo."),
    ("William", "Isso não estava nos meus resultados. Por que tem uma coisa verde me encarando?"),
    ("Roberto (interfone)", "Primo, não deixe ela encostar em você! Use o pulso de contenção "
                            "(ESPAÇO ou E) quando estiver perto!"),
]
EQUIP_LINES = [
    "Prateleiras de reagentes, pipetas e um frasco rotulado 'NÃO ABRIR (sério)'. William decide não abrir.",
    "Uma estante de equipamentos. Falta uma etiqueta de 'quem pegou o multímetro?'.",
    "Caixas de luvas, óculos de proteção e um jaleco com o nome 'Roberto C.' bordado. O bordado está torto.",
]


class Actor(object):
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)


class Creature(object):
    """Criatura gerada por uma análise genética que saiu do controle."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.hp = self.max_hp = 6
        self.t = 0.0
        self.flash = 0.0
        self.kx = 0.0
        self.ky = 0.0

    def body(self):
        return pygame.Rect(int(self.x) - 24, int(self.y) - 38, 48, 38)

    def knock(self, nx, ny, power=260.0):
        self.kx += nx * power
        self.ky += ny * power

    def update(self, dt, player, world):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        dx, dy = player.x - self.x, player.y - self.y
        d = math.hypot(dx, dy) or 1.0
        speed = 70 + (self.max_hp - self.hp) * 10
        vx = dx / d * speed + math.sin(self.t * 3.1) * 26 + self.kx
        vy = dy / d * speed + math.cos(self.t * 2.4) * 26 + self.ky
        decay = 0.02 ** dt
        self.kx *= decay
        self.ky *= decay
        world.move_entity(self, vx * dt, vy * dt, 20, 14)

    def draw(self, surf, player):
        x, y = int(self.x), int(self.y)
        pulse = math.sin(self.t * 6) * 3
        pygame.draw.ellipse(surf, (130, 130, 160), (x - 28, y - 9, 56, 16))
        rect = pygame.Rect(0, 0, int(50 + pulse), int(38 - pulse))
        rect.midbottom = (x, y)
        body = (112, 214, 124) if self.flash <= 0 else (255, 255, 255)
        pygame.draw.ellipse(surf, (28, 58, 40), rect.inflate(6, 6))
        pygame.draw.ellipse(surf, body, rect)
        for k in range(3):
            pygame.draw.circle(surf, (150, 92, 200), (rect.x + 12 + k * 13, rect.y + 10 + (k % 2) * 9), 4)
        dx, dy = player.x - self.x, (player.y - 30) - (self.y - 20)
        d = math.hypot(dx, dy) or 1.0
        for sx in (-9, 9):
            ex, ey = rect.centerx + sx, rect.y + 16
            pygame.draw.circle(surf, WHITE, (ex, ey), 6)
            pygame.draw.circle(surf, BLACK, (int(ex + dx / d * 2.5), int(ey + dy / d * 2.5)), 3)
        pygame.draw.line(surf, (28, 58, 40), (rect.centerx - 7, rect.y + 28),
                         (rect.centerx + 7, rect.y + 28), 3)
        if self.hp < self.max_hp:
            draw_bar(surf, (x - 28, rect.y - 16, 56, 8), self.hp, self.max_hp, RED)


class World(Scene):
    SPEED = 190.0

    def __init__(self, game):
        self.g = game
        self.p = Actor(528, 560)
        self.face = 1
        self.walk_t = 0.0
        self.moving = False
        self.dialog = None
        self.creature = None
        self.inv = 0.0
        self.atk_cd = 0.0
        self.attack_t = 0.0
        self.shake = 0.0
        self.t = 0.0
        self.near = None
        st = game.state
        self.seen_done = set(st.done)
        self.last_stage = st.stage
        self.shadow = pygame.Surface((46, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (30, 30, 60, 90), (0, 0, 46, 16))
        game.audio.music(st.stage)
        if not st.intro_done:
            st.intro_done = True
            self.say(TUTORIAL)

    # ---------------------------------------------------------- utilidades
    def say(self, lines, on_done=None):
        self.dialog = Dialog(self.g, lines, on_done)

    def locked(self, sid):
        return sid in ("exp", "scope") and self.g.state.stage < 2

    def blocked(self, x, y, hw, fh):
        if x < X_MIN or x > X_MAX or y < Y_MIN or y > Y_MAX:
            return True
        rect = pygame.Rect(int(x) - hw, int(y) - fh, hw * 2, fh)
        for s in SOLIDS:
            if rect.colliderect(s):
                return True
        return False

    def move_entity(self, ent, dx, dy, hw=13, fh=12):
        nx = ent.x + dx
        if not self.blocked(nx, ent.y, hw, fh):
            ent.x = nx
        ny = ent.y + dy
        if not self.blocked(ent.x, ny, hw, fh):
            ent.y = ny

    def player_body(self):
        return pygame.Rect(int(self.p.x) - 16, int(self.p.y) - 60, 32, 56)

    # ------------------------------------------------------------ entrada
    def handle(self, e):
        if self.dialog:
            self.dialog.handle(e)
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_e, pygame.K_SPACE,
                                                   pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.creature:
                self.attack()
            elif self.near:
                self.interact(self.near)

    def interact(self, s):
        sid = s["id"]
        st = self.g.state
        self.g.audio.play("confirm")
        if self.locked(sid):
            self.say([("Roberto (interfone)", "Essa área ainda está lacrada, primo. Termine o Estudo: "
                                              "análise de DNA e tradução de códons.")])
        elif sid == "dna":
            self.g.push(DNAScene(self.g))
        elif sid == "bank":
            self.g.push(BankScene(self.g))
        elif sid == "exp":
            self.g.push(ExpScene(self.g))
        elif sid == "scope":
            self.g.push(SimScene(self.g))
        elif sid == "pc":
            self.g.push(PCScene(self.g))
        elif sid == "fridge":
            self.fridge()
        elif sid == "equip":
            self.say([("William", random.choice(EQUIP_LINES))])
        elif sid == "door":
            self.say([("William", "Não posso ir embora agora."),
                      ("Roberto (interfone)", "Ei, onde pensa que vai? O laboratório não se pesquisa sozinho!")])

    def fridge(self):
        st = self.g.state
        if st.budget >= 90:
            self.say([("William", "A geladeira está cheia de amostras rotuladas... e um sanduíche sem rótulo. "
                                  "Melhor não mexer em nada.")])
        elif st.fridge_uses >= 4:
            self.say([("Roberto (interfone)", "A verba acabou, primo. De agora em diante, cada tubo conta!")])
        else:
            st.fridge_uses += 1
            before = st.budget
            st.budget = min(100, st.budget + 25)
            self.g.audio.play("ok")
            self.say([("Roberto (interfone)", "Reposição aprovada! (Resmungando) Isso sai do meu café, viu?"),
                      ("Sistema", "Recursos: %d -> %d" % (before, st.budget))])

    # ------------------------------------------------------------- criatura
    def spawn_creature(self):
        st = self.g.state
        st.creature_spawned = True
        self.creature = Creature(800, 450)
        self.g.audio.play("alert")
        self.say(CREATURE_LINES)

    def attack(self):
        if self.atk_cd > 0:
            return
        self.atk_cd = 0.45
        self.attack_t = 0.25
        self.g.audio.play("zap")
        c = self.creature
        d = math.hypot(c.x - self.p.x, (c.y - 18) - (self.p.y - 30))
        if d <= 90:
            c.hp -= 1
            c.flash = 0.2
            nx, ny = (c.x - self.p.x) / (d or 1.0), (c.y - self.p.y) / (d or 1.0)
            c.knock(nx, ny)
            self.g.audio.play("hit")
            if c.hp <= 0:
                self.kill_creature()

    def kill_creature(self):
        st = self.g.state
        self.creature = None
        st.done.add("creature")
        self.g.gain_xp(40)
        st.log_event("criatura", "hp=6", "contida", True)
        self.g.audio.play("unlock")

    # ----------------------------------------------------------- progresso
    def check_progress(self):
        st = self.g.state
        new = st.done - self.seen_done
        if not new:
            return
        self.seen_done = set(st.done)
        lines = []
        for key in ("dna", "bank", "exp", "sim", "creature"):
            if key in new:
                lines.extend(PROGRESS_LINES[key])
        if st.stage != self.last_stage:
            self.last_stage = st.stage
            lines.extend(STAGE_LINES.get(st.stage, []))
            self.g.audio.play("unlock")
            self.g.audio.music(st.stage)
        if lines:
            self.say(lines)

    # -------------------------------------------------------------- update
    def update(self, dt):
        self.t += dt
        self.inv = max(0.0, self.inv - dt)
        self.atk_cd = max(0.0, self.atk_cd - dt)
        self.attack_t = max(0.0, self.attack_t - dt)
        self.shake = max(0.0, self.shake - dt)
        if self.dialog:
            self.dialog.update(dt)
            if self.dialog.finished:
                self.dialog = None
            return
        if self.g.pending:
            self.say(self.g.pending.pop(0))
            return
        self.check_progress()
        if self.dialog:
            return
        st = self.g.state
        if (st.stage == 2 and "exp" in st.done and "sim" in st.done
                and not st.creature_spawned and not self.creature):
            self.spawn_creature()
            return
        # movimento
        keys = pygame.key.get_pressed()
        dx = int(bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])) - int(bool(keys[pygame.K_LEFT] or keys[pygame.K_a]))
        dy = int(bool(keys[pygame.K_DOWN] or keys[pygame.K_s])) - int(bool(keys[pygame.K_UP] or keys[pygame.K_w]))
        self.moving = bool(dx or dy)
        if self.moving:
            if dx and dy:
                dx *= 0.7071
                dy *= 0.7071
            if dx:
                self.face = 1 if dx > 0 else -1
            self.walk_t += dt
            self.move_entity(self.p, dx * self.SPEED * dt, dy * self.SPEED * dt)
        # estação mais próxima
        feet = pygame.Rect(int(self.p.x) - 35, int(self.p.y) - 34, 70, 56)
        self.near = None
        best = 1e9
        for s in STATIONS:
            if feet.colliderect(s["r"]):
                d = math.hypot(self.p.x - s["r"].centerx, self.p.y - s["r"].centery)
                if d < best:
                    best = d
                    self.near = s
        # criatura
        if self.creature:
            self.creature.update(dt, self.p, self)
            if self.inv <= 0 and self.creature.body().colliderect(self.player_body()):
                self.inv = 1.2
                self.shake = 0.25
                c = self.creature
                d = math.hypot(self.p.x - c.x, self.p.y - c.y) or 1.0
                self.g.audio.play("hit")
                self.move_entity(self.p, (self.p.x - c.x) / d * 50, (self.p.y - c.y) / d * 50)
                self.g.hurt(8)

    # --------------------------------------------------------------- desenho
    def draw(self, surf):
        f = self.g.fonts
        ox = oy = 0
        if self.shake > 0:
            ox, oy = random.randint(-3, 3), random.randint(-3, 3)
        surf.fill((20, 22, 34))
        surf.blit(self.g.assets["lab"], (ox, oy))
        for s in STATIONS:
            if self.locked(s["id"]):
                shade = pygame.Surface(s["r"].size, pygame.SRCALPHA)
                shade.fill((10, 10, 30, 120))
                surf.blit(shade, s["r"].move(ox, oy))
                draw_lock(surf, (s["r"].centerx + ox, s["r"].centery + oy))
        # personagem e criatura (ordenados por profundidade)
        drawables = [(self.p.y, "p")]
        if self.creature:
            drawables.append((self.creature.y, "c"))
        for _y, kind in sorted(drawables):
            if kind == "p":
                self.draw_player(surf, ox, oy)
            else:
                self.creature.draw(surf, self.p)
        if self.attack_t > 0:
            r = int(95 * (1 - self.attack_t / 0.25))
            pygame.draw.circle(surf, (130, 225, 255), (int(self.p.x), int(self.p.y - 30)), max(4, r), 3)
        if self.near and not self.dialog and not self.creature:
            self.draw_prompt(surf)
        self.draw_hud(surf)
        draw_text(surf, "Setas/WASD: mover   E: interagir   M: som   F11: tela cheia", f["xs"], WHITE,
                  (40, H - 12), "bottomleft", shadow=BLACK)
        if self.dialog:
            self.dialog.draw(surf)

    def draw_player(self, surf, ox, oy):
        if self.inv > 0 and int(self.t * 20) % 2 == 0:
            return
        x, y = int(self.p.x) + ox, int(self.p.y) + oy
        surf.blit(self.shadow, (x - 23, y - 9))
        img = self.g.assets["william"] if self.face > 0 else self.g.assets["william_l"]
        bob = int(abs(math.sin(self.walk_t * 10)) * 3) if self.moving else 0
        surf.blit(img, img.get_rect(midbottom=(x, y + 4 - bob)))

    def draw_prompt(self, surf):
        f = self.g.fonts
        s = self.near
        txt = "[E] " + s["name"] + ("  (bloqueado)" if self.locked(s["id"]) else "")
        w = f["s"].size(txt)[0] + 28
        r = pygame.Rect(0, 0, w, 34)
        r.midbottom = (int(clamp(self.p.x, w // 2 + 8, W - w // 2 - 8)), int(self.p.y) - 92)
        r.top = max(r.top, 60)
        inner = draw_panel(surf, r, radius=8, width=3)
        draw_text(surf, txt, f["s"], INK, inner.center, "center")

    def draw_hud(self, surf):
        f = self.g.fonts
        st = self.g.state
        inner = draw_panel(surf, (8, 6, 318, 78), radius=8, width=3)
        draw_text(surf, "Integridade", f["xs"], INK, (inner.x + 8, inner.y + 5))
        col = GREEN if st.integrity > 50 else (YELLOW if st.integrity > 25 else RED)
        draw_bar(surf, (inner.x + 112, inner.y + 6, 180, 12), st.integrity, 100, col, back=(200, 204, 214))
        draw_text(surf, "Recursos", f["xs"], INK, (inner.x + 8, inner.y + 26))
        draw_bar(surf, (inner.x + 112, inner.y + 27, 180, 12), st.budget, 100, BLUE, back=(200, 204, 214))
        draw_text(surf, "Nv %d  XP %d/%d" % (st.level, st.xp % 50, 50), f["xs"], INK,
                  (inner.x + 8, inner.y + 48))
        stage_name = {1: "Estudo", 2: "Pesquisa", 3: "Projeto"}[st.stage]
        draw_text(surf, "Fase: " + stage_name, f["xs"], RED, (inner.right - 8, inner.y + 48), "topright")
        obj = pygame.Rect(W - 478, 6, 470, 58)
        oin = draw_panel(surf, obj, radius=8, width=3, accent=BLUE)
        draw_text(surf, "OBJETIVO", f["xs"], RED, (oin.x + 8, oin.y + 3))
        draw_wrapped(surf, st.objective(bool(self.creature)), f["xs"], INK,
                     pygame.Rect(oin.x + 8, oin.y + 20, oin.w - 16, 30), 2)
