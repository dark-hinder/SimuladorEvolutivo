import pygame
import random
import math

pygame.init()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

LARGURA = 1000
ALTURA = 700

FPS = 60

POPULACAO_INICIAL = 100
COMIDA_INICIAL = 150

TAMANHO_CRIATURA = 8

ENERGIA_INICIAL = 100
ENERGIA_COMIDA = 35

CUSTO_VIDA = 0.04

# A cada quantos frames ocorre uma rodada de seleção
TEMPO_SELECAO = 300

# Quantidade máxima de criaturas
MAX_POPULACAO = 300

# Quantidade de criaturas eliminadas pelo predador
PREDADORES = 25

# Chance de uma mutação acontecer
TAXA_MUTACAO = 0.15

# Intensidade máxima da mutação de cor
FORCA_MUTACAO = 20


tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Evolução da Camuflagem")

clock = pygame.time.Clock()

fonte = pygame.font.SysFont("Arial", 20)
fonte_grande = pygame.font.SysFont("Arial", 28)


# ============================================================
# AMBIENTE
# ============================================================

# Cor do ambiente
COR_AMBIENTE = [100, 150, 100]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def distancia_cor(cor1, cor2):

    r1, g1, b1 = cor1
    r2, g2, b2 = cor2

    return math.sqrt(
        (r1 - r2) ** 2 +
        (g1 - g2) ** 2 +
        (b1 - b2) ** 2
    )


def mutar_cor(cor):

    nova_cor = list(cor)

    for i in range(3):

        if random.random() < TAXA_MUTACAO:

            nova_cor[i] += random.randint(
                -FORCA_MUTACAO,
                FORCA_MUTACAO
            )

    nova_cor[0] = limitar(nova_cor[0], 0, 255)
    nova_cor[1] = limitar(nova_cor[1], 0, 255)
    nova_cor[2] = limitar(nova_cor[2], 0, 255)

    return tuple(nova_cor)


# ============================================================
# COMIDA
# ============================================================

class Comida:

    def __init__(self):

        self.x = random.randint(10, LARGURA - 10)
        self.y = random.randint(10, ALTURA - 10)

        self.raio = 4

    def desenhar(self):

        pygame.draw.circle(
            tela,
            (230, 210, 50),
            (self.x, self.y),
            self.raio
        )


# ============================================================
# CRIATURA
# ============================================================

class Criatura:

    def __init__(self, cor=None):

        self.x = random.randint(
            20,
            LARGURA - 20
        )

        self.y = random.randint(
            20,
            ALTURA - 20
        )

        self.energia = ENERGIA_INICIAL

        self.idade = 0

        # ----------------------------------------------------
        # GENES
        # ----------------------------------------------------

        if cor is None:

            # População inicial possui cores aleatórias
            self.cor = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )

        else:

            self.cor = cor

    # ========================================================
    # MOVIMENTO
    # ========================================================

    def mover(self):

        # Movimento aleatório

        self.x += random.uniform(-1.5, 1.5)
        self.y += random.uniform(-1.5, 1.5)

        # Limites da tela

        self.x = limitar(
            self.x,
            TAMANHO_CRIATURA,
            LARGURA - TAMANHO_CRIATURA
        )

        self.y = limitar(
            self.y,
            TAMANHO_CRIATURA,
            ALTURA - TAMANHO_CRIATURA
        )

    # ========================================================
    # COMER
    # ========================================================

    def comer(self, comidas):

        for comida in comidas[:]:

            distancia = math.sqrt(
                (self.x - comida.x) ** 2 +
                (self.y - comida.y) ** 2
            )

            if distancia < TAMANHO_CRIATURA + comida.raio:

                self.energia += ENERGIA_COMIDA

                comidas.remove(comida)

                break

    # ========================================================
    # ATUALIZAR
    # ========================================================

    def atualizar(self, comidas):

        self.idade += 1

        self.energia -= CUSTO_VIDA

        self.mover()

        self.comer(comidas)

    # ========================================================
    # REPRODUÇÃO
    # ========================================================

    def reproduzir(self):

        # Filho recebe a cor do pai
        nova_cor = mutar_cor(self.cor)

        filho = Criatura(nova_cor)

        filho.x = self.x + random.randint(-20, 20)
        filho.y = self.y + random.randint(-20, 20)

        filho.x = limitar(
            filho.x,
            TAMANHO_CRIATURA,
            LARGURA - TAMANHO_CRIATURA
        )

        filho.y = limitar(
            filho.y,
            TAMANHO_CRIATURA,
            ALTURA - TAMANHO_CRIATURA
        )

        return filho

    # ========================================================
    # DESENHAR
    # ========================================================

    def desenhar(self):

        # Corpo
        pygame.draw.rect(
            tela,
            self.cor,
            (
                int(self.x - TAMANHO_CRIATURA),
                int(self.y - TAMANHO_CRIATURA),
                TAMANHO_CRIATURA * 2,
                TAMANHO_CRIATURA * 2
            )
        )

        # Borda
        pygame.draw.rect(
            tela,
            (255, 255, 255),
            (
                int(self.x - TAMANHO_CRIATURA),
                int(self.y - TAMANHO_CRIATURA),
                TAMANHO_CRIATURA * 2,
                TAMANHO_CRIATURA * 2
            ),
            1
        )


# ============================================================
# CRIAR POPULAÇÃO
# ============================================================

criaturas = []

for i in range(POPULACAO_INICIAL):

    criaturas.append(
        Criatura()
    )


# ============================================================
# CRIAR COMIDA
# ============================================================

comidas = []

for i in range(COMIDA_INICIAL):

    comidas.append(
        Comida()
    )


# ============================================================
# VARIÁVEIS DA SIMULAÇÃO
# ============================================================

geracao = 1

tempo = 0

sobreviventes_ultima_geracao = 0

rodando = True


# ============================================================
# LOOP PRINCIPAL
# ============================================================

while rodando:

    clock.tick(FPS)

    # ========================================================
    # EVENTOS
    # ========================================================

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:

            rodando = False

        # ----------------------------------------------------
        # ESPAÇO = nova rodada de seleção
        # ----------------------------------------------------

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_SPACE:

                tempo = TEMPO_SELECAO

            # ------------------------------------------------
            # R = reiniciar
            # ------------------------------------------------

            if evento.key == pygame.K_r:

                criaturas.clear()

                comidas.clear()

                geracao = 1

                tempo = 0

                for i in range(POPULACAO_INICIAL):

                    criaturas.append(
                        Criatura()
                    )

                for i in range(COMIDA_INICIAL):

                    comidas.append(
                        Comida()
                    )


    # ========================================================
    # ATUALIZAR CRIATURAS
    # ========================================================

    for criatura in criaturas:

        criatura.atualizar(comidas)


    # ========================================================
    # MORTE NATURAL
    # ========================================================

    criaturas = [

        criatura
        for criatura in criaturas
        if criatura.energia > 0

    ]


    # ========================================================
    # REPOVOAR COMIDA
    # ========================================================

    while len(comidas) < COMIDA_INICIAL:

        comidas.append(
            Comida()
        )


    # ========================================================
    # CONTADOR
    # ========================================================

    tempo += 1


    # ========================================================
    # SELEÇÃO NATURAL
    # ========================================================

    if tempo >= TEMPO_SELECAO:

        tempo = 0

        # ----------------------------------------------------
        # CALCULAR CAMUFLAGEM
        # ----------------------------------------------------

        candidatos = []

        for criatura in criaturas:

            contraste = distancia_cor(
                criatura.cor,
                COR_AMBIENTE
            )

            candidatos.append(
                (contraste, criatura)
            )


        # ----------------------------------------------------
        # ORDENAR
        #
        # Quanto maior o contraste,
        # mais fácil de enxergar.
        # ----------------------------------------------------

        candidatos.sort(
            key=lambda x: x[0],
            reverse=True
        )


        # ----------------------------------------------------
        # PREDADORES
        #
        # Eliminam os mais visíveis.
        # ----------------------------------------------------

        quantidade_mortes = min(
            PREDADORES,
            len(candidatos)
        )

        mortos = candidatos[
            :quantidade_mortes
        ]


        for contraste, criatura in mortos:

            if criatura in criaturas:

                criaturas.remove(
                    criatura
                )


        sobreviventes_ultima_geracao = len(
            criaturas
        )


        # ----------------------------------------------------
        # REPRODUÇÃO
        # ----------------------------------------------------

        pais = criaturas.copy()

        novos_filhos = []

        for criatura in pais:

            if len(criaturas) + len(novos_filhos) >= MAX_POPULACAO:

                break

            # Criaturas mais camufladas
            # possuem maior chance de reprodução

            contraste = distancia_cor(
                criatura.cor,
                COR_AMBIENTE
            )

            chance = 0.8 - (
                contraste / 400
            )

            chance = limitar(
                chance,
                0.1,
                0.8
            )

            if random.random() < chance:

                filho = criatura.reproduzir()

                novos_filhos.append(
                    filho
                )


        criaturas.extend(
            novos_filhos
        )


        # ----------------------------------------------------
        # NOVA GERAÇÃO
        # ----------------------------------------------------

        geracao += 1


    # ========================================================
    # DESENHAR AMBIENTE
    # ========================================================

    tela.fill(
        COR_AMBIENTE
    )


    # ========================================================
    # DESENHAR COMIDA
    # ========================================================

    for comida in comidas:

        comida.desenhar()


    # ========================================================
    # DESENHAR CRIATURAS
    # ========================================================

    for criatura in criaturas:

        criatura.desenhar()


    # ========================================================
    # ESTATÍSTICAS
    # ========================================================

    if criaturas:

        contrastes = []

        for criatura in criaturas:

            contraste = distancia_cor(
                criatura.cor,
                COR_AMBIENTE
            )

            contrastes.append(
                contraste
            )

        media_contraste = (
            sum(contrastes)
            / len(contrastes)
        )

    else:

        media_contraste = 0


    # ========================================================
    # TEXTOS
    # ========================================================

    texto = fonte.render(
        f"População: {len(criaturas)}",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (10, 10)
    )


    texto = fonte.render(
        f"Geração: {geracao}",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (10, 35)
    )


    texto = fonte.render(
        f"Contraste médio: {media_contraste:.1f}",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (10, 60)
    )


    texto = fonte.render(
        f"Sobreviventes: {sobreviventes_ultima_geracao}",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (10, 85)
    )


    # ========================================================
    # INSTRUÇÕES
    # ========================================================

    texto = fonte.render(
        "ESPAÇO = seleção natural | R = reiniciar",
        True,
        (255, 255, 255)
    )

    tela.blit(
        texto,
        (10, ALTURA - 30)
    )


    # ========================================================
    # ATUALIZAR TELA
    # ========================================================

    pygame.display.flip()


pygame.quit()