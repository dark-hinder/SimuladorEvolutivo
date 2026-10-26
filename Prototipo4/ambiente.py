import pygame

class Ambiente:

    def __init__(self):
        self.quadrantes = [
            ((255, 69, 0), (0, 0, 350, 350)),
            ((250, 250, 0), (350, 0, 350, 350)),
            ((24, 116, 205), (0, 350, 350, 350)),
            ((102, 205, 0), (350, 350, 350, 350))
        ]

    def desenhar(self, janela):
        for cor, retangulo in self.quadrantes:
            pygame.draw.rect(janela, cor, retangulo)

