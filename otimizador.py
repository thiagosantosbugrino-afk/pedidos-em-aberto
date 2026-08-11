from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import math
import random


# ==========================================================
# CONFIGURAÇÃO DA CHAPA
# ==========================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400
AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA

# Acréscimo de lapidação já utilizado pelo sistema.
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
        return self.largura_corte * self.altura_corte

    @property
    def distancia_minima(self):
        codigo = str(self.codigo).upper()

        if codigo.startswith("LM"):
            return 30

        numeros = "".join(
            c for c in codigo
            if c.isdigit()
        )

        if numeros:
            try:
                espessura = int(numeros)
            except ValueError:
                espessura = 0

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

    def __init__(
        self,
        largura: float = LARGURA_CHAPA,
        altura: float = ALTURA_CHAPA
    ):

        self.largura = float(largura)
        self.altura = float(altura)

        self.pecas: List[Posicionamento] = []

        self.espacos: List[Espaco] = [
            Espaco(
                0,
                0,
                self.largura,
                self.altura
            )
        ]

    @property
    def area_total(self):
        return self.largura * self.altura

    @property
    def area_utilizada(self):
        return sum(
            p.largura * p.altura
            for p in self.pecas
        )

    @property
    def desperdicio(self):
        return self.area_total - self.area_utilizada

    @property
    def aproveitamento(self):
        if self.area_total <= 0:
            return 0

        return (
            self.area_utilizada / self.area_total
        ) * 100

    # ------------------------------------------------------
    # VALIDAÇÃO DO ESPAÇO
    # ------------------------------------------------------

    def cabe(
        self,
        espaco: Espaco,
        largura: float,
        altura: float,
        distancia: float
    ):

        if largura > espaco.largura + 1e-9:
            return False

        if altura > espaco.altura + 1e-9:
            return False

        sobra_direita = espaco.largura - largura
        sobra_superior = espaco.altura - altura

        # A distância mínima é necessária somente quando
        # existe uma sobra real. Tolerância numérica evita
        # rejeitar encaixes por diferenças de ponto flutuante.
        tol = 1e-7

        if (
            sobra_direita > tol
            and sobra_direita < distancia - tol
        ):
            return False

        if (
            sobra_superior > tol
            and sobra_superior < distancia - tol
        ):
            return False

        return True

    # ------------------------------------------------------
    # MELHOR POSIÇÃO
    # ------------------------------------------------------

    def procurar_melhor_espaco(
        self,
        peca: Peca,
        estrategia: str = "best_area"
    ):

        melhor = None
        melhor_girada = False
        melhor_score = None

        distancia = peca.distancia_minima

        orientacoes = [
            (
                False,
                peca.largura_corte,
                peca.altura_corte
            ),
            (
                True,
                peca.altura_corte,
                peca.largura_corte
            )
        ]

        # Remove duplicação quando a peça é quadrada.
        if (
            abs(
                peca.largura_corte
                -
                peca.altura_corte
            ) < 1e-9
        ):
            orientacoes = orientacoes[:1]

        for espaco in self.espacos:

            for girada, largura, altura in orientacoes:

                if not self.cabe(
                    espaco,
                    largura,
                    altura,
                    distancia
                ):
                    continue

                sobra_direita = (
                    espaco.largura - largura
                )

                sobra_superior = (
                    espaco.altura - altura
                )

                sobra_area = (
                    espaco.area
                    -
                    largura * altura
                )

                menor_sobra = min(
                    sobra_direita,
                    sobra_superior
                )

                maior_sobra = max(
                    sobra_direita,
                    sobra_superior
                )

                # Estratégias diferentes geram candidatos
                # diferentes. Todas continuam obedecendo
                # às mesmas regras geométricas.
                if estrategia == "best_area":
                    score = (
                        sobra_area,
                        menor_sobra,
                        maior_sobra,
                        espaco.y,
                        espaco.x
                    )

                elif estrategia == "best_short_side":
                    score = (
                        menor_sobra,
                        sobra_area,
                        maior_sobra,
                        espaco.y,
                        espaco.x
                    )

                elif estrategia == "best_long_side":
                    score = (
                        maior_sobra,
                        menor_sobra,
                        sobra_area,
                        espaco.y,
                        espaco.x
                    )

                elif estrategia == "bottom_left":
                    score = (
                        espaco.y,
                        espaco.x,
                        sobra_area,
                        menor_sobra
                    )

                elif estrategia == "best_fit":
                    # Prioriza preencher ao máximo uma das
                    # dimensões sem sacrificar o encaixe.
                    score = (
                        min(
                            sobra_direita,
                            sobra_superior
                        ),
                        abs(
                            sobra_direita
                            -
                            sobra_superior
                        ),
                        sobra_area,
                        espaco.y,
                        espaco.x
                    )

                else:
                    score = (
                        sobra_area,
                        menor_sobra,
                        maior_sobra,
                        espaco.y,
                        espaco.x
                    )

                if (
                    melhor_score is None
                    or score < melhor_score
                ):
                    melhor_score = score
                    melhor = espaco
                    melhor_girada = girada

        return melhor, melhor_girada

    # ------------------------------------------------------
    # INSERE PEÇA
    # ------------------------------------------------------

    def inserir_peca(
        self,
        peca: Peca,
        estrategia: str = "best_area"
    ):

        espaco, girada = (
            self.procurar_melhor_espaco(
                peca,
                estrategia
            )
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

    # ------------------------------------------------------
    # GERAÇÃO DE SOBRAS
    # ------------------------------------------------------

    def _gerar_sobras(
        self,
        espaco,
        largura,
        altura
    ):

        sobra_direita = (
            espaco.largura - largura
        )

        sobra_superior = (
            espaco.altura - altura
        )

        if sobra_direita <= 0 and sobra_superior <= 0:
            return

        perda_vertical = (
            max(0, sobra_direita)
            *
            max(0, altura)
        )

        perda_horizontal = (
            max(0, sobra_superior)
            *
            max(0, espaco.largura)
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

    # ------------------------------------------------------
    # LIMPEZA DE ESPAÇOS CONTIDOS
    # ------------------------------------------------------

    def _limpar_espacos(self):

        novos = []

        for i, espaco1 in enumerate(self.espacos):

            if (
                espaco1.largura <= 0
                or espaco1.altura <= 0
            ):
                continue

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

        self.espacos = sorted(
            novos,
            key=lambda e: (
                e.y,
                e.x,
                e.area
            )
        )


# ==========================================================
# ORDENAÇÃO DAS PEÇAS
# ==========================================================

def _ordenar_pecas(
    pecas: List[Peca],
    estrategia: str
) -> List[Peca]:

    if estrategia == "area":
        chave = lambda p: (
            p.area,
            max(
                p.largura_corte,
                p.altura_corte
            ),
            min(
                p.largura_corte,
                p.altura_corte
            )
        )

    elif estrategia == "maior_lado":
        chave = lambda p: (
            max(
                p.largura_corte,
                p.altura_corte
            ),
            p.area
        )

    elif estrategia == "menor_lado":
        chave = lambda p: (
            min(
                p.largura_corte,
                p.altura_corte
            ),
            p.area
        )

    elif estrategia == "perimetro":
        chave = lambda p: (
            2 * (
                p.largura_corte
                +
                p.altura_corte
            ),
            p.area
        )

    elif estrategia == "alongadas":
        chave = lambda p: (
            max(
                p.largura_corte,
                p.altura_corte
            )
            /
            max(
                1,
                min(
                    p.largura_corte,
                    p.altura_corte
                )
            ),
            p.area
        )

    elif estrategia == "largura":
        chave = lambda p: (
            p.largura_corte,
            p.area
        )

    elif estrategia == "altura":
        chave = lambda p: (
            p.altura_corte,
            p.area
        )

    else:
        chave = lambda p: p.area

    return sorted(
        pecas,
        key=chave,
        reverse=True
    )


# ==========================================================
# AVALIAÇÃO DA SOLUÇÃO
# ==========================================================

def _avaliar_chapas(
    chapas: List[Chapa]
):

    if not chapas:
        return (
            0,
            0.0,
            0.0
        )

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
        *
        100
        if area_total > 0
        else 0
    )

    return (
        len(chapas),
        desperdicio,
        aproveitamento
    )


# ==========================================================
# CHAVE DA SOLUÇÃO
# ==========================================================

def _chave_solucao(
    chapas: List[Chapa]
):
    """
    Critério principal:
    1) menor desperdício absoluto;
    2) maior aproveitamento;
    3) menor quantidade de chapas.

    Assim evitamos escolher uma solução que economize
    uma chapa mas desperdice muito mais material.
    """

    qtd, desperdicio, aproveitamento = (
        _avaliar_chapas(chapas)
    )

    return (
        round(desperdicio, 6),
        -round(aproveitamento, 6),
        qtd
    )


# ==========================================================
# OTIMIZAÇÃO DE UMA TENTATIVA
# ==========================================================

def _otimizar_tentativa(
    pecas: List[Peca],
    largura_chapa: float,
    altura_chapa: float,
    ordem: str,
    estrategia_espaco: str
):

    ordenadas = _ordenar_pecas(
        pecas,
        ordem
    )

    chapas: List[Chapa] = []

    for peca in ordenadas:

        melhor_chapa = None
        melhor_posicao = None
        melhor_score = None

        for chapa in chapas:

            espaco, girada = (
                chapa.procurar_melhor_espaco(
                    peca,
                    estrategia_espaco
                )
            )

            if espaco is None:
                continue

            if girada:
                largura = peca.altura_corte
                altura = peca.largura_corte
            else:
                largura = peca.largura_corte
                altura = peca.altura_corte

            sobra_direita = (
                espaco.largura - largura
            )

            sobra_superior = (
                espaco.altura - altura
            )

            sobra_area = (
                espaco.area
                -
                largura * altura
            )

            # Preferimos espaços que deixam menor
            # sobra residual, mas sem forçar uma
            # única regra de encaixe.
            score = (
                sobra_area,
                min(
                    sobra_direita,
                    sobra_superior
                ),
                max(
                    sobra_direita,
                    sobra_superior
                ),
                espaco.y,
                espaco.x
            )

            if (
                melhor_score is None
                or score < melhor_score
            ):
                melhor_score = score
                melhor_chapa = chapa
                melhor_posicao = (
                    espaco,
                    girada
                )

        if melhor_chapa is None:

            nova = Chapa(
                largura=largura_chapa,
                altura=altura_chapa
            )

            inseriu = nova.inserir_peca(
                peca,
                estrategia_espaco
            )

            # Nunca ignora uma peça silenciosamente.
            if inseriu:
                chapas.append(nova)

        else:

            melhor_chapa.inserir_peca(
                peca,
                estrategia_espaco
            )

    return chapas


# ==========================================================
# VALIDAÇÃO DAS PEÇAS
# ==========================================================

def _peca_cabe_em_chapa(
    peca: Peca,
    largura_chapa: float,
    altura_chapa: float
):

    w = peca.largura_corte
    h = peca.altura_corte

    normal = (
        w <= largura_chapa
        and
        h <= altura_chapa
    )

    girada = (
        h <= largura_chapa
        and
        w <= altura_chapa
    )

    return normal or girada


# ==========================================================
# OTIMIZAÇÃO DE UM MATERIAL
# ==========================================================

def otimizar_material(
    codigo: str,
    pecas: List[Peca],
    largura_chapa: float = LARGURA_CHAPA,
    altura_chapa: float = ALTURA_CHAPA
):

    if not pecas:
        return []

    # Mantém todas as peças válidas.
    pecas_validas = [
        p
        for p in pecas
        if _peca_cabe_em_chapa(
            p,
            largura_chapa,
            altura_chapa
        )
    ]

    # Se houver peça que não cabe nem girando,
    # ela não pode ser colocada em uma chapa.
    # O sistema continua otimizando as demais, sem
    # interromper os outros materiais.
    if not pecas_validas:
        return []

    ordens = [
        "area",
        "maior_lado",
        "menor_lado",
        "perimetro",
        "alongadas",
        "largura",
        "altura"
    ]

    estrategias = [
        "best_area",
        "best_short_side",
        "best_long_side",
        "bottom_left",
        "best_fit"
    ]

    melhor_chapas = None
    melhor_chave = None

    # Executa várias combinações, mas sempre usando
    # a mesma geometria e as mesmas regras de corte.
    for ordem in ordens:

        for estrategia in estrategias:

            chapas = _otimizar_tentativa(
                pecas_validas,
                largura_chapa,
                altura_chapa,
                ordem,
                estrategia
            )

            chave = _chave_solucao(
                chapas
            )

            if (
                melhor_chave is None
                or chave < melhor_chave
            ):
                melhor_chave = chave
                melhor_chapas = chapas

    # Pequenas perturbações determinísticas adicionais.
    # Não mudam as dimensões; apenas testam ordens diferentes.
    for semente in range(5):

        embaralhadas = list(
            pecas_validas
        )

        random.Random(
            semente
        ).shuffle(
            embaralhadas
        )

        chapas = _otimizar_tentativa(
            embaralhadas,
            largura_chapa,
            altura_chapa,
            "area",
            "best_fit"
        )

        chave = _chave_solucao(
            chapas
        )

        if (
            melhor_chave is None
            or chave < melhor_chave
        ):
            melhor_chave = chave
            melhor_chapas = chapas

    return (
        melhor_chapas
        if melhor_chapas is not None
        else []
    )


# ==========================================================
# OTIMIZA TODOS OS MATERIAIS
# ==========================================================

def otimizar_lista(
    lista_pecas: List[Peca],
    configuracao_chapas: Dict = None
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

    for codigo in sorted(
        materiais.keys()
    ):

        largura_chapa = LARGURA_CHAPA
        altura_chapa = ALTURA_CHAPA

        if configuracao_chapas:

            dados_chapa = (
                configuracao_chapas.get(
                    str(codigo)
                )
            )

            if isinstance(
                dados_chapa,
                dict
            ):

                try:

                    largura_chapa = float(
                        dados_chapa.get(
                            "largura",
                            largura_chapa
                        )
                    )

                    altura_chapa = float(
                        dados_chapa.get(
                            "altura",
                            altura_chapa
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    largura_chapa = (
                        LARGURA_CHAPA
                    )

                    altura_chapa = (
                        ALTURA_CHAPA
                    )

        resultado[codigo] = (
            otimizar_material(
                codigo,
                materiais[codigo],
                largura_chapa,
                altura_chapa
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

        qtd_chapas = len(
            chapas
        )

        area_total = sum(
            chapa.largura
            *
            chapa.altura
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
            *
            100
            if area_total > 0
            else 0
        )

        linhas.append(
            {
                "Codigo": codigo,

                "Qtd Chapas": qtd_chapas,

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
