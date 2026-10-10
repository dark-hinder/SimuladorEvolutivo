import random
populacao = [] #[Tamanho, Camuflagem, Taxa_Agressividade ]
Selec = None

def Vida():
    TamanhoInicial = random.randint(1,20)
    Camuflagem = random.randint(0,10)
    Taxa = random.randint(0,100)
    linha = [TamanhoInicial,Camuflagem,Taxa]
    return linha
popNums = int(input("Digite a quantidade de individuos: "))
for i in range(popNums):
    populacao.append(Vida())

def Ambiente():
    pass

