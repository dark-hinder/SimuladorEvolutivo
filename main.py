import pygame
from organismo import Organismo
import random

pygame.init()

largura = 700
altura = 700


organismoLista = []
for i in range(12):
    def aletorio():
        return random.randint(0,255)
    rgb = [aletorio(),aletorio(),aletorio()]
    latX = random.randint(0,800)
    latY = random.randint(0,800)
    organismo = Organismo(latX, latY, rgb)
    organismoLista.append(organismo)

janela = pygame.display.set_mode([largura,altura])
pygame.display.set_caption("Evolução")

clock = pygame.time.Clock()
executando = True
while executando:
    
    eventos = pygame.event.get()
    for evento in eventos:
        if evento.type == pygame.QUIT:
            executando = False
    pygame.draw.rect(janela, (255, 69, 0), (0, 0, 350, 350))
    pygame.draw.rect(janela, (250, 250, 0), (350, 0, 350, 350))
    pygame.draw.rect(janela, (24, 116, 205), (0, 350, 350, 350))
    pygame.draw.rect(janela, (102, 205, 0), (350, 350, 350, 350))
    
    
    for i in range(12):
        organismoLista[i].desenhar(janela)
    
    pygame.display.update()
    clock.tick(30)

pygame.quit()