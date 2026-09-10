import pygame
from organismo import Organismo
from ambiente import Ambiente
import random

pygame.init()

largura = 700
altura = 700



organismoLista = []

def gerar(number):
    for i in range(number):
        def aletorio():
            return random.randint(0,255)
        rgb = [aletorio(),aletorio(),aletorio()]
        latX = random.randint(0,679)
        latY = random.randint(0,679)
        organismo = Organismo(latX, latY, rgb)
        organismoLista.append(organismo)


gerar(12)

janela = pygame.display.set_mode([largura,altura])
pygame.display.set_caption("Evolução")

fundo = Ambiente()

clock = pygame.time.Clock()
executando = True

reproducao = False

while executando:
    if reproducao == True:
        gerar(1)
    eventos = pygame.event.get()
    for evento in eventos:
        if evento.type == pygame.QUIT:
            executando = False

    
    
    fundo.desenhar(janela)
    
    for i in range(len(organismoLista)):
        organismoLista[i].desenhar(janela)
    
    pygame.display.update()
    clock.tick(30)

pygame.quit()

