import random

def GeraVida():
    tam = [random.randint(0,30)]
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    cor = (r,g,b)
    x = random.randint(0,300)
    y = random.randint(0,300)
    posi = (x,y)
    lista = {1:tam,3:posi,2:cor}
    return lista




father = GeraVida()
mother = GeraVida()
prole = []

for y in father:
    for i in range(len(father[y])):
        divi = father[y][i] + mother[y][i]
        total = divi/2
        prole.append(total)


print(f"pai: {father}")
print(f"mãe: {mother}")
print(f"filho: {prole}")
