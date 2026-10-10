# -*- coding: utf-8 -*-
"""
PSE - Projeto Simulador Evolutivo
Lógica científica do jogo (sem pygame): genética, código genético,
simulação evolutiva e modelo do experimento controlado.
"""
import math
import random

# ---------------------------------------------------------------- DNA / RNA
BASES = "ACGT"
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}


def complement(seq):
    """Fita complementar (pareamento A-T e C-G)."""
    return "".join(COMP[b] for b in seq)


def transcribe(dna):
    """DNA (fita codificante) -> mRNA."""
    return dna.replace("T", "U")


def random_dna(n, rng=random):
    return "".join(rng.choice(BASES) for _ in range(n))


def point_mutation(seq, rng=random):
    """Substitui uma base. Retorna (nova_sequencia, indice_mutado)."""
    i = rng.randrange(len(seq))
    new = rng.choice([b for b in BASES if b != seq[i]])
    return seq[:i] + new + seq[i + 1:], i


def split_codons(seq):
    return [seq[i:i + 3] for i in range(0, len(seq) - len(seq) % 3, 3)]


def make_sequence_with_start(n, rng=random):
    """Sequência de n bases com exatamente um ATG. Retorna (seq, indice_do_A)."""
    while True:
        seq = random_dna(n, rng)
        if "ATG" in seq:
            continue
        pos = rng.randrange(0, n - 2)
        seq = seq[:pos] + "ATG" + seq[pos + 3:]
        if seq.count("ATG") == 1:
            return seq, pos


# Código genético padrão (tabela 1 do NCBI). Ordem das bases: T, C, A, G.
_AA_STR = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
CODON_TABLE = {}
_i = 0
for _a in "TCAG":
    for _b in "TCAG":
        for _c in "TCAG":
            CODON_TABLE[_a + _b + _c] = _AA_STR[_i]
            _i += 1

AA_INFO = {
    "F": ("Phe", "Fenilalanina"), "L": ("Leu", "Leucina"), "S": ("Ser", "Serina"),
    "Y": ("Tyr", "Tirosina"), "C": ("Cys", "Cisteína"), "W": ("Trp", "Triptofano"),
    "P": ("Pro", "Prolina"), "H": ("His", "Histidina"), "Q": ("Gln", "Glutamina"),
    "R": ("Arg", "Arginina"), "I": ("Ile", "Isoleucina"), "M": ("Met", "Metionina"),
    "T": ("Thr", "Treonina"), "N": ("Asn", "Asparagina"), "K": ("Lys", "Lisina"),
    "V": ("Val", "Valina"), "A": ("Ala", "Alanina"), "D": ("Asp", "Aspartato"),
    "E": ("Glu", "Glutamato"), "G": ("Gly", "Glicina"), "*": ("Stop", "Parada"),
}


def translate_codon(codon):
    return CODON_TABLE[codon]


def aa_short(letter):
    return AA_INFO[letter][0]


def aa_label(letter):
    a, b = AA_INFO[letter]
    return "%s - %s" % (a, b)


def mutation_effect(orig, mutated):
    """Classifica uma mutação pontual em um códon: silenciosa, missense ou nonsense."""
    a, b = CODON_TABLE[orig], CODON_TABLE[mutated]
    if a == b:
        return "silenciosa"
    if b == "*":
        return "nonsense"
    return "missense"


def make_mutation_question(target, rng=random):
    """Gera (codon_original, codon_mutado) cujo efeito seja `target`."""
    codons = [c for c in CODON_TABLE if CODON_TABLE[c] != "*"]
    for _ in range(2000):
        orig = rng.choice(codons)
        mut, _idx = point_mutation(orig, rng)
        if mutation_effect(orig, mut) == target:
            return orig, mut
    return "GAA", "GAG"  # silenciosa (fallback)


# ------------------------------------------------------- Simulação evolutiva
MUT_RATES = [0.0, 0.002, 0.005, 0.01, 0.02, 0.04, 0.08]
PRESSURES = [1, 2, 3, 4, 5]
SIZES = list(range(20, 201, 20))
RESOURCES = [0.5, 0.75, 1.0, 1.25, 1.5]
ENV_VALUES = [i / 20.0 for i in range(21)]


class Population:
    """Cada indivíduo tem 8 genes (0/1). O traço (cor da pelagem, 0 = clara,
    1 = escura) é a fração de genes 'escuros'. A aptidão depende da distância
    entre o traço e o ótimo do ambiente."""
    LOCI = 8

    def __init__(self, size=60, init_p=0.5, rng=None):
        self.rng = rng or random.Random()
        self.genomes = [[1 if self.rng.random() < init_p else 0
                         for _ in range(self.LOCI)] for _ in range(size)]
        self.generation = 0

    @staticmethod
    def trait(genome):
        return sum(genome) / float(len(genome))

    def traits(self):
        return [self.trait(g) for g in self.genomes]

    @staticmethod
    def fitness(t, optimum, pressure):
        sigma = 0.5 / max(0.5, pressure)
        return math.exp(-((t - optimum) ** 2) / (2.0 * sigma * sigma))

    def stats(self, optimum, pressure):
        ts = self.traits()
        n = len(ts)
        mean = sum(ts) / n
        var = sum((t - mean) ** 2 for t in ts) / n
        fit = sum(self.fitness(t, optimum, pressure) for t in ts) / n
        return {"mean": mean, "var": var, "fit": fit, "n": n}

    def step(self, optimum, pressure, mutation, size, resources):
        """Avança uma geração: seleção por aptidão, reprodução com
        recombinação e mutação. `resources` altera o tamanho efetivo."""
        w = [self.fitness(t, optimum, pressure) for t in self.traits()]
        if sum(w) <= 1e-12:
            w = [1.0] * len(w)
        n = max(8, int(size * resources))
        new = []
        for _ in range(n):
            a, b = self.rng.choices(self.genomes, weights=w, k=2)
            child = [a[i] if self.rng.random() < 0.5 else b[i]
                     for i in range(self.LOCI)]
            if mutation > 0:
                for i in range(self.LOCI):
                    if self.rng.random() < mutation:
                        child[i] = 1 - child[i]
            new.append(child)
        self.genomes = new
        self.generation += 1


def is_adapted(mean, optimum, tol=0.08):
    return abs(mean - optimum) <= tol


# ---------------------------------------------------- Experimento controlado
EXP_VARS = [
    ("temp", "Temperatura", "37 °C", "25 °C"),
    ("ph", "pH do meio", "7,0", "5,0"),
    ("luz", "Luz", "escuro", "luz intensa"),
    ("nutri", "Nutrientes", "1% de glicose", "0,1% de glicose"),
]

SAMPLES = [
    ("ecoli", "Cultura de E. coli (fresca, placa A-01)",
     "Colônias saudáveis, meio límpido. Parece uma boa candidata."),
    ("yeast", "Levedura seca (validade vencida)",
     "O pacote diz 'validade: 2019'. Será que ainda está viva?"),
    ("turva", "Amostra turva do fundo da geladeira (C-07)",
     "Está turva, com cheiro duvidoso e uma textura de gelatina verde."),
]

EQUIPS = [
    ("incub", "Incubadora com leitor de densidade óptica",
     "Mantém a temperatura e mede o crescimento da cultura ao longo do tempo."),
    ("centri", "Centrífuga",
     "Separa componentes por densidade. Gira muito rápido."),
    ("autoc", "Autoclave",
     "Esteriliza materiais com vapor a alta pressão. Mata TUDO."),
]

SCENARIOS = [
    dict(id="temp", var="temp",
         hip="Hipótese: a 25 °C a bactéria cresce mais devagar do que a 37 °C.",
         options=["A 25 °C a cultura cresceu mais devagar: a hipótese foi apoiada.",
                  "A temperatura não alterou o crescimento: as curvas são iguais.",
                  "A cultura cresceu mais rápido no frio: a hipótese foi refutada."],
         correct=0,
         why="Apenas a temperatura mudou entre controle e teste, então a "
             "diferença na curva pode ser atribuída a ela."),
    dict(id="ph", var="ph",
         hip="Hipótese: um meio ácido (pH 5,0) prejudica o crescimento da bactéria.",
         options=["O pH não teve efeito: as curvas são iguais.",
                  "No pH 5,0 o crescimento foi mais lento e menor: hipótese apoiada.",
                  "Qualquer diferença entre as curvas é só sorte, nada se conclui."],
         correct=1,
         why="Só o pH foi alterado, e a curva de teste ficou abaixo e mais "
             "lenta que a do controle."),
    dict(id="nutri", var="nutri",
         hip="Hipótese: com menos glicose, a população máxima da cultura será menor.",
         options=["Menos nutrientes aumentaram a população máxima.",
                  "Nutrientes só mudam a cor do meio, não o crescimento.",
                  "Com menos glicose o platô da população foi menor: hipótese apoiada."],
         correct=2,
         why="O platô (população máxima) é limitado pelos nutrientes disponíveis."),
]


def growth_curve(altered, t_max=24.0, n=25):
    """Crescimento logístico. Retorna lista de n pontos (células x1000/mL)."""
    r, K, N0 = 0.55, 1000.0, 10.0
    if "temp" in altered:
        r *= 0.45
    if "ph" in altered:
        r *= 0.6
        K *= 0.8
    if "nutri" in altered:
        r *= 0.85
        K *= 0.3
    # 'luz' não afeta uma bactéria não fotossintética
    pts = []
    for i in range(n):
        t = i * t_max / (n - 1)
        pts.append(K / (1.0 + ((K - N0) / N0) * math.exp(-r * t)))
    return pts


def evaluate_experiment(sample_id, equip_id, altered, scenario):
    """Retorna dict(status, msg, hurt). Status:
    contaminada, amostra_ruim, autoclave, equip_errado, sem_variavel,
    confusao, fora_da_hipotese, ok."""
    if sample_id == "turva":
        return dict(status="contaminada", hurt=12,
                    msg="CONTAMINAÇÃO! A amostra turva estava cheia de fungos e "
                        "a bancada precisou ser isolada.")
    if sample_id == "yeast":
        return dict(status="amostra_ruim", hurt=3,
                    msg="A levedura vencida não cresceu em nenhuma condição. "
                        "Amostra inadequada para este teste.")
    if equip_id == "autoc":
        return dict(status="autoclave", hurt=8,
                    msg="Você esterilizou a cultura. Resultado: zero bactérias "
                        "e um alarme de incêndio.")
    if equip_id == "centri":
        return dict(status="equip_errado", hurt=5,
                    msg="A centrífuga separou o meio, mas não mede crescimento. "
                        "Equipamento errado para a pergunta.")
    if len(altered) == 0:
        return dict(status="sem_variavel", hurt=0,
                    msg="Nada foi alterado: sem diferença entre controle e "
                        "teste, não há o que comparar.")
    if len(altered) >= 2:
        return dict(status="confusao", hurt=0,
                    msg="Você alterou várias variáveis ao mesmo tempo. Não dá "
                        "para saber qual causou a diferença: resultado inconclusivo.")
    only = next(iter(altered))
    if only != scenario["var"]:
        return dict(status="fora_da_hipotese", hurt=0,
                    msg="Você testou outra variável, que não é a da hipótese. "
                        "O controle foi bom, mas a pergunta ficou sem resposta.")
    return dict(status="ok", hurt=0,
                msg="Experimento bem controlado: só uma variável mudou. "
                    "Observe as curvas e interprete o resultado.")
