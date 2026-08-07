from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

# ==========================================================
# CONFIGURAÇÃO DA CHAPA
# ==========================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400

AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA

LAPIDACAO = 4


# ==========================================================
# PEÇA
# ==========================================================

@dataclass
class Peca:

    codigo: str

    largura: float

    altura: float

    pedido: str = ""

    cliente: str = ""

    pc: str = ""

    rota: str = ""

    @property
    def largura_corte(self):

        return self.largura + LAPIDACAO

    @property
    def altura_corte(self):

        return self.altura + LAPIDACAO

    @property
    def area(self):

        return (

            self.largura_corte

            *

            self.altura_corte

        )

    @property
    def distancia_minima(self):

        codigo = str(

            self.codigo

        ).upper()

        if codigo.startswith("LM"):

            return 30

        numeros = "".join(

            c

            for c in codigo

            if c.isdigit()

        )

        if numeros:

            espessura = int(

                numeros

            )

            if espessura in (

                3,

                4

            ):

                return 12

            elif espessura in (

                6,

                8

            ):

                return 20

            elif espessura >= 10:

                return 30

        return 12


# ==========================================================
# ESPAÇO LIVRE
# ==========================================================

@dataclass
class Espaco:

    x: float

    y: float

    largura: float

    altura: float

    @property
    def area(self):

        return (

            self.largura

            *

            self.altura

        )


# ==========================================================
# POSICIONAMENTO
# ==========================================================

@dataclass
class Posicionamento:

    peca: Peca

    x: float

    y: float

    largura: float

    altura: float

    girada: bool
# ==========================================================
# CHAPA
# ==========================================================

class Chapa:
    def __init__(self, largura_chapa=LARGURA_CHAPA, altura_chapa=ALTURA_CHAPA):
        self.largura = largura_chapa
        self.altura = altura_chapa
        self.pecas: List[Posicionamento] = []
        self.espacos: List[Espaco] = [
            Espaco(0, 0, self.largura, self.altura)
        ]
        # ✅ Define a área total da chapa personalizada
        self.area_total = self.largura * self.altura

    @property
    def area_utilizada(self):
        return sum(p.largura * p.altura for p in self.pecas)

    @property
    def desperdicio(self):
        return self.area_total - self.area_utilizada

    @property
    def aproveitamento(self):
        if self.area_total == 0:
            return 0
        return (self.area_utilizada / self.area_total) * 100


    # --------------------------------------------------

    @property
    def area_total(self):

        return AREA_CHAPA

    # --------------------------------------------------

    @property
    def area_utilizada(self):

        return sum(

            p.largura * p.altura

            for p in self.pecas

        )

    # --------------------------------------------------

    @property
    def desperdicio(self):

        return self.area_total - self.area_utilizada

    # --------------------------------------------------

    @property
    def aproveitamento(self):

        if self.area_total == 0:

            return 0

        return (

            self.area_utilizada

            /

            self.area_total

        ) * 100

    # --------------------------------------------------

    def cabe(

        self,

        espaco: Espaco,

        largura,

        altura,

        distancia

    ):

        if (

            largura > espaco.largura

            or

            altura > espaco.altura

        ):

            return False

        sobra_direita = (

            espaco.largura

            -

            largura

        )

        sobra_superior = (

            espaco.altura

            -

            altura

        )

        if (

            sobra_direita != 0

            and

            sobra_direita < distancia

        ):

            return False

        if (

            sobra_superior != 0

            and

            sobra_superior < distancia

        ):

            return False

        return True

    # --------------------------------------------------

    def procurar_melhor_espaco(

        self,

        peca: Peca

    ):

        melhor = None

        girada = False

        melhor_score = None

        distancia = (

            peca.distancia_minima

        )

        for espaco in self.espacos:

            for rotacionada in (

                False,

                True

            ):

                if rotacionada:

                    largura = (

                        peca.altura_corte

                    )

                    altura = (

                        peca.largura_corte

                    )

                else:

                    largura = (

                        peca.largura_corte

                    )

                    altura = (

                        peca.altura_corte

                    )

                if not self.cabe(

                    espaco,

                    largura,

                    altura,

                    distancia

                ):

                    continue

                sobra_direita = (

                    espaco.largura

                    -

                    largura

                )

                sobra_superior = (

                    espaco.altura

                    -

                    altura

                )

                score = (

                    sobra_direita * sobra_superior,

                    sobra_direita + sobra_superior,

                    espaco.area

                )

                if (

                    melhor_score is None

                    or

                    score < melhor_score

                ):

                    melhor_score = score

                    melhor = espaco

                    girada = rotacionada

        return (

            melhor,

            girada

        )
            # --------------------------------------------------

    def inserir_peca(

        self,

        peca: Peca

    ):

        espaco, girada = self.procurar_melhor_espaco(

            peca

        )

        if espaco is None:

            return False

        if girada:

            largura = peca.altura_corte

            altura = peca.largura_corte

        else:

            largura = peca.largura_corte

            altura = peca.altura_corte

        self.pecas.append(

            Posicionamento(

                peca,

                espaco.x,

                espaco.y,

                largura,

                altura,

                girada

            )

        )

        self.espacos.remove(

            espaco

        )

        self._gerar_sobras(

            espaco,

            largura,

            altura

        )

        self._limpar_espacos()

        return True

    # --------------------------------------------------

    def _gerar_sobras(

        self,

        espaco,

        largura,

        altura

    ):

        sobra_direita = (

            espaco.largura

            -

            largura

        )

        sobra_superior = (

            espaco.altura

            -

            altura

        )

        perda_vertical = (

            sobra_direita

            *

            altura

        )

        perda_horizontal = (

            sobra_superior

            *

            espaco.largura

        )

        if perda_vertical <= perda_horizontal:

            if sobra_direita > 0:

                self.espacos.append(

                    Espaco(

                        espaco.x + largura,

                        espaco.y,

                        sobra_direita,

                        altura

                    )

                )

            if sobra_superior > 0:

                self.espacos.append(

                    Espaco(

                        espaco.x,

                        espaco.y + altura,

                        espaco.largura,

                        sobra_superior

                    )

                )

        else:

            if sobra_superior > 0:

                self.espacos.append(

                    Espaco(

                        espaco.x,

                        espaco.y + altura,

                        largura,

                        sobra_superior

                    )

                )

            if sobra_direita > 0:

                self.espacos.append(

                    Espaco(

                        espaco.x + largura,

                        espaco.y,

                        sobra_direita,

                        espaco.altura

                    )

                )

    # --------------------------------------------------

    def _limpar_espacos(

        self

    ):

        novos = []

        for i, espaco1 in enumerate(

            self.espacos

        ):

            contido = False

            for j, espaco2 in enumerate(

                self.espacos

            ):

                if i == j:

                    continue

                if (

                    espaco1.x >= espaco2.x

                    and

                    espaco1.y >= espaco2.y

                    and

                    espaco1.x + espaco1.largura

                    <=

                    espaco2.x + espaco2.largura

                    and

                    espaco1.y + espaco1.altura

                    <=

                    espaco2.y + espaco2.altura

                ):

                    contido = True

                    break

            if not contido:

                novos.append(

                    espaco1

                )

        self.espacos = sorted(

            novos,

            key=lambda e: (

                e.y,

                e.x,

                e.area

            )

        )

# ==========================================================
# OTIMIZAÇÃO DE UM MATERIAL
# ==========================================================

def otimizar_material(
    codigo: str,
    pecas: List[Peca],
    largura_chapa=LARGURA_CHAPA,
    altura_chapa=ALTURA_CHAPA
):
    pecas = sorted(
        pecas,
        key=lambda p: (
            p.area,
            max(p.largura_corte, p.altura_corte)
        ),
        reverse=True
    )

    chapas: List[Chapa] = []

    for peca in pecas:
        melhor_chapa = None
        melhor_score = None

        for chapa in chapas:
            espaco, girada = chapa.procurar_melhor_espaco(peca)
            if espaco is None:
                continue

            if girada:
                largura = peca.altura_corte
                altura = peca.largura_corte
            else:
                largura = peca.largura_corte
                altura = peca.altura_corte

            sobra_direita = espaco.largura - largura
            sobra_superior = espaco.altura - altura

            menor_sobra = min(sobra_direita, sobra_superior)
            maior_sobra = max(sobra_direita, sobra_superior)

            score = (
                espaco.area - (largura * altura),
                menor_sobra,
                maior_sobra,
                espaco.area
            )

            if melhor_score is None or score < melhor_score:
                melhor_score = score
                melhor_chapa = chapa

        if melhor_chapa is None:
            # 🔧 Agora cria a chapa com largura/altura personalizadas
            melhor_chapa = Chapa(largura_chapa, altura_chapa)
            chapas.append(melhor_chapa)

        melhor_chapa.inserir_peca(peca)

    return chapas
# ==========================================================
# OTIMIZA TODOS OS MATERIAIS
# ==========================================================

def otimizar_lista(
    lista_pecas: List[Peca],
    largura_chapa=LARGURA_CHAPA,
    altura_chapa=ALTURA_CHAPA
):
    materiais: Dict[str, List[Peca]] = {}

    for peca in lista_pecas:
        materiais.setdefault(peca.codigo, []).append(peca)

    resultado = {}

    for codigo in sorted(materiais.keys()):
        # 🔧 Agora repassa largura/altura para otimizar_material
        resultado[codigo] = otimizar_material(
            codigo,
            materiais[codigo],
            largura_chapa,
            altura_chapa
        )

    return resultado
    # ==========================================================
# RESUMO
# ==========================================================

def resumo_otimizacao(resultado):
    linhas = []

    for codigo, chapas in resultado.items():
        qtd_chapas = len(chapas)

        # 🔧 Usa a área da chapa realmente criada (com largura/altura personalizadas)
        area_total = qtd_chapas * chapas[0].area_total if chapas else 0

        area_utilizada = sum(chapa.area_utilizada for chapa in chapas)
        desperdicio = area_total - area_utilizada
        aproveitamento = (area_utilizada / area_total * 100) if area_total > 0 else 0

        linhas.append({
            "Codigo": codigo,
            "Qtd Chapas": qtd_chapas,
            "Área Total": round(area_total / 1_000_000, 2),
            "Área Utilizada": round(area_utilizada / 1_000_000, 2),
            "Desperdício Total": round(desperdicio / 1_000_000, 2),
            "Aproveitamento (%)": round(aproveitamento, 2)
        })

    linhas.sort(key=lambda x: x["Codigo"])
    return linhas




   
