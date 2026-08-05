from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ==========================================================
# CONFIGURAÇÃO DA CHAPA
# ==========================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400

AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA

# Sobras menores que isso são descartadas
MIN_SOBRA = 80


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
    def area(self):

        return self.largura * self.altura

    @property
    def distancia_minima(self):

        codigo = str(self.codigo).upper()

        if codigo.startswith("LM"):
            return 30

        numeros = "".join(c for c in codigo if c.isdigit())

        if numeros:

            espessura = int(numeros)

            if espessura in (3, 4):
                return 12

            elif espessura in (6, 8):
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

        return self.largura * self.altura


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

    def __init__(self):

        self.largura = LARGURA_CHAPA

        self.altura = ALTURA_CHAPA

        self.pecas: List[Posicionamento] = []

        self.espacos: List[Espaco] = [

            Espaco(
                0,
                0,
                self.largura,
                self.altura
            )

        ]

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

            / self.area_total

        ) * 100

    # --------------------------------------------------

    def cabe(

        self,

        espaco: Espaco,

        largura,

        altura

    ):

        return (

            largura <= espaco.largura

            and

            altura <= espaco.altura

        )
          # --------------------------------------------------
    # PROCURA O MELHOR ESPAÇO (BEST FIT)
    # --------------------------------------------------

    def procurar_melhor_espaco(self, peca: Peca):

        melhor = None
        menor_sobra = None
        girada = False

        for espaco in self.espacos:

            # -----------------------------
            # posição normal
            # -----------------------------

            if self.cabe(
                espaco,
                peca.largura,
                peca.altura
            ):

                sobra = (
                    espaco.area
                    -
                    peca.area
                )

                if (
                    menor_sobra is None
                    or
                    sobra < menor_sobra
                ):

                    melhor = espaco
                    menor_sobra = sobra
                    girada = False

            # -----------------------------
            # posição girada
            # -----------------------------

            if self.cabe(
                espaco,
                peca.altura,
                peca.largura
            ):

                sobra = (
                    espaco.area
                    -
                    peca.area
                )

                if (
                    menor_sobra is None
                    or
                    sobra < menor_sobra
                ):

                    melhor = espaco
                    menor_sobra = sobra
                    girada = True

        return melhor, girada

    # --------------------------------------------------
    # INSERE A PEÇA
    # --------------------------------------------------

    def inserir_peca(self, peca: Peca):

        espaco, girada = self.procurar_melhor_espaco(peca)

        if espaco is None:

            return False

        if girada:

            largura = peca.altura
            altura = peca.largura

        else:

            largura = peca.largura
            altura = peca.altura

        self.pecas.append(

            Posicionamento(

                peca=peca,

                x=espaco.x,

                y=espaco.y,

                largura=largura,

                altura=altura,

                girada=girada

            )

        )

        self.espacos.remove(espaco)

        self._gerar_sobras(
            espaco,
            largura,
            altura
        )

        self._limpar_espacos()

        return True

    # --------------------------------------------------
    # CORTE GUILHOTINADO
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

        sobra_inferior = (

            espaco.altura
            -
            altura

        )

        # -----------------------------
        # sobra da direita
        # -----------------------------

        if sobra_direita >= MIN_SOBRA:

            self.espacos.append(

                Espaco(

                    x=espaco.x + largura,

                    y=espaco.y,

                    largura=sobra_direita,

                    altura=altura

                )

            )

        # -----------------------------
        # sobra inferior
        # -----------------------------

        if sobra_inferior >= MIN_SOBRA:

            self.espacos.append(

                Espaco(

                    x=espaco.x,

                    y=espaco.y + altura,

                    largura=espaco.largura,

                    altura=sobra_inferior

                )

            )

    # --------------------------------------------------
    # REMOVE SOBRAS CONTIDAS
    # --------------------------------------------------

    def _limpar_espacos(self):

        novos = []

        for i, espaco1 in enumerate(self.espacos):

            contido = False

            for j, espaco2 in enumerate(self.espacos):

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

                novos.append(espaco1)

        self.espacos = novos

        self.espacos.sort(

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

    pecas: List[Peca]

):

    # -----------------------------------------
    # Best Fit Decreasing
    # -----------------------------------------

    pecas = sorted(

        pecas,

        key=lambda p: (

            p.area,

            max(
                p.largura,
                p.altura
            )

        ),

        reverse=True

    )

    chapas: List[Chapa] = []

    for peca in pecas:

        melhor_chapa = None

        menor_desperdicio = None

        # tenta encaixar em alguma chapa existente

        for chapa in chapas:

            espaco, girada = chapa.procurar_melhor_espaco(peca)

            if espaco is None:

                continue

            desperdicio = espaco.area - peca.area

            if (

                menor_desperdicio is None

                or

                desperdicio < menor_desperdicio

            ):

                menor_desperdicio = desperdicio

                melhor_chapa = chapa

        if melhor_chapa is None:

            melhor_chapa = Chapa()

            chapas.append(

                melhor_chapa

            )

        melhor_chapa.inserir_peca(

            peca

        )

    return chapas


# ==========================================================
# OTIMIZA TODOS OS MATERIAIS
# ==========================================================

def otimizar_lista(

    lista_pecas: List[Peca]

):

    materiais: Dict[str, List[Peca]] = {}

    for peca in lista_pecas:

        materiais.setdefault(

            peca.codigo,

            []

        ).append(

            peca

        )

    resultado = {}

    for codigo, pecas in materiais.items():

        resultado[codigo] = (

            otimizar_material(

                codigo,

                pecas

            )

        )

    return resultado


# ==========================================================
# RESUMO
# ==========================================================

def resumo_otimizacao(

    resultado

):

    linhas = []

    for codigo, chapas in resultado.items():

        area_total = sum(

            chapa.area_total

            for chapa in chapas

        )

        area_utilizada = sum(

            chapa.area_utilizada

            for chapa in chapas

        )

        desperdicio = (

            area_total

            -

            area_utilizada

        )

        aproveitamento = (

            (

                area_utilizada

                /

                area_total

            )

            * 100

            if area_total

            else 0

        )

        linhas.append(

            {

                "Codigo": codigo,

                "Qtd Chapas": len(

                    chapas

                ),

                "Área Total": round(

                    area_total / 1_000_000,

                    2

                ),

                "Área Utilizada": round(

                    area_utilizada / 1_000_000,

                    2

                ),

                "Desperdício Total": round(

                    desperdicio / 1_000_000,

                    2

                ),

                "Aproveitamento (%)": round(

                    aproveitamento,

                    2

                )

            }

        )

    linhas.sort(

        key=lambda x: x["Codigo"]

    )

    return linhas
      
