# -*- coding: utf-8 -*-
"""
PSE - Projeto Simulador Evolutivo
Minigames: análise genética, tradução de códons, experimento controlado,
simulação evolutiva, terminal do laboratório e montagem do Computador Evolutivo.
"""
import math
import random

import pygame

from pse_core import *
from pse_logic import *


def is_confirm(e):
    return e.type == pygame.KEYDOWN and e.key in CONFIRM_KEYS


def is_click(e):
    return e.type == pygame.MOUSEBUTTONDOWN and e.button == 1


class Mini(Scene):
    """Base dos minigames: fundo 'tela de computador', cabeçalho e rodapé."""
    icon_name = "icon_pc"

    def __init__(self, game):
        self.g = game
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def close(self):
        if self.g.stack and self.g.stack[-1] is self:
            self.g.pop()

    def bg(self, surf):
        gradient_bg(surf, (22, 30, 52), (10, 14, 26))
        for x in range(0, W, 48):
            pygame.draw.line(surf, (26, 36, 62), (x, 0), (x, H))
        for y in range(0, H, 48):
            pygame.draw.line(surf, (26, 36, 62), (0, y), (W, y))

    def header(self, surf, title, right=""):
        f = self.g.fonts
        inner = draw_panel(surf, (24, 16, W - 48, 72))
        icon = self.g.assets.get(self.icon_name)
        if icon:
            surf.blit(icon, icon.get_rect(midleft=(inner.x + 8, inner.centery)))
        draw_text(surf, title, f["l"], INK, (inner.x + 84, inner.centery), "midleft")
        if right:
            draw_text(surf, right, f["m"], INK, (inner.right - 14, inner.centery), "midright")

    def footer(self, surf, text):
        draw_text(surf, text, self.g.fonts["s"], (170, 180, 205), (W // 2, H - 20), "center")

    def feedback_panel(self, surf, ok, text, hint="ENTER para continuar", y=470, h=150):
        f = self.g.fonts
        inner = draw_panel(surf, (24, y, W - 48, h), accent=GREEN if ok else RED)
        title = "CORRETO!" if ok else "NÃO FOI DESSA VEZ"
        draw_text(surf, title, f["l"], (40, 140, 70) if ok else (190, 60, 50),
                  (inner.x + 18, inner.y + 10))
        draw_wrapped(surf, text, f["m"], INK,
                     pygame.Rect(inner.x + 18, inner.y + 48, inner.w - 36, h - 90))
        draw_text(surf, hint, f["s"], GRAY, (inner.right - 14, inner.bottom - 8), "bottomright")


# ============================================================ ANÁLISE GENÉTICA
class DNAScene(Mini):
    INSTR = {
        "complement": "Complete a fita complementar do DNA. Pareamento: A com T e C com G. "
                      "Digite A, T, C ou G (ou clique nos botões) e confirme com ENTER.",
        "mutation": "Compare a referência com a amostra do paciente: uma base mudou "
                    "(mutação pontual). Use as setas e ENTER, ou clique na base alterada.",
        "start": "Procure o códon de iniciação ATG: é onde a tradução começa. "
                 "Selecione a base A desse ATG (setas + ENTER, ou clique).",
    }

    def __init__(self, game):
        super().__init__(game)
        self.length = {1: 8, 2: 10, 3: 12}[game.state.stage]
        self.kinds = ["complement", "mutation", "start"]
        random.shuffle(self.kinds)
        self.round = 0
        self.correct = 0
        self.hit = []
        self.buttons = []
        self.submit_rect = None
        self.first_time = "dna" not in game.state.done
        self.new_round()

    def new_round(self):
        self.kind = self.kinds[self.round]
        self.cursor = 0
        self.fb_ok = False
        self.fb_text = ""
        self.typed = ""
        if self.kind == "complement":
            self.seq = random_dna(self.length)
        elif self.kind == "mutation":
            self.ref = random_dna(16)
            self.sam, self.idx = point_mutation(self.ref)
        else:
            self.seq, self.idx = make_sequence_with_start(18)
        self.mode = "ask"

    # ---- entrada
    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.close()
            return
        if self.mode == "summary":
            if is_confirm(e) or is_click(e):
                self.finish()
        elif self.mode == "feedback":
            if is_confirm(e) or is_click(e):
                self.round += 1
                if self.round >= 3:
                    self.mode = "summary"
                else:
                    self.new_round()
        elif self.kind == "complement":
            self.handle_complement(e)
        else:
            self.handle_pick(e)

    def handle_complement(self, e):
        full = len(self.typed) == len(self.seq)
        if e.type == pygame.KEYDOWN:
            letter = {pygame.K_a: "A", pygame.K_t: "T", pygame.K_c: "C",
                      pygame.K_g: "G"}.get(e.key)
            if letter and not full:
                self.typed += letter
                self.g.audio.play("select")
            elif e.key == pygame.K_BACKSPACE:
                self.typed = self.typed[:-1]
            elif e.key in ENTER_KEYS and full:
                self.evaluate(self.typed == complement(self.seq))
        elif is_click(e):
            for rect, letter in self.buttons:
                if rect.collidepoint(e.pos) and not full:
                    self.typed += letter
                    self.g.audio.play("select")
                    return
            if self.submit_rect and self.submit_rect.collidepoint(e.pos) and full:
                self.evaluate(self.typed == complement(self.seq))

    def handle_pick(self, e):
        n = len(self.sam) if self.kind == "mutation" else len(self.seq)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a):
                self.cursor = max(0, self.cursor - 1)
                self.g.audio.play("select")
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.cursor = min(n - 1, self.cursor + 1)
                self.g.audio.play("select")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.evaluate(self.cursor == self.idx)
        elif e.type == pygame.MOUSEMOTION:
            for rect, i in self.hit:
                if rect.collidepoint(e.pos):
                    self.cursor = i
        elif is_click(e):
            for rect, i in self.hit:
                if rect.collidepoint(e.pos):
                    self.cursor = i
                    self.evaluate(i == self.idx)
                    return

    # ---- avaliação
    def evaluate(self, ok):
        st = self.g.state
        st.stats["dna_total"] += 1
        self.fb_ok = ok
        if ok:
            self.correct += 1
            st.stats["dna_ok"] += 1
            self.g.gain_xp(10 if self.first_time else 2)
            self.g.audio.play("mutation" if self.kind == "mutation" else "ok")
        else:
            self.g.audio.play("bad")
        if self.kind == "complement":
            ans = complement(self.seq)
            detail = "seq=%s;resp=%s" % (self.seq, self.typed)
            if ok:
                self.fb_text = "Isso! A fita complementar de %s é %s. Cada A pareia com T e cada C com G." % (self.seq, ans)
            else:
                self.fb_text = "A resposta certa era %s (você digitou %s). Lembre: A-T e C-G." % (ans, self.typed)
        elif self.kind == "mutation":
            detail = "idx=%d;resp=%d" % (self.idx, self.cursor)
            if ok:
                st.stats["mutations"] += 1
                self.fb_text = ("Mutação encontrada na posição %d: %s virou %s. É uma mutação pontual "
                                "(substituição de uma única base)." % (self.idx + 1, self.ref[self.idx], self.sam[self.idx]))
            else:
                self.fb_text = ("A diferença estava na posição %d (%s na referência, %s na amostra). "
                                "Compare base por base." % (self.idx + 1, self.ref[self.idx], self.sam[self.idx]))
        else:
            detail = "idx=%d;resp=%d" % (self.idx, self.cursor)
            if ok:
                self.fb_text = ("O ATG começa na posição %d. A tradução inicia ali e segue lendo em "
                                "trincas (códons)." % (self.idx + 1))
            else:
                self.fb_text = "O ATG estava na posição %d. Procure a trinca A-T-G em sequência." % (self.idx + 1)
        st.log_event("dna_" + self.kind, detail, "acerto" if ok else "erro", ok)
        self.mode = "feedback"

    def finish(self):
        st = self.g.state
        if self.correct >= 2:
            if "dna" not in st.done:
                st.done.add("dna")
                self.g.gain_xp(20)
        else:
            self.g.queue_dialog([("Roberto (interfone)",
                                  "Só %d acerto(s) em 3. Revise o pareamento A-T / C-G e tente de novo, "
                                  "primo. DNA não morde." % self.correct)])
        self.close()

    # ---- desenho
    def draw(self, surf):
        f = self.g.fonts
        self.bg(surf)
        self.header(surf, "ANÁLISE GENÉTICA", "Rodada %d/3   Acertos: %d" % (min(self.round + 1, 3), self.correct))
        self.hit = []
        self.buttons = []
        self.submit_rect = None
        if self.mode == "summary":
            self.draw_summary(surf)
            return
        inner = draw_panel(surf, (24, 100, W - 48, 84), fill=(236, 242, 255), accent=BLUE)
        draw_wrapped(surf, self.INSTR[self.kind], f["m"], INK,
                     pygame.Rect(inner.x + 14, inner.y + 10, inner.w - 28, 60))
        fb = self.mode == "feedback"
        if self.kind == "complement":
            self.draw_complement(surf, fb)
        elif self.kind == "mutation":
            self.draw_mutation(surf, fb)
        else:
            self.draw_start(surf, fb)
        if fb:
            self.feedback_panel(surf, self.fb_ok, self.fb_text)
        self.footer(surf, "ESC: sair da análise")

    def draw_complement(self, surf, fb):
        f = self.g.fonts
        n = len(self.seq)
        draw_text(surf, "Fita molde", f["s"], (170, 180, 205), (W // 2, 226), "center")
        for ch, c in zip(self.seq, row_centers(n, y=268)):
            draw_base(surf, f["l"], ch, c)
        draw_text(surf, "Sua fita complementar", f["s"], (170, 180, 205), (W // 2, 326), "center")
        ans = complement(self.seq)
        for i, c in enumerate(row_centers(n, y=370)):
            if i < len(self.typed):
                state = None
                if fb:
                    state = "good" if self.typed[i] == ans[i] else "bad"
                draw_base(surf, f["l"], self.typed[i], c, state=state)
            else:
                draw_empty_slot(surf, c)
        if not fb:
            mouse = pygame.mouse.get_pos()
            for k, letter in enumerate("ATCG"):
                center = (W // 2 - 260 + k * 76, 480)
                probe = pygame.Rect(0, 0, 56, 56)
                probe.center = center
                state = "hover" if probe.collidepoint(mouse) else None
                r = draw_base(surf, f["l"], letter, center, size=56, state=state)
                self.buttons.append((r, letter))
            full = len(self.typed) == n
            self.submit_rect = pygame.Rect(W // 2 + 40, 452, 230, 56)
            inner = draw_panel(surf, self.submit_rect, fill=(200, 235, 205) if full else (225, 225, 230),
                               accent=GREEN if full else GRAY, radius=8, width=3)
            draw_text(surf, "CONFIRMAR (ENTER)", f["s"], INK, inner.center, "center")
            draw_text(surf, "BACKSPACE apaga", f["xs"], (150, 160, 190), (W // 2 - 260, 530))

    def draw_mutation(self, surf, fb):
        f = self.g.fonts
        n = len(self.ref)
        draw_text(surf, "Referência (saudável)", f["s"], (170, 180, 205), (W // 2, 222), "center")
        draw_text(surf, "Amostra do paciente", f["s"], (170, 180, 205), (W // 2, 312), "center")
        c_ref = row_centers(n, y=266)
        c_sam = row_centers(n, y=356)
        for i in range(n):
            draw_base(surf, f["l"], self.ref[i], c_ref[i])
            state = None
            if fb:
                if i == self.idx:
                    state = "good"
                elif i == self.cursor:
                    state = "bad"
            elif i == self.cursor:
                state = "hover"
            draw_base(surf, f["l"], self.sam[i], c_sam[i], state=state)
            draw_text(surf, str(i + 1), f["xs"], (130, 142, 172), (c_sam[i][0], 394), "center")
            probe = pygame.Rect(0, 0, 46, 46)
            probe.center = c_sam[i]
            self.hit.append((probe, i))

    def draw_start(self, surf, fb):
        f = self.g.fonts
        n = len(self.seq)
        draw_text(surf, "Sequência codificante", f["s"], (170, 180, 205), (W // 2, 250), "center")
        cs = row_centers(n, y=316)
        for i in range(n):
            state = None
            if fb:
                if self.idx <= i < self.idx + 3:
                    state = "good"
                elif i == self.cursor:
                    state = "bad"
            elif i == self.cursor:
                state = "hover"
            draw_base(surf, f["l"], self.seq[i], cs[i], state=state)
            draw_text(surf, str(i + 1), f["xs"], (130, 142, 172), (cs[i][0], 354), "center")
            probe = pygame.Rect(0, 0, 46, 46)
            probe.center = cs[i]
            self.hit.append((probe, i))

    def draw_summary(self, surf):
        f = self.g.fonts
        inner = draw_panel(surf, (160, 150, W - 320, 330), accent=BLUE)
        draw_text(surf, "RELATÓRIO DA ANÁLISE", f["xl"], INK, (inner.centerx, inner.y + 20), "midtop")
        draw_text(surf, "Acertos: %d / 3" % self.correct, f["l"], INK, (inner.centerx, inner.y + 100), "midtop")
        if self.correct >= 2:
            msg = "Análise aprovada! Você identificou padrões e mutações com precisão."
            col = (40, 140, 70)
        else:
            msg = "São necessários pelo menos 2 acertos. Revise e tente de novo."
            col = (190, 60, 50)
        draw_wrapped(surf, msg, f["m"], col, pygame.Rect(inner.x + 30, inner.y + 160, inner.w - 60, 90))
        draw_text(surf, "ENTER para voltar ao laboratório", f["s"], GRAY,
                  (inner.centerx, inner.bottom - 12), "midbottom")


# ============================================================ BANCO DE DADOS
class BankScene(Mini):
    icon_name = "icon_mesa"
    MUT_OPTS = ["Silenciosa (mesmo aminoácido)", "Missense (troca de aminoácido)",
                "Nonsense (vira códon de parada)"]
    MUT_IDX = {"silenciosa": 0, "missense": 1, "nonsense": 2}

    def __init__(self, game):
        super().__init__(game)
        self.qs = self.build_questions()
        self.q = 0
        self.sel = 0
        self.correct = 0
        self.mode = "ask"      # ask | feedback | summary
        self.show_table = False
        self.fb_ok = False
        self.fb_text = ""
        self.opt_rects = []
        self.first_time = "bank" not in game.state.done

    def build_questions(self):
        qs = []
        normal = [c for c in CODON_TABLE if CODON_TABLE[c] != "*"]
        for kind in ("translate", "mutation", "translate_stop", "mutation"):
            if kind.startswith("translate"):
                codon = random.choice(["TAA", "TAG", "TGA"]) if kind == "translate_stop" else random.choice(normal)
                aa = CODON_TABLE[codon]
                others = [a for a in AA_INFO if a != aa]
                random.shuffle(others)
                letters = [aa] + others[:3]
                random.shuffle(letters)
                qs.append(dict(kind="translate", codon=codon,
                               text="Qual aminoácido é codificado por este códon da fita codificante?",
                               options=[aa_label(a) for a in letters],
                               correct=letters.index(aa),
                               expl="%s -> mRNA %s -> %s." % (codon, transcribe(codon), aa_label(aa))))
            else:
                target = random.choice(["silenciosa", "missense", "nonsense"])
                orig, mut = make_mutation_question(target)
                a, b = CODON_TABLE[orig], CODON_TABLE[mut]
                qs.append(dict(kind="mutation", codon=orig, mutated=mut,
                               text="Uma mutação pontual mudou o códon. Que tipo de mutação é essa?",
                               options=list(self.MUT_OPTS), correct=self.MUT_IDX[target],
                               expl="%s codifica %s e %s codifica %s: mutação %s." %
                                    (orig, aa_short(a), mut, aa_short(b), target)))
        return qs

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.show_table:
                self.show_table = False
            else:
                self.close()
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_TAB, pygame.K_t):
            self.show_table = not self.show_table
            self.g.audio.play("select")
            return
        if self.show_table:
            return
        if self.mode == "summary":
            if is_confirm(e) or is_click(e):
                self.finish()
        elif self.mode == "feedback":
            if is_confirm(e) or is_click(e):
                self.q += 1
                self.sel = 0
                self.mode = "summary" if self.q >= len(self.qs) else "ask"
        else:
            n = len(self.qs[self.q]["options"])
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = (self.sel - 1) % n
                    self.g.audio.play("select")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = (self.sel + 1) % n
                    self.g.audio.play("select")
                elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    k = e.key - pygame.K_1
                    if k < n:
                        self.sel = k
                        self.answer()
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.answer()
            elif e.type == pygame.MOUSEMOTION:
                for r, i in self.opt_rects:
                    if r.collidepoint(e.pos):
                        self.sel = i
            elif is_click(e):
                for r, i in self.opt_rects:
                    if r.collidepoint(e.pos):
                        self.sel = i
                        self.answer()
                        return

    def answer(self):
        st = self.g.state
        q = self.qs[self.q]
        ok = self.sel == q["correct"]
        st.stats["bank_total"] += 1
        self.fb_ok = ok
        if ok:
            self.correct += 1
            st.stats["bank_ok"] += 1
            self.g.gain_xp(10 if self.first_time else 2)
            self.g.audio.play("ok")
            self.fb_text = "Muito bem! " + q["expl"]
        else:
            self.g.audio.play("bad")
            self.fb_text = "Resposta certa: %s. %s" % (q["options"][q["correct"]], q["expl"])
        st.log_event("codon_" + q["kind"], "codon=%s;resp=%d" % (q["codon"], self.sel),
                     "acerto" if ok else "erro", ok)
        self.mode = "feedback"

    def finish(self):
        st = self.g.state
        if self.correct >= 3:
            if "bank" not in st.done:
                st.done.add("bank")
                self.g.gain_xp(20)
        else:
            self.g.queue_dialog([("Roberto (interfone)",
                                  "%d acertos em 4. Consulte a tabela de códons (TAB) com calma e "
                                  "tente de novo. Ela existe para isso." % self.correct)])
        self.close()

    def draw(self, surf):
        f = self.g.fonts
        self.bg(surf)
        n = min(self.q + 1, len(self.qs))
        self.header(surf, "BANCO DE DADOS BIOLÓGICOS", "Questão %d/%d   Acertos: %d" % (n, len(self.qs), self.correct))
        self.opt_rects = []
        if self.mode == "summary":
            self.draw_summary(surf)
        else:
            q = self.qs[self.q]
            inner = draw_panel(surf, (24, 100, W - 48, 70), fill=(236, 242, 255), accent=BLUE)
            draw_wrapped(surf, q["text"], f["m"], INK, pygame.Rect(inner.x + 14, inner.y + 10, inner.w - 28, 50))
            if q["kind"] == "translate":
                draw_text(surf, "Fita codificante (DNA)", f["s"], (170, 180, 205), (W // 2, 200), "center")
                for ch, c in zip(q["codon"], row_centers(3, size=54, gap=10, y=250)):
                    draw_base(surf, f["xl"], ch, c, size=54)
            else:
                draw_text(surf, "Códon original", f["s"], (170, 180, 205), (W // 2 - 170, 200), "center")
                draw_text(surf, "Códon mutado", f["s"], (170, 180, 205), (W // 2 + 170, 200), "center")
                for i, c in enumerate(row_centers(3, size=54, gap=10, y=250)):
                    draw_base(surf, f["xl"], q["codon"][i], (c[0] - 170, c[1]), size=54)
                    state = "bad" if q["codon"][i] != q["mutated"][i] else None
                    draw_base(surf, f["xl"], q["mutated"][i], (c[0] + 170, c[1]), size=54, state=state)
            y0 = 306
            for i, opt in enumerate(q["options"]):
                r = pygame.Rect(W // 2 - 300, y0 + i * 40, 600, 36)
                chosen = (i == self.sel)
                if self.mode == "feedback":
                    if i == q["correct"]:
                        accent, fill = GREEN, (214, 244, 220)
                    elif chosen:
                        accent, fill = RED, (250, 218, 214)
                    else:
                        accent, fill = GRAY, (236, 236, 240)
                else:
                    accent, fill = (BLUE, (255, 244, 205)) if chosen else (GRAY, (236, 236, 240))
                inn = draw_panel(surf, r, fill=fill, accent=accent, radius=8, width=3)
                draw_text(surf, "%d  %s" % (i + 1, opt), f["m"], INK, (inn.x + 14, inn.centery), "midleft")
                self.opt_rects.append((r, i))
            if self.mode == "feedback":
                self.feedback_panel(surf, self.fb_ok, self.fb_text, y=484, h=140)
        self.footer(surf, "TAB: tabela de códons    1-4 ou setas + ENTER: responder    ESC: sair")
        if self.show_table:
            self.draw_table(surf)

    def draw_table(self, surf):
        f = self.g.fonts
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 10, 20, 238))
        surf.blit(overlay, (0, 0))
        draw_text(surf, "CÓDIGO GENÉTICO (fita codificante, em DNA)", f["l"], WHITE, (W // 2, 28), "center")
        cw, ch = 240, 118
        x0, y0 = (W - 4 * cw) // 2, 60
        for ri, b1 in enumerate("TCAG"):
            for ci, b2 in enumerate("TCAG"):
                x, y = x0 + ci * cw, y0 + ri * ch
                pygame.draw.rect(surf, (30, 38, 64), (x + 4, y + 4, cw - 8, ch - 8), border_radius=8)
                for k, b3 in enumerate("TCAG"):
                    codon = b1 + b2 + b3
                    aa = CODON_TABLE[codon]
                    col = (255, 120, 110) if aa == "*" else (YELLOW if codon == "ATG" else WHITE)
                    draw_text(surf, "%s  %s" % (codon, aa_short(aa)), f["s"], col, (x + 18, y + 12 + k * 24))
        draw_text(surf, "Linhas = 1ª base, colunas = 2ª base, dentro da caixa = 3ª base.  "
                        "Amarelo: início (ATG).  Vermelho: parada.",
                  f["xs"], (170, 180, 205), (W // 2, y0 + 4 * ch + 14), "center")
        draw_text(surf, "TAB ou ESC para fechar", f["s"], (170, 180, 205), (W // 2, H - 22), "center")

    def draw_summary(self, surf):
        f = self.g.fonts
        inner = draw_panel(surf, (160, 150, W - 320, 330), accent=BLUE)
        draw_text(surf, "RELATÓRIO DO BANCO DE DADOS", f["xl"], INK, (inner.centerx, inner.y + 20), "midtop")
        draw_text(surf, "Acertos: %d / %d" % (self.correct, len(self.qs)), f["l"], INK,
                  (inner.centerx, inner.y + 100), "midtop")
        if self.correct >= 3:
            msg = "Tradução dominada! Você sabe ler o código genético e prever o efeito das mutações."
            col = (40, 140, 70)
        else:
            msg = "São necessários pelo menos 3 acertos. Use a tabela de códons (TAB) e tente de novo."
            col = (190, 60, 50)
        draw_wrapped(surf, msg, f["m"], col, pygame.Rect(inner.x + 30, inner.y + 160, inner.w - 60, 90))
        draw_text(surf, "ENTER para voltar ao laboratório", f["s"], GRAY,
                  (inner.centerx, inner.bottom - 12), "midbottom")


# ================================================== EXPERIMENTO CONTROLADO
class ExpScene(Mini):
    icon_name = "icon_mesa"

    def __init__(self, game):
        super().__init__(game)
        st = game.state
        pend = [s for s in SCENARIOS if s["id"] not in st.exp_ok]
        self.sc = random.choice(pend) if pend else random.choice(SCENARIOS)
        self.sample = 0
        self.equip = 0
        self.altered = set()
        self.sel = 0
        self.mode = "setup"    # setup | result | question | qfeedback
        self.res = None
        self.res_altered = set()
        self.q_sel = 0
        self.q_ok = False
        self.msg = ""
        self.row_rects = []
        self.q_rects = []

    def reset_setup(self):
        self.sample = 0
        self.equip = 0
        self.altered = set()
        self.sel = 0
        self.msg = ""
        self.mode = "setup"

    # ---- ações
    def act_row(self, row, direction=1):
        if row == 0:
            self.sample = (self.sample + direction) % len(SAMPLES)
            self.g.audio.play("select")
        elif row == 1:
            self.equip = (self.equip + direction) % len(EQUIPS)
            self.g.audio.play("select")
        elif 2 <= row <= 5:
            key = EXP_VARS[row - 2][0]
            if key in self.altered:
                self.altered.discard(key)
            else:
                self.altered.add(key)
            self.g.audio.play("select")
        elif row == 6:
            self.run()

    def run(self):
        st = self.g.state
        if st.budget < st.EXP_COST:
            self.msg = "Recursos insuficientes! Peça reposição na geladeira de amostras."
            self.g.audio.play("bad")
            return
        st.budget -= st.EXP_COST
        st.stats["exp_runs"] += 1
        sid, eid = SAMPLES[self.sample][0], EQUIPS[self.equip][0]
        self.res_altered = set(self.altered)
        self.res = evaluate_experiment(sid, eid, self.res_altered, self.sc)
        status = self.res["status"]
        st.log_event("experimento", "cenario=%s;amostra=%s;equip=%s;alteradas=%s" %
                     (self.sc["id"], sid, eid, "+".join(sorted(self.res_altered)) or "nenhuma"),
                     status, status == "ok")
        self.mode = "result"
        self.msg = ""
        if status == "ok":
            self.g.audio.play("confirm")
            self.g.gain_xp(15)
        else:
            self.g.audio.play("bad")
            if status in ("sem_variavel", "confusao", "fora_da_hipotese"):
                self.g.gain_xp(3)
        if self.res["hurt"]:
            self.g.hurt(self.res["hurt"])

    def answer_question(self):
        st = self.g.state
        ok = self.q_sel == self.sc["correct"]
        self.q_ok = ok
        st.log_event("interpretacao", "cenario=%s;resp=%d" % (self.sc["id"], self.q_sel),
                     "acerto" if ok else "erro", ok)
        if ok:
            st.exp_ok.add(self.sc["id"])
            self.g.gain_xp(25)
            self.g.audio.play("ok")
            if len(st.exp_ok) >= 2 and "exp" not in st.done:
                st.done.add("exp")
                self.g.gain_xp(20)
        else:
            self.g.audio.play("bad")
            self.g.hurt(4)
        self.mode = "qfeedback"

    def after_feedback(self):
        st = self.g.state
        if self.q_ok:
            pend = [s for s in SCENARIOS if s["id"] not in st.exp_ok]
            if "exp" in st.done or not pend:
                self.close()
                return
            self.sc = random.choice(pend)
        self.reset_setup()

    # ---- entrada
    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.close()
            return
        if self.mode == "setup":
            self.handle_setup(e)
        elif self.mode == "result":
            if is_confirm(e) or is_click(e):
                if self.res["status"] == "ok":
                    self.mode = "question"
                    self.q_sel = 0
                else:
                    self.reset_setup_keep()
        elif self.mode == "question":
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.q_sel = (self.q_sel - 1) % 3
                    self.g.audio.play("select")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.q_sel = (self.q_sel + 1) % 3
                    self.g.audio.play("select")
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.answer_question()
            elif e.type == pygame.MOUSEMOTION:
                for r, i in self.q_rects:
                    if r.collidepoint(e.pos):
                        self.q_sel = i
            elif is_click(e):
                for r, i in self.q_rects:
                    if r.collidepoint(e.pos):
                        self.q_sel = i
                        self.answer_question()
                        return
        elif self.mode == "qfeedback":
            if is_confirm(e) or is_click(e):
                self.after_feedback()

    def reset_setup_keep(self):
        """Volta ao painel mantendo as escolhas (para o jogador ajustar)."""
        self.mode = "setup"
        self.msg = ""

    def handle_setup(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % 7
                self.g.audio.play("select")
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % 7
                self.g.audio.play("select")
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                if self.sel < 2:
                    self.act_row(self.sel, -1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                if self.sel < 2:
                    self.act_row(self.sel, 1)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.act_row(self.sel, 1)
        elif e.type == pygame.MOUSEMOTION:
            for r, i in self.row_rects:
                if r.collidepoint(e.pos):
                    self.sel = i
        elif is_click(e):
            for r, i in self.row_rects:
                if r.collidepoint(e.pos):
                    self.sel = i
                    self.act_row(i, -1 if (i < 2 and e.pos[0] < r.centerx) else 1)
                    return

    # ---- desenho
    def draw(self, surf):
        f = self.g.fonts
        st = self.g.state
        self.bg(surf)
        self.header(surf, "LABORATÓRIO DE EXPERIMENTAÇÃO",
                    "Recursos: %d   Custo: %d" % (st.budget, st.EXP_COST))
        inner = draw_panel(surf, (24, 100, W - 48, 62), fill=(255, 248, 225), accent=ORANGE)
        draw_wrapped(surf, self.sc["hip"], f["m"], INK, pygame.Rect(inner.x + 14, inner.y + 8, inner.w - 28, 46))
        left = pygame.Rect(24, 174, 560, 424)
        right = pygame.Rect(600, 174, W - 624, 424)
        self.row_rects = []
        self.q_rects = []
        if self.mode == "setup":
            self.draw_setup(surf, left, right)
        else:
            self.draw_outcome(surf, left, right)
        self.footer(surf, "Setas: escolher e alterar    ENTER: confirmar    ESC: sair")

    def draw_setup(self, surf, left, right):
        f = self.g.fonts
        inner = draw_panel(surf, left, accent=BLUE)
        names = ["Amostra", "Equipamento"] + [v[1] for v in EXP_VARS]
        for i in range(7):
            r = pygame.Rect(inner.x + 8, inner.y + 8 + i * 56, inner.w - 16, 50)
            self.row_rects.append((r, i))
            chosen = (i == self.sel)
            pygame.draw.rect(surf, (255, 240, 200) if chosen else (238, 240, 246), r, border_radius=8)
            if chosen:
                pygame.draw.rect(surf, ORANGE, r, 3, border_radius=8)
            if i == 6:
                ok = self.g.state.budget >= self.g.state.EXP_COST
                draw_text(surf, "EXECUTAR EXPERIMENTO", f["m"], (40, 140, 70) if ok else (190, 60, 50),
                          r.center, "center")
                continue
            draw_text(surf, names[i], f["s"], GRAY, (r.x + 12, r.centery), "midleft")
            vx = r.x + 150
            if i == 0:
                draw_text(surf, clip_text(SAMPLES[self.sample][1], f["s"], r.w - 190), f["s"], INK,
                          (vx, r.centery), "midleft")
            elif i == 1:
                draw_text(surf, clip_text(EQUIPS[self.equip][1], f["s"], r.w - 190), f["s"], INK,
                          (vx, r.centery), "midleft")
            else:
                key, _name, ctrl, alt = EXP_VARS[i - 2]
                on = key in self.altered
                txt = ("ALTERADA: " + alt) if on else ("controle: " + ctrl)
                draw_text(surf, txt, f["m"], (200, 90, 20) if on else INK, (vx, r.centery), "midleft")
                draw_check(surf, pygame.Rect(r.right - 38, r.centery - 12, 24, 24), on)
            if i < 2 and chosen:
                draw_arrows(surf, pygame.Rect(r.x + 130, r.y, r.w - 130, r.h))
        # painel de descrição
        rin = draw_panel(surf, right, fill=(236, 242, 255), accent=BLUE)
        title, body = self.describe()
        draw_text(surf, title, f["m"], INK, (rin.x + 14, rin.y + 12))
        draw_wrapped(surf, body, f["s"], INK, pygame.Rect(rin.x + 14, rin.y + 48, rin.w - 28, rin.h - 60), 6)
        if self.msg:
            draw_text(surf, self.msg, f["s"], (190, 60, 50), (rin.x + 14, rin.bottom - 10), "bottomleft")

    def describe(self):
        s = self.sel
        if s == 0:
            _id, name, desc = SAMPLES[self.sample]
            return name, desc + "\n\nA amostra certa é essencial: material inadequado ou contaminado arruína o experimento."
        if s == 1:
            _id, name, desc = EQUIPS[self.equip]
            return name, desc + "\n\nEscolha o equipamento que realmente responde à pergunta da hipótese."
        if 2 <= s <= 5:
            key, name, ctrl, alt = EXP_VARS[s - 2]
            return name, ("Grupo controle: %s\nGrupo teste: %s\n\nSó o que você marcar como ALTERADA "
                          "muda no grupo teste. Todo o resto fica igual ao controle.\n\n"
                          "Pense: qual variável a hipótese quer testar?" % (ctrl, alt))
        return "Executar", ("Custo: %d recursos.\n\nA sequência segue o método científico: hipótese, "
                            "experimento, análise e decisão. Erros custam recursos e podem "
                            "danificar o laboratório." % self.g.state.EXP_COST)

    def draw_outcome(self, surf, left, right):
        f = self.g.fonts
        status = self.res["status"]
        inner = draw_panel(surf, left, accent=GREEN if status == "ok" else ORANGE)
        if self.mode == "result":
            draw_text(surf, "RESULTADO", f["l"], INK, (inner.x + 16, inner.y + 12))
            draw_wrapped(surf, self.res["msg"], f["m"], INK,
                         pygame.Rect(inner.x + 16, inner.y + 56, inner.w - 32, 220), 6)
            if self.res["hurt"]:
                draw_text(surf, "Integridade do laboratório: -%d" % self.res["hurt"], f["m"],
                          (190, 60, 50), (inner.x + 16, inner.bottom - 70))
            draw_text(surf, "ENTER para continuar", f["s"], GRAY, (inner.right - 14, inner.bottom - 8), "bottomright")
        elif self.mode == "question":
            draw_text(surf, "Como você interpreta os dados?", f["m"], INK, (inner.x + 16, inner.y + 12))
            for i, opt in enumerate(self.sc["options"]):
                r = pygame.Rect(inner.x + 12, inner.y + 52 + i * 104, inner.w - 24, 96)
                self.q_rects.append((r, i))
                chosen = (i == self.q_sel)
                pygame.draw.rect(surf, (255, 240, 200) if chosen else (238, 240, 246), r, border_radius=8)
                if chosen:
                    pygame.draw.rect(surf, ORANGE, r, 3, border_radius=8)
                draw_wrapped(surf, opt, f["s"], INK, pygame.Rect(r.x + 12, r.y + 10, r.w - 24, r.h - 16), 4)
        else:  # qfeedback
            ok = self.q_ok
            draw_text(surf, "CORRETO!" if ok else "INTERPRETAÇÃO INCORRETA", f["l"],
                      (40, 140, 70) if ok else (190, 60, 50), (inner.x + 16, inner.y + 12))
            txt = self.sc["why"]
            if not ok:
                txt = "A interpretação certa era: %s\n\n%s\n\nIntegridade do laboratório: -4" % (
                    self.sc["options"][self.sc["correct"]], txt)
            elif "exp" in self.g.state.done:
                txt += "\n\nExperimentos concluídos! O laboratório confia em você."
            draw_wrapped(surf, txt, f["m"], INK, pygame.Rect(inner.x + 16, inner.y + 56, inner.w - 32, 260), 6)
            draw_text(surf, "ENTER para continuar", f["s"], GRAY, (inner.right - 14, inner.bottom - 8), "bottomright")
        # lado direito: gráfico
        rin = pygame.Rect(right)
        if status in ("ok", "confusao", "fora_da_hipotese"):
            draw_chart(surf, rin, [
                dict(points=growth_curve(set()), color=(120, 180, 255), label="Controle"),
                dict(points=growth_curve(self.res_altered), color=ORANGE, label="Teste"),
            ], 24, 1000, f["xs"], xlabel="horas", ylabel="células x1000/mL")
        else:
            inn = draw_panel(surf, rin, fill=(236, 236, 240), accent=GRAY)
            draw_wrapped(surf, "Sem dados: o experimento falhou antes da medição. Revise a amostra, "
                               "o equipamento e as variáveis.", f["m"], GRAY,
                         pygame.Rect(inn.x + 16, inn.y + 16, inn.w - 32, 200), 6)


# =================================================== SIMULAÇÃO EVOLUTIVA
class SimScene(Mini):
    def __init__(self, game):
        super().__init__(game)
        st = game.state
        self.params = [
            dict(key="env", label="Ambiente (cor do terreno)", values=ENV_VALUES, idx=1),
            dict(key="press", label="Pressão seletiva", values=PRESSURES, idx=1),
            dict(key="mut", label="Taxa de mutação", values=MUT_RATES, idx=3),
            dict(key="size", label="Tamanho da população", values=SIZES, idx=2),
            dict(key="res", label="Recursos disponíveis", values=RESOURCES, idx=2),
        ]
        self.sel = 0
        self.phase = 2 if "sim" in st.done else 0
        self.row_rects = []
        self.pebbles = [(random.random(), random.random(), random.random()) for _ in range(40)]
        self.reset_sim()

    def val(self, key):
        for p in self.params:
            if p["key"] == key:
                return p["values"][p["idx"]]
        return None

    def reset_sim(self):
        self.pop = Population(int(self.val("size")))
        self.hist = []
        self.record()
        self.running = False
        self.fast = False
        self.timer = 0.0
        self.hold = 0
        self.msg = ""
        self.new_positions()

    def record(self):
        s = self.pop.stats(self.val("env"), self.val("press"))
        s["opt"] = self.val("env")
        self.hist.append(s)

    def new_positions(self):
        self.pos = [(random.random(), random.random(), random.random() * 6.28)
                    for _ in range(len(self.pop.genomes))]

    def mission_text(self):
        if self.phase == 0:
            return ("Missão 1/2: adapte a população ao terreno CLARO. Deixe a média do traço "
                    "perto do ótimo (diferença <= 0,06) por 5 gerações seguidas.")
        if self.phase == 1:
            return ("Missão 2/2: o ambiente escureceu! Readapte a população ao terreno ESCURO. "
                    "Sem variação genética, a seleção natural não tem o que selecionar.")
        return "Modo livre: experimente os parâmetros e observe o que muda na evolução."

    # ---- entrada
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE:
                self.close()
            elif k in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.params)
                self.g.audio.play("select")
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.params)
                self.g.audio.play("select")
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.change(-1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.change(1)
            elif k == pygame.K_SPACE:
                self.running = not self.running
                self.g.audio.play("confirm")
            elif k in (pygame.K_n, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.step_gen()
            elif k == pygame.K_r:
                self.reset_sim()
                self.g.audio.play("select")
            elif k == pygame.K_f:
                self.fast = not self.fast
        elif is_click(e):
            for r, i in self.row_rects:
                if r.collidepoint(e.pos):
                    self.sel = i
                    self.change(-1 if e.pos[0] < r.centerx else 1)
                    return

    def change(self, d):
        p = self.params[self.sel]
        new = clamp(p["idx"] + d, 0, len(p["values"]) - 1)
        if new != p["idx"]:
            p["idx"] = new
            self.g.audio.play("select")
            self.hold = 0
            self.record_param_change()

    def record_param_change(self):
        s = self.pop.stats(self.val("env"), self.val("press"))
        s["opt"] = self.val("env")
        self.hist[-1] = s

    # ---- simulação
    def step_gen(self):
        opt, press = self.val("env"), self.val("press")
        self.pop.step(opt, press, self.val("mut"), int(self.val("size")), self.val("res"))
        self.g.state.stats["sim_gens"] += 1
        self.record()
        self.new_positions()
        s = self.hist[-1]
        in_target = (self.phase == 0 and opt <= 0.30) or (self.phase == 1 and opt >= 0.70)
        if in_target:
            self.hold = self.hold + 1 if is_adapted(s["mean"], opt, 0.06) else 0
            if self.hold >= 5:
                self.complete_phase()
                return
        else:
            self.hold = 0
        if s["var"] < 0.0015 and not is_adapted(s["mean"], opt, 0.06):
            self.msg = ("Pouca variação genética! Sem variação a seleção natural não tem o que "
                        "selecionar: aumente a taxa de mutação.")
        elif self.val("mut") >= 0.04 and not is_adapted(s["mean"], opt, 0.06):
            self.msg = "Mutação alta demais gera 'ruído': os indivíduos bem adaptados se perdem."
        elif self.phase < 2 and not in_target:
            self.msg = "Ajuste o ambiente: a missão pede terreno %s." % ("CLARO" if self.phase == 0 else "ESCURO")
        else:
            self.msg = ""

    def complete_phase(self):
        st = self.g.state
        st.log_event("simulacao",
                     "fase=%d;geracoes=%d;mut=%g;pressao=%d;tam=%d;recursos=%g" %
                     (self.phase, self.pop.generation, self.val("mut"), self.val("press"),
                      self.val("size"), self.val("res")), "adaptada", True)
        self.g.gain_xp(25)
        if self.phase == 0:
            self.phase = 1
            self.hold = 0
            self.params[0]["idx"] = 19
            self.record_param_change()
            self.msg = "MUDANÇA AMBIENTAL! O terreno escureceu. Readapte a população."
            self.g.audio.play("alert")
        else:
            self.phase = 2
            self.running = False
            st.done.add("sim")
            self.g.gain_xp(20)
            self.msg = "Missão cumprida! Pressione ESC para voltar ao laboratório."
            self.g.audio.play("unlock")

    def update(self, dt):
        self.t += dt
        if self.running:
            self.timer += dt * (4.0 if self.fast else 1.0)
            while self.timer >= 0.2:
                self.timer -= 0.2
                self.step_gen()
                if not self.running:
                    break

    # ---- desenho
    def draw(self, surf):
        f = self.g.fonts
        self.bg(surf)
        self.header(surf, "OBSERVAÇÃO DE POPULAÇÕES",
                    "Geração %d%s" % (self.pop.generation, "   [RODANDO]" if self.running else ""))
        mt = pygame.Rect(24, 96, W - 48, 40)
        draw_wrapped(surf, self.mission_text(), f["s"], (255, 236, 170), mt, 2)
        terrain = pygame.Rect(24, 142, 520, 246)
        self.draw_terrain(surf, terrain)
        self.draw_params(surf, pygame.Rect(560, 142, W - 584, 246))
        chart_series = [
            dict(points=[h["mean"] for h in self.hist], color=(110, 170, 255), label="Média do traço"),
            dict(points=[h["opt"] for h in self.hist], color=(255, 110, 100), label="Ótimo do ambiente"),
            dict(points=[min(1.0, h["var"] / 0.03125) for h in self.hist], color=(110, 220, 140), label="Variação"),
            dict(points=[h["fit"] for h in self.hist], color=(255, 190, 80), label="Aptidão"),
        ]
        draw_chart(surf, pygame.Rect(24, 398, W - 48, 186), chart_series,
                   max(60, len(self.hist) - 1), 1.0, f["xs"], xlabel="gerações")
        s = self.hist[-1]
        draw_text(surf, "Média %.2f   Ótimo %.2f   Aptidão %.2f   Variação %.3f   População %d" %
                  (s["mean"], s["opt"], s["fit"], s["var"], s["n"]),
                  f["s"], (200, 210, 235), (24, 592))
        if self.msg:
            draw_wrapped(surf, self.msg, f["s"], (255, 214, 120), pygame.Rect(24, 614, W - 48, 36), 2)
        elif self.hold > 0:
            draw_text(surf, "Adaptada! Mantenha por mais %d geração(ões)..." % max(0, 5 - self.hold),
                      f["s"], (140, 230, 160), (24, 614))
        self.footer(surf, "Setas: parâmetros   ESPAÇO: rodar/pausar   N: 1 geração   F: rápido   R: reiniciar   ESC: sair")

    def draw_terrain(self, surf, rect):
        env = self.val("env")
        ground = lerp_color((232, 220, 190), (70, 56, 44), env)
        pygame.draw.rect(surf, ground, rect, border_radius=8)
        dark = lerp_color(ground, (0, 0, 0), 0.18)
        light = lerp_color(ground, (255, 255, 255), 0.14)
        for i, (px, py, pr) in enumerate(self.pebbles):
            c = dark if pr < 0.5 else light
            pygame.draw.circle(surf, c, (int(rect.x + 8 + px * (rect.w - 16)), int(rect.y + 8 + py * (rect.h - 16))),
                               2 + int(pr * 3))
        for i, (px, py, ph) in enumerate(self.pos):
            if i >= len(self.pop.genomes):
                break
            t = Population.trait(self.pop.genomes[i])
            body = lerp_color((244, 234, 206), (44, 34, 28), t)
            x = rect.x + 14 + px * (rect.w - 28) + math.sin(self.t * 2 + ph) * 2
            y = rect.y + 14 + py * (rect.h - 28) + math.cos(self.t * 1.7 + ph) * 2
            pygame.draw.ellipse(surf, body, (int(x - 8), int(y - 5), 16, 10))
            pygame.draw.circle(surf, body, (int(x + 8), int(y - 1)), 4)
            pygame.draw.circle(surf, (250, 250, 250), (int(x + 9), int(y - 2)), 1)
        pygame.draw.rect(surf, BORDER, rect, 4, border_radius=8)
        label = "claro" if env < 0.35 else ("escuro" if env > 0.65 else "intermediário")
        draw_text(surf, "Terreno %s (ótimo %.2f)" % (label, env), self.g.fonts["xs"], WHITE,
                  (rect.x + 10, rect.bottom - 8), "bottomleft", shadow=BLACK)

    def draw_params(self, surf, rect):
        f = self.g.fonts
        inner = draw_panel(surf, rect, accent=BLUE)
        self.row_rects = []
        for i, p in enumerate(self.params):
            r = pygame.Rect(inner.x + 6, inner.y + 6 + i * 46, inner.w - 12, 42)
            self.row_rects.append((r, i))
            chosen = (i == self.sel)
            pygame.draw.rect(surf, (255, 240, 200) if chosen else (238, 240, 246), r, border_radius=6)
            if chosen:
                pygame.draw.rect(surf, ORANGE, r, 2, border_radius=6)
            v = p["values"][p["idx"]]
            draw_text(surf, p["label"], f["xs"], GRAY, (r.x + 10, r.y + 4))
            draw_text(surf, self.fmt(p["key"], v), f["s"], INK, (r.x + 10, r.y + 20))
            draw_bar(surf, pygame.Rect(r.right - 120, r.centery - 5, 108, 10),
                     p["idx"], max(1, len(p["values"]) - 1), BLUE, back=(200, 204, 214))

    @staticmethod
    def fmt(key, v):
        if key == "env":
            return "%.2f" % v
        if key == "press":
            return "%d (%s)" % (v, ["fraca", "moderada", "média", "forte", "extrema"][int(v) - 1])
        if key == "mut":
            return "%.1f%% por gene" % (v * 100)
        if key == "size":
            return "%d indivíduos" % v
        return "%d%%" % int(v * 100)


# ========================================================= TERMINAL (PC)
class PCScene(Mini):
    TABS = ["Missões", "Dados", "Computador Evolutivo"]
    MISSIONS = [
        ("Estudo", "dna", "Analisar sequências de DNA (quadro de DNA)"),
        ("Estudo", "bank", "Traduzir códons (bancada das pastas)"),
        ("Pesquisa", "exp", "Experimento com controle de variáveis (bancada dos tubos)"),
        ("Pesquisa", "sim", "Simulação evolutiva (microscópio)"),
        ("Crise", "creature", "Conter a criatura (surge ao fim da Pesquisa)"),
        ("Projeto", "final", "Construir o Computador Evolutivo (este terminal)"),
    ]

    def __init__(self, game):
        super().__init__(game)
        self.tab = 0
        self.msg = ""

    def unlocked(self):
        return "creature" in self.g.state.done

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.close()
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.tab = (self.tab - 1) % 3
                self.msg = ""
                self.g.audio.play("select")
            elif e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                self.tab = (self.tab + 1) % 3
                self.msg = ""
                self.g.audio.play("select")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.tab == 2:
                if self.unlocked() and "final" not in self.g.state.done:
                    self.g.replace_top(FinalScene(self.g))
                    self.g.audio.play("confirm")
                elif "final" in self.g.state.done:
                    self.msg = "O Computador Evolutivo já está operacional."
                else:
                    self.msg = "Bloqueado: conclua Estudo e Pesquisa (e contenha a criatura)."
                    self.g.audio.play("bad")

    def draw(self, surf):
        f = self.g.fonts
        st = self.g.state
        self.bg(surf)
        self.header(surf, "TERMINAL DO LABORATÓRIO", "Nível %d   XP %d" % (st.level, st.xp))
        big = self.g.assets.get("computador")
        if big:
            surf.blit(big, (40, 130))
        draw_text(surf, "PSE v1.0", f["m"], (170, 180, 205), (100, 330), "midtop")
        draw_text(surf, "setas: trocar aba", f["xs"], (130, 142, 172), (100, 360), "midtop")
        x = 220
        for i, name in enumerate(self.TABS):
            w = f["m"].size(name)[0] + 30
            r = pygame.Rect(x, 104, w, 40)
            inn = draw_panel(surf, r, fill=(255, 244, 205) if i == self.tab else (225, 228, 238),
                             accent=ORANGE if i == self.tab else GRAY, radius=8, width=3)
            draw_text(surf, name, f["m"], INK, inn.center, "center")
            x += w + 10
        body = pygame.Rect(220, 152, W - 244, 440)
        inner = draw_panel(surf, body, accent=BLUE)
        if self.tab == 0:
            self.draw_missions(surf, inner)
        elif self.tab == 1:
            self.draw_data(surf, inner)
        else:
            self.draw_final(surf, inner)
        self.footer(surf, "ESC: fechar terminal")

    def draw_missions(self, surf, inner):
        f = self.g.fonts
        st = self.g.state
        y = inner.y + 14
        last = None
        for phase, key, text in self.MISSIONS:
            if phase != last:
                draw_text(surf, phase.upper(), f["s"], RED, (inner.x + 16, y))
                y += 26
                last = phase
            draw_check(surf, pygame.Rect(inner.x + 24, y, 24, 24), key in st.done)
            draw_text(surf, text, f["m"], INK if key not in st.done else GRAY, (inner.x + 62, y + 12), "midleft")
            y += 34
        draw_text(surf, "Dica: o ciclo é investigação, experimentação, análise, decisão e resultado.",
                  f["xs"], GRAY, (inner.x + 16, inner.bottom - 10), "bottomleft")

    def draw_data(self, surf, inner):
        f = self.g.fonts
        st = self.g.state
        s = st.stats
        lines = [
            "Sequências analisadas: %d (acertos: %d)   Mutações encontradas: %d" % (s["dna_total"], s["dna_ok"], s["mutations"]),
            "Códons traduzidos: %d (acertos: %d)   Experimentos: %d   Gerações simuladas: %d" % (
                s["bank_total"], s["bank_ok"], s["exp_runs"], s["sim_gens"]),
        ]
        y = inner.y + 12
        for ln in lines:
            draw_text(surf, clip_text(ln, f["s"], inner.w - 28), f["s"], INK, (inner.x + 14, y))
            y += 24
        draw_text(surf, "Últimos registros (também salvos em pse_dados.csv):", f["s"], RED, (inner.x + 14, y + 6))
        y += 36
        for row in st.log[-9:][::-1]:
            ln = "%4ds  %-14s %-9s %s" % (row["tempo_s"], row["tipo"], row["resultado"], row["detalhe"])
            draw_text(surf, clip_text(ln, f["xs"], inner.w - 28), f["xs"],
                      (40, 130, 70) if row["acerto"] else (170, 70, 60), (inner.x + 14, y))
            y += 22
        if not st.log:
            draw_text(surf, "Nenhum dado registrado ainda. Faça análises e experimentos!", f["s"], GRAY,
                      (inner.x + 14, y))

    def draw_final(self, surf, inner):
        f = self.g.fonts
        st = self.g.state
        if "final" in st.done:
            txt = "O Computador Evolutivo está operacional. Missão concluída!"
        elif self.unlocked():
            txt = ("Todos os módulos estão prontos para a montagem. Pressione ENTER para iniciar a "
                   "construção do supercomputador capaz de simular a evolução.")
        else:
            falta = []
            if "dna" not in st.done:
                falta.append("análise de DNA")
            if "bank" not in st.done:
                falta.append("tradução de códons")
            if "exp" not in st.done:
                falta.append("experimento controlado")
            if "sim" not in st.done:
                falta.append("simulação evolutiva")
            if not falta:
                falta.append("conter a criatura")
            txt = "BLOQUEADO. Pendências: " + ", ".join(falta) + "."
        draw_wrapped(surf, txt, f["m"], INK, pygame.Rect(inner.x + 16, inner.y + 16, inner.w - 32, 200), 6)
        if self.msg:
            draw_text(surf, self.msg, f["s"], (190, 60, 50), (inner.x + 16, inner.bottom - 12), "bottomleft")


# =============================================== COMPUTADOR EVOLUTIVO (FINAL)
class FinalScene(Mini):
    MODULES = [
        dict(name="Módulo de Simulação", q="Qual processo cria NOVA variação genética na população?",
             opts=["Mutação", "Seleção natural", "Aumentar o tamanho da população"], correct=0,
             why="Mutações geram variantes novas. A seleção só escolhe entre o que já existe."),
        dict(name="Módulo de Seleção", q="Por que uma população se adapta ao ambiente ao longo das gerações?",
             opts=["Cada indivíduo muda o próprio DNA para se adaptar",
                   "Os mais adaptados deixam mais descendentes",
                   "O ambiente altera o DNA de forma dirigida"], correct=1,
             why="Quem tem variantes vantajosas se reproduz mais, e essas variantes ficam mais comuns."),
        dict(name="Módulo de Dados", q="Em um experimento controlado, o que fazemos com as variáveis?",
             opts=["Alteramos todas para ganhar tempo", "Alteramos apenas a variável testada",
                   "Não alteramos nenhuma"], correct=1,
             why="Com uma única variável alterada, a diferença observada pode ser atribuída a ela."),
        dict(name="Módulo de Bioinformática", q="Que recurso usamos para traduzir um códon em aminoácido?",
             opts=["A tabela do código genético", "A fita complementar", "O número de gerações"], correct=0,
             why="O código genético relaciona cada trinca (códon) a um aminoácido ou a uma parada."),
    ]

    def __init__(self, game):
        super().__init__(game)
        self.mods = []
        for m in self.MODULES:
            idx = list(range(len(m["opts"])))
            random.shuffle(idx)
            self.mods.append(dict(name=m["name"], q=m["q"], why=m["why"],
                                  opts=[m["opts"][i] for i in idx], correct=idx.index(m["correct"])))
        self.k = 0
        self.sel = 0
        self.installed = 0
        self.stage = "build"    # build | feedback | run | done
        self.fb_ok = False
        self.pop = None
        self.hist = []
        self.timer = 0.0
        self.opt_rects = []

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.stage in ("build", "feedback"):
            self.close()
            return
        if self.stage == "build":
            n = len(self.mods[self.k]["opts"])
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = (self.sel - 1) % n
                    self.g.audio.play("select")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = (self.sel + 1) % n
                    self.g.audio.play("select")
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.answer()
            elif e.type == pygame.MOUSEMOTION:
                for r, i in self.opt_rects:
                    if r.collidepoint(e.pos):
                        self.sel = i
            elif is_click(e):
                for r, i in self.opt_rects:
                    if r.collidepoint(e.pos):
                        self.sel = i
                        self.answer()
                        return
        elif self.stage == "feedback":
            if is_confirm(e) or is_click(e):
                if self.fb_ok:
                    self.k += 1
                    self.sel = 0
                    if self.k >= len(self.mods):
                        self.start_run()
                    else:
                        self.stage = "build"
                else:
                    self.stage = "build"
        elif self.stage == "done":
            if is_confirm(e) or is_click(e):
                self.g.end_game()

    def answer(self):
        m = self.mods[self.k]
        ok = self.sel == m["correct"]
        self.fb_ok = ok
        self.g.state.log_event("modulo_final", "modulo=%d;resp=%d" % (self.k, self.sel),
                               "acerto" if ok else "erro", ok)
        if ok:
            self.installed += 1
            self.g.audio.play("unlock")
            self.g.gain_xp(15)
        else:
            self.g.audio.play("bad")
            self.g.state.budget = max(0, self.g.state.budget - 10)
            self.g.hurt(5)
        self.stage = "feedback"

    def start_run(self):
        self.stage = "run"
        self.pop = Population(60)
        self.hist = []
        self.record(0)
        self.g.audio.play("alert")

    def env_at(self, gen):
        return 0.5 + 0.4 * math.sin(gen / 10.0)

    def record(self, gen):
        opt = self.env_at(gen)
        s = self.pop.stats(opt, 3)
        s["opt"] = opt
        self.hist.append(s)

    def update(self, dt):
        self.t += dt
        if self.stage == "run":
            self.timer += dt
            while self.timer >= 0.12 and self.stage == "run":
                self.timer -= 0.12
                gen = self.pop.generation
                self.pop.step(self.env_at(gen), 3, 0.015, 60, 1.0)
                self.record(self.pop.generation)
                if self.pop.generation >= 90:
                    self.stage = "done"
                    self.g.audio.play("ok")

    def draw(self, surf):
        f = self.g.fonts
        self.bg(surf)
        self.header(surf, "COMPUTADOR EVOLUTIVO", "Módulos: %d/%d" % (self.installed, len(self.mods)))
        self.opt_rects = []
        # trilho de módulos
        for i, m in enumerate(self.mods):
            r = pygame.Rect(24 + i * 256, 100, 246, 44)
            done = i < self.installed
            inn = draw_panel(surf, r, fill=(214, 244, 220) if done else (225, 228, 238),
                             accent=GREEN if done else GRAY, radius=8, width=3)
            draw_text(surf, clip_text(m["name"], f["xs"], inn.w - 10), f["xs"], INK, inn.center, "center")
        if self.stage in ("build", "feedback"):
            m = self.mods[self.k]
            inner = draw_panel(surf, (24, 160, W - 48, 90), fill=(236, 242, 255), accent=BLUE)
            draw_text(surf, "Instalar: " + m["name"], f["s"], RED, (inner.x + 14, inner.y + 8))
            draw_wrapped(surf, m["q"], f["m"], INK, pygame.Rect(inner.x + 14, inner.y + 34, inner.w - 28, 50))
            for i, opt in enumerate(m["opts"]):
                r = pygame.Rect(W // 2 - 340, 276 + i * 54, 680, 46)
                chosen = (i == self.sel)
                if self.stage == "feedback":
                    if i == m["correct"]:
                        accent, fill = GREEN, (214, 244, 220)
                    elif chosen:
                        accent, fill = RED, (250, 218, 214)
                    else:
                        accent, fill = GRAY, (236, 236, 240)
                else:
                    accent, fill = (BLUE, (255, 244, 205)) if chosen else (GRAY, (236, 236, 240))
                inn = draw_panel(surf, r, fill=fill, accent=accent, radius=8, width=3)
                draw_text(surf, opt, f["m"], INK, (inn.x + 14, inn.centery), "midleft")
                self.opt_rects.append((r, i))
            if self.stage == "feedback":
                txt = m["why"]
                if not self.fb_ok:
                    txt = "Módulo incompatível! Faíscas no gabinete. (Recursos -10, integridade -5)\n" + txt
                self.feedback_panel(surf, self.fb_ok, txt, y=450, h=150)
            self.footer(surf, "Setas + ENTER: escolher    ESC: sair")
        else:
            self.draw_run(surf)

    def draw_run(self, surf):
        f = self.g.fonts
        s = self.hist[-1]
        done = self.stage == "done"
        title = "SIMULAÇÃO CONCLUÍDA" if done else "EXECUTANDO SIMULAÇÃO EVOLUTIVA..."
        draw_text(surf, title, f["l"], (140, 230, 160) if done else WHITE, (W // 2, 176), "center")
        draw_chart(surf, pygame.Rect(24, 210, W - 48, 290), [
            dict(points=[h["mean"] for h in self.hist], color=(110, 170, 255), label="Média do traço"),
            dict(points=[h["opt"] for h in self.hist], color=(255, 110, 100), label="Ótimo do ambiente"),
            dict(points=[h["fit"] for h in self.hist], color=(255, 190, 80), label="Aptidão"),
        ], 90, 1.0, f["xs"], xlabel="gerações")
        draw_text(surf, "Geração %d/90   média %.2f   ótimo %.2f   aptidão %.2f" %
                  (self.pop.generation, s["mean"], s["opt"], s["fit"]), f["m"], (200, 210, 235), (W // 2, 522), "center")
        if done:
            draw_wrapped(surf, "O ambiente oscilou e a população o acompanhou: variação, seleção e mutação "
                               "trabalhando juntas. Sua ferramenta já pode ajudar pesquisas médicas!",
                         f["m"], (230, 236, 250), pygame.Rect(60, 552, W - 120, 70), 4)
            draw_text(surf, "ENTER para continuar", f["s"], (170, 180, 205), (W // 2, H - 20), "center")
