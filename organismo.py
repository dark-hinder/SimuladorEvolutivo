import pygame

class Organismo:
    def __init__(self,x,y, rgb):
        self.x = x
        self.y = y
        self.cor = (rgb[0], rgb[1], rgb[2])

        self.largura = 20
        self.altura = 20
        
    def desenhar(self, janela):
        pygame.draw.rect(janela,self.cor, (self.x, self.y, self.largura, self.altura))
        pygame.draw.rect(janela,(0, 0, 0),(self.x, self.y, self.largura, self.altura),2)