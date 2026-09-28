"""
Tela inicial (menu principal) em Pygame para um jogo evolutivo.

Como rodar:
    pip install pygame
    python tela_inicial.py

Controles:
    Setas ↑ ↓ ou W/S  -> navegar
    ENTER / ESPAÇO    -> selecionar
    Mouse             -> passar por cima e clicar
    ESC               -> sair
"""
import math
import random
import sys

import pygame

# ---------- Configurações ----------
LARGURA, ALTURA = 960, 600
FPS = 60
TITULO_JOGO = "EVOLUTIVO"
SUBTITULO = "Adapte-se. Evolua. Sobreviva."

COR_FUNDO_TOPO = (8, 14, 30)
COR_FUNDO_BAIXO = (14, 40, 60)
COR_TITULO = (120, 255, 190)
COR_TEXTO = (220, 235, 240)
COR_DESTAQUE = (255, 214, 90)
COR_BOTAO = (25, 50, 70)
COR_BOTAO_SEL = (40, 110, 110)


# ---------- Fundo animado: "células" flutuando ----------
class Celula:
    def __init__(self):
        self.reset(inicial=True)

    def reset(self, inicial=False):
        self.x = random.uniform(0, LARGURA)
        self.y = random.uniform(0, ALTURA) if inicial else ALTURA + 30
        self.raio = random.randint(4, 22)
        self.vel = random.uniform(0.2, 0.9)
        self.fase = random.uniform(0, math.tau)
        self.cor = random.choice([(80, 220, 170), (90, 170, 240), (170, 120, 240)])

    def atualizar(self, t):
        self.y -= self.vel
        self.x += math.sin(t * 0.8 + self.fase) * 0.4
        if self.y < -30:
            self.reset()

    def desenhar(self, tela, t):
        pulso = 1 + 0.12 * math.sin(t * 2 + self.fase)
        r = int(self.raio * pulso)
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.cor, 40), (r * 2, r * 2), r * 2)   # brilho
        pygame.draw.circle(surf, (*self.cor, 120), (r * 2, r * 2), r)      # corpo
        pygame.draw.circle(surf, (255, 255, 255, 90), (r * 2 - r // 3, r * 2 - r // 3), max(1, r // 3))
        tela.blit(surf, (self.x - r * 2, self.y - r * 2))


def gradiente_vertical(largura, altura, topo, base):
    surf = pygame.Surface((largura, altura))
    for y in range(altura):
        k = y / altura
        cor = tuple(int(topo[i] + (base[i] - topo[i]) * k) for i in range(3))
        pygame.draw.line(surf, cor, (0, y), (largura, y))
    return surf


# ---------- Botão do menu ----------
class Botao:
    def __init__(self, texto, centro_y, fonte):
        self.texto = texto
        self.fonte = fonte
        self.rect = pygame.Rect(0, 0, 320, 52)
        self.rect.center = (LARGURA // 2, centro_y)

    def desenhar(self, tela, selecionado):
        cor_fundo = COR_BOTAO_SEL if selecionado else COR_BOTAO
        cor_texto = COR_DESTAQUE if selecionado else COR_TEXTO
        rect = self.rect.inflate(16, 6) if selecionado else self.rect
        pygame.draw.rect(tela, cor_fundo, rect, border_radius=14)
        pygame.draw.rect(tela, COR_TITULO if selecionado else (60, 90, 110), rect, 2, border_radius=14)
        img = self.fonte.render(self.texto, True, cor_texto)
        tela.blit(img, img.get_rect(center=rect.center))


# ---------- Tela inicial ----------
def tela_inicial(tela, relogio):
    fonte_titulo = pygame.font.SysFont("arial", 96, bold=True)
    fonte_sub = pygame.font.SysFont("arial", 24, italic=True)
    fonte_botao = pygame.font.SysFont("arial", 28, bold=True)
    fonte_rodape = pygame.font.SysFont("arial", 16)

    fundo = gradiente_vertical(LARGURA, ALTURA, COR_FUNDO_TOPO, COR_FUNDO_BAIXO)
    celulas = [Celula() for _ in range(45)]

    opcoes = ["JOGAR", "OPÇÕES", "SAIR"]
    botoes = [Botao(txt, 330 + i * 70, fonte_botao) for i, txt in enumerate(opcoes)]
    indice = 0
    t = 0.0

    while True:
        dt = relogio.tick(FPS) / 1000
        t += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    indice = (indice - 1) % len(botoes)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    indice = (indice + 1) % len(botoes)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return opcoes[indice].lower()
                elif evento.key == pygame.K_ESCAPE:
                    return "sair"

            if evento.type == pygame.MOUSEMOTION:
                for i, b in enumerate(botoes):
                    if b.rect.collidepoint(evento.pos):
                        indice = i

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, b in enumerate(botoes):
                    if b.rect.collidepoint(evento.pos):
                        return opcoes[i].lower()

        # --- desenho ---
        tela.blit(fundo, (0, 0))
        for c in celulas:
            c.atualizar(t)
            c.desenhar(tela, t)

        # título com leve flutuação e sombra
        oscila = math.sin(t * 2) * 6
        sombra = fonte_titulo.render(TITULO_JOGO, True, (0, 0, 0))
        titulo = fonte_titulo.render(TITULO_JOGO, True, COR_TITULO)
        pos = titulo.get_rect(center=(LARGURA // 2, 130 + oscila))
        tela.blit(sombra, pos.move(4, 5))
        tela.blit(titulo, pos)

        sub = fonte_sub.render(SUBTITULO, True, COR_TEXTO)
        tela.blit(sub, sub.get_rect(center=(LARGURA // 2, 210)))

        for i, b in enumerate(botoes):
            b.desenhar(tela, i == indice)

        rodape = fonte_rodape.render("↑ ↓ navegar  •  ENTER selecionar  •  ESC sair", True, (140, 165, 180))
        tela.blit(rodape, rodape.get_rect(center=(LARGURA // 2, ALTURA - 24)))

        pygame.display.flip()


# ---------- Programa principal ----------
def main():
    pygame.init()
    pygame.display.set_caption(TITULO_JOGO)
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    relogio = pygame.time.Clock()

    escolha = tela_inicial(tela, relogio)

    if escolha == "jogar":
        print("Iniciar o jogo aqui!")      # TODO: chamar sua função/cena do jogo
    elif escolha == "opções":
        print("Abrir tela de opções aqui!")  # TODO: criar a tela de opções

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()