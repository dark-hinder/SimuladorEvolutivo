#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSE - Projeto Simulador Evolutivo
Conceito e design: João Pedro Ferreira Rosa

Jogo 2D de simulação científica (estética inspirada em Pokémon FireRed).
Você é William Charles II, geneticista recém-contratado por um laboratório
na Noruega. Analise DNA, traduza códons, planeje experimentos controlados,
observe populações evoluírem e, no fim, construa o Computador Evolutivo.

Executar:  python pse.py
"""
import math
import os
import random
import sys

import pygame

from pse_core import *
from pse_world import World


def load_assets():
    a = {}

    def load(name):
        path = os.path.join(ASSET_DIR, name)
        return pygame.image.load(path).convert_alpha()

    a["lab"] = load("laboratorio.png")
    w = load("william.png")
    a["william"] = w
    a["william_l"] = pygame.transform.flip(w, True, False)
    pc = load("computador.png")
    a["computador"] = pygame.transform.scale(pc, (150, 145))
    a["icon_pc"] = pygame.transform.scale(pc, (60, 58))
    mesa = load("mesa.png")
    a["mesa"] = mesa
    a["icon_mesa"] = pygame.transform.scale(mesa, (66, 58))
    return a


class Game(object):
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        try:
            self.screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
        except Exception:
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("PSE - Projeto Simulador Evolutivo")
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        self.assets = load_assets()
        self.audio = Audio()
        self.state = GameState()
        self.stack = []
        self.pending = []
        self.toasts = []
        self.running = True

    # ---- pilha de cenas
    def push(self, scene):
        self.stack.append(scene)

    def pop(self):
        if self.stack:
            self.stack.pop()
        if self.stack:
            self.stack[-1].on_resume()

    def replace(self, scene):
        self.stack = [scene]

    def replace_top(self, scene):
        if self.stack:
            self.stack[-1] = scene
        else:
            self.stack.append(scene)

    # ---- serviços usados pelas cenas
    def queue_dialog(self, lines):
        self.pending.append(lines)

    def toast(self, text, dur=2.2, color=WHITE):
        self.toasts.append([text, dur, color])
        self.toasts = self.toasts[-4:]

    def gain_xp(self, n):
        st = self.state
        before = st.level
        st.xp += n
        self.toast("+%d XP" % n, 1.8, (170, 240, 190))
        if st.level > before:
            self.toast("NÍVEL %d!" % st.level, 3.0, YELLOW)
            self.audio.play("unlock")

    def hurt(self, n):
        st = self.state
        st.integrity = max(0, st.integrity - n)
        self.toast("Integridade do laboratório -%d" % n, 2.4, (255, 150, 140))
        if st.integrity <= 0:
            self.audio.play("bad")
            self.replace(GameOverScene(self))

    def end_game(self):
        self.state.done.add("final")
        self.state.log_event("final", "xp=%d" % self.state.xp, "concluido", True)
        self.replace(EndingScene(self))

    def restart(self):
        self.state.reset()
        self.state.intro_done = True
        self.pending = []
        self.audio.cur_stage = 0
        self.replace(World(self))

    def to_title(self):
        self.state.reset()
        self.pending = []
        self.audio.cur_stage = 0
        self.replace(TitleScene(self))

    # ---- laço principal
    def run(self):
        while self.running and self.stack:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    self.toast("Som desligado" if self.audio.toggle_mute() else "Som ligado", 1.2)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif self.stack:
                    self.stack[-1].handle(e)
            if not self.stack:
                break
            self.stack[-1].update(dt)
            if not self.stack:
                break
            self.stack[-1].draw(self.screen)
            self.draw_toasts(dt)
            pygame.display.flip()

    def draw_toasts(self, dt):
        f = self.fonts["s"]
        y = 92
        for t in self.toasts:
            t[1] -= dt
        self.toasts = [t for t in self.toasts if t[1] > 0]
        for text, _d, color in self.toasts:
            w = f.size(text)[0] + 28
            r = pygame.Rect(0, 0, w, 32)
            r.midtop = (W // 2, y)
            pygame.draw.rect(self.screen, (16, 20, 34), r, border_radius=8)
            pygame.draw.rect(self.screen, color, r, 2, border_radius=8)
            draw_text(self.screen, text, f, color, r.center, "center")
            y += 38


# ----------------------------------------------------------------- título
class TitleScene(Scene):
    def __init__(self, game):
        self.g = game
        self.t = 0.0
        w = game.assets["william"]
        self.big = pygame.transform.scale(w, (w.get_width() * 3, w.get_height() * 3))
        self.shade = pygame.Surface((W, H), pygame.SRCALPHA)
        self.shade.fill((10, 14, 30, 185))

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.g.audio.play("confirm")
                self.g.audio.music(1)
                self.g.replace(IntroScene(self.g))
            elif e.key == pygame.K_ESCAPE:
                self.g.running = False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.g.audio.play("confirm")
            self.g.audio.music(1)
            self.g.replace(IntroScene(self.g))

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        f = self.g.fonts
        surf.blit(self.g.assets["lab"], (0, 0))
        surf.blit(self.shade, (0, 0))
        draw_text(surf, "PSE", f["title"], (255, 236, 170), (W // 2, 78), "midtop", shadow=BLACK)
        draw_text(surf, "Projeto Simulador Evolutivo", f["xl"], WHITE, (W // 2, 160), "midtop", shadow=BLACK)
        bob = int(math.sin(self.t * 3) * 6)
        surf.blit(self.big, self.big.get_rect(midbottom=(W // 2 - 150, 500 + bob)))
        pc = self.g.assets["computador"]
        surf.blit(pc, pc.get_rect(midbottom=(W // 2 + 150, 490)))
        if int(self.t * 2) % 2 == 0:
            draw_text(surf, "Pressione ENTER para começar", f["l"], WHITE, (W // 2, 546), "midtop", shadow=BLACK)
        draw_text(surf, "ESC: sair    M: som    F11: tela cheia", f["s"], (190, 200, 225),
                  (W // 2, 596), "midtop")
        draw_text(surf, "Conceito e design: João Pedro Ferreira Rosa", f["s"], (190, 200, 225),
                  (W // 2, H - 22), "center")


# ------------------------------------------------------------------ intro
INTRO = [
    ("Narração", "Noruega. Uma manhã de fiordes, neve e café fraco."),
    ("William", "Seis meses de intercâmbio e a única coisa que dominei foi o aquecedor do apartamento..."),
    ("William", "Espera... aquele anúncio gigante: 'Laboratório de Pesquisa Genética - CONTRATANDO'. "
                "Fundado por um brasileiro?!"),
    ("Narração", "William Charles II, geneticista formado pela UFRJ, envia o currículo e aguarda uma resposta."),
    ("Roberto", "Hmm... William Charles II? Charles? Esse sobrenome... esse queixo... "
                "Esse rapaz tem cara de Charles."),
    ("Roberto", "Ele é meu PARENTE?! Contratado! Quem não contrata família, contrata o quê?"),
    ("Narração", "E assim começa uma nova fase na vida de William..."),
]


class IntroScene(Scene):
    def __init__(self, game):
        self.g = game
        self.t = 0.0
        self.snow = [[random.uniform(0, W), random.uniform(0, H), random.uniform(25, 70)]
                     for _ in range(90)]
        self.dialog = Dialog(game, INTRO, on_done=self.finish)

    def finish(self):
        self.g.state.intro_done = False   # o mundo mostra o tutorial
        self.g.replace(World(self.g))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.finish()
            return
        self.dialog.handle(e)

    def update(self, dt):
        self.t += dt
        for s in self.snow:
            s[1] += s[2] * dt
            s[0] += math.sin(self.t + s[2]) * 8 * dt
            if s[1] > H:
                s[1] = -4
                s[0] = random.uniform(0, W)
        self.dialog.update(dt)

    def draw(self, surf):
        gradient_bg(surf, (8, 16, 42), (44, 74, 96))
        for k, col in enumerate(((60, 220, 150), (90, 170, 230), (150, 120, 220))):
            pts = [(x, 120 + k * 36 + math.sin(x * 0.008 + self.t * 0.6 + k) * 34)
                   for x in range(0, W + 24, 24)]
            pygame.draw.lines(surf, col, False, pts, 5)
        pygame.draw.polygon(surf, (16, 24, 40), [(0, 430), (170, 300), (320, 400), (520, 260),
                                                 (720, 410), (900, 310), (W, 420), (W, 480), (0, 480)])
        pygame.draw.rect(surf, (220, 230, 240), (0, 476, W, H - 476))
        pygame.draw.rect(surf, (28, 52, 80), (0, 440, W, 40))
        w = self.g.assets["william"]
        surf.blit(w, w.get_rect(midbottom=(W // 2, 560)))
        for x, y, _s in self.snow:
            pygame.draw.circle(surf, WHITE, (int(x), int(y)), 2)
        self.dialog.draw(surf)
        draw_text(surf, "ESC: pular introdução", self.g.fonts["xs"], (190, 200, 225),
                  (W - 14, 12), "topright")


# -------------------------------------------------------------- game over
class GameOverScene(Scene):
    def __init__(self, game):
        self.g = game
        self.t = 0.0
        game.state.log_event("game_over", "", "laboratorio_destruido", False)

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.g.restart()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.g.to_title()

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        f = self.g.fonts
        gradient_bg(surf, (60, 10, 10), (18, 6, 10))
        for i in range(14):
            x = (i * 97 + int(self.t * 40)) % W
            y = H - 40 - int(abs(math.sin(self.t * 2 + i)) * 160)
            pygame.draw.circle(surf, (255, 150 + (i * 7) % 90, 40), (x, y), 8 + (i % 4) * 3)
        draw_text(surf, "O LABORATÓRIO FOI DESTRUÍDO", f["xl"], (255, 220, 200), (W // 2, 150), "center", shadow=BLACK)
        draw_wrapped(surf, "Roberto (interfone): Primo... eu avisei sobre a regra número um. "
                           "O seguro não cobre 'experimentos criativos'.",
                     f["m"], WHITE, pygame.Rect(180, 230, W - 360, 120), 6)
        draw_text(surf, "Cada erro tem consequências: contaminação, equipamento errado e criaturas soltas "
                        "cobram seu preço.", f["s"], (230, 190, 180), (W // 2, 380), "center")
        if int(self.t * 2) % 2 == 0:
            draw_text(surf, "ENTER: recomeçar    ESC: título", f["l"], WHITE, (W // 2, 480), "center")


# ------------------------------------------------------------------ final
class EndingScene(Scene):
    def __init__(self, game):
        self.g = game
        self.t = 0.0
        game.audio.play("unlock")

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                                  pygame.K_SPACE, pygame.K_ESCAPE):
            self.g.to_title()

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        f = self.g.fonts
        st = self.g.state
        gradient_bg(surf, (14, 24, 54), (6, 10, 24))
        for i in range(60):
            x = (i * 173) % W
            y = (i * 91 + int(self.t * 14)) % H
            pygame.draw.circle(surf, (120, 140, 200), (x, y), 1 + i % 2)
        draw_text(surf, "FIM DA TEMPORADA 1", f["xl"], (255, 236, 170), (W // 2, 70), "center", shadow=BLACK)
        draw_wrapped(surf, "William construiu o Computador Evolutivo: uma ferramenta capaz de simular a "
                           "evolução e apoiar pesquisas médicas e de bioinformática.",
                     f["m"], WHITE, pygame.Rect(160, 120, W - 320, 90), 6)
        s = st.stats
        lines = [
            "Nível alcançado: %d   XP: %d" % (st.level, st.xp),
            "Integridade do laboratório: %d%%   Recursos restantes: %d" % (st.integrity, st.budget),
            "Sequências analisadas: %d   Mutações encontradas: %d" % (s["dna_total"], s["mutations"]),
            "Experimentos realizados: %d   Gerações simuladas: %d" % (s["exp_runs"], s["sim_gens"]),
            "Decisões registradas: %d (arquivo pse_dados.csv)" % len(st.log),
        ]
        y = 250
        for ln in lines:
            draw_text(surf, ln, f["m"], (210, 220, 245), (W // 2, y), "center")
            y += 36
        w = self.g.assets["william"]
        pc = self.g.assets["computador"]
        surf.blit(w, w.get_rect(midbottom=(W // 2 - 120, 610 + int(math.sin(self.t * 3) * 4))))
        surf.blit(pc, pc.get_rect(midbottom=(W // 2 + 120, 604)))
        if int(self.t * 2) % 2 == 0:
            draw_text(surf, "ENTER: voltar ao título", f["s"], WHITE, (W // 2, H - 18), "center")


def main():
    os.chdir(BASE_DIR)
    try:
        game = Game()
    except Exception as exc:
        print("Erro ao iniciar o jogo:", exc)
        print("Verifique se a pasta 'assets' está ao lado de pse.py e se o pygame está instalado "
              "(pip install pygame).")
        sys.exit(1)
    game.push(TitleScene(game))
    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
