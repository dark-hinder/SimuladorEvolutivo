import random

class Organismo:
    def __init__(self, tamanho, cor, posicao):
        self._Tamanho = tamanho
        self._Cor = cor
        self._Posicao = posicao

    def retornaTamanho(self):
        return self._Tamanho

    def retornaCor(self):
        return self._Cor

    def retornaPosicao(self):
        return self._Posicao

    def mostrar(self):
        print(f"Tamanho: {self._Tamanho}  Cor: {self._Cor[0],self._Cor[1],self._Cor[2]}  Posição: {self._Posicao[0],self._Posicao[1]}\n")

def GeraVida():
    tam = random.randint(0,30)
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    cor = [r,g,b]
    x = random.randint(0,300)
    y = random.randint(0,300)
    posi = [x,y]
    Obj = Organismo(tam,cor,posi)
    return Obj

def reproducao(mae, pai):
    filhoT = (mae.retornaTamanho() + pai.retornaTamanho())/2

    corM = mae.retornaCor() 
    corP = pai.retornaCor()
    filhoC = [(corM[0]+corP[0])/2,(corM[1]+corP[1])/2,(corM[2]+corP[2])/2]

    porM = mae.retornaPosicao()
    porP = pai.retornaPosicao()
    filhoP = [(porM[0] + porP[0])/2,(porM[1] + porP[1])/2]

    FilhoObj = Organismo(filhoT, filhoC, filhoP)

    return FilhoObj

Organismo1 = GeraVida()
Organismo2 = GeraVida()
Organismo1.mostrar()
Organismo2.mostrar()
Filho = reproducao(Organismo1,Organismo2)
Filho.mostrar()