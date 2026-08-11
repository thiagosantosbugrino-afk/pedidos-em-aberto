from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random


# ==========================================================
# CONFIGURAÇÃO DA CHAPA
# ==========================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400
AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA

# Acréscimo atualmente utilizado pelo sistema para lapidação.
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
    def largura_corte(self) -> float:
        return self.largura + LAPIDACAO

    @property
    def altura_corte(self) -> float:
        return self.altura + LAPIDACAO

    @property
    def area(self) -> float:
        return self.largura_corte * self.altura_corte

    @property
    def distancia_minima(self) -> float:
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
            if espessura in (6, 8):
                return 20
            if espessura >= 10:
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
    def area(self) -> float:
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
# CHAPA - MAXRECTS
# ==========================================================

class Chapa:
    """
    Implementação de MaxRects para peças retangulares.

    A diferença importante em relação ao algoritmo anterior é que
    os retângulos livres são mantidos como uma lista de espaços
    candidatos e, ao inserir uma peça, todos os espaços que
    intersectam a peça são efetivamente divididos e depois
    podados. Isso reduz sobreposição de espaços livres e melhora
    bastante a qualidade do nesting.
    """

    EPS = 1e-7

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
                0.0,
                0.0,
                self.largura,
                self.altura
            )
        ]

    @property
    def area_total(self) -> float:
        return self.largura * self.altura

    @property
    def area_utilizada(self) -> float:
        return sum(
            p.largura * p.altura
            for p in self.pecas
        )

    @property
    def desperdicio(self) -> float:
        return self.area_total - self.area_utilizada

    @property
    def aproveitamento(self) -> float:
        if self.area_total <= 0:
            return 0.0
        return (
            self.area_utilizada
            /
            self.area_total
        ) * 100.0

    # ------------------------------------------------------
    # GEOMETRIA
    # ------------------------------------------------------

    @staticmethod
    def _intersecta(
        a: Espaco,
        x: float,
        y: float,
        largura: float,
        altura: float
    ) -> bool:
        return not (
            x + largura <= a.x + Chapa.EPS
            or
            x >= a.x + a.largura - Chapa.EPS
            or
            y + altura <= a.y + Chapa.EPS
            or
            y >= a.y + a.altura - Chapa.EPS
        )

    @staticmethod
    def _contido(
        pequeno: Espaco,
        grande: Espaco
    ) -> bool:
        return (
            pequeno.x >= grande.x - Chapa.EPS
            and
            pequeno.y >= grande.y - Chapa.EPS
            and
            pequeno.x + pequeno.largura
            <= grande.x + grande.largura + Chapa.EPS
            and
            pequeno.y + pequeno.altura
            <= grande.y + grande.altura + Chapa.EPS
        )

    # ------------------------------------------------------
    # CANDIDATOS DE POSIÇÃO
    # ------------------------------------------------------

    def _candidatos(
        self,
        peca: Peca
    ):
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

        if (
            abs(
                peca.largura_corte
                -
                peca.altura_corte
            ) < self.EPS
        ):
            orientacoes = orientacoes[:1]

        candidatos = []

        for espaco in self.espacos:
            for girada, largura, altura in orientacoes:

                if largura > espaco.largura + self.EPS:
                    continue

                if altura > espaco.altura + self.EPS:
                    continue

                sobra_largura = (
                    espaco.largura - largura
                )
                sobra_altura = (
                    espaco.altura - altura
                )

                # A peça é posicionada no canto inferior
                # esquerdo do retângulo livre.
                candidatos.append(
                    (
                        espaco,
                        girada,
                        largura,
                        altura,
                        sobra_largura,
                        sobra_altura
                    )
                )

        return candidatos

    def procurar_melhor_espaco(
        self,
        peca: Peca,
        estrategia: str = "bssf"
    ):
        candidatos = self._candidatos(peca)

        if not candidatos:
            return None, False

        melhor = None
        melhor_score = None

        for (
            espaco,
            girada,
            largura,
            altura,
            sobra_largura,
            sobra_altura
        ) in candidatos:

            area_sobra = (
                espaco.area
                -
                largura * altura
            )

            menor_sobra = min(
                sobra_largura,
                sobra_altura
            )

            maior_sobra = max(
                sobra_largura,
                sobra_altura
            )

            # As estratégias são diferentes funções de
            # desempate; todas usam o mesmo conjunto de
            # posições geometricamente válidas.
            if estrategia == "bssf":
                score = (
                    menor_sobra,
                    maior_sobra,
                    area_sobra,
                    espaco.y,
                    espaco.x
                )

            elif estrategia == "bl":
                score = (
                    espaco.y,
                    espaco.x,
                    menor_sobra,
                    area_sobra
                )

            elif estrategia == "baf":
                score = (
                    area_sobra,
                    menor_sobra,
                    maior_sobra,
                    espaco.y,
                    espaco.x
                )

            elif estrategia == "bsl":
                score = (
                    maior_sobra,
                    menor_sobra,
                    area_sobra,
                    espaco.y,
                    espaco.x
                )

            elif estrategia == "contact":
                contato = 0.0

                if abs(espaco.x) < self.EPS:
                    contato += altura
                if abs(espaco.y) < self.EPS:
                    contato += largura
                if abs(
                    espaco.x
                    +
                    largura
                    -
                    self.largura
                ) < self.EPS:
                    contato += altura
                if abs(
                    espaco.y
                    +
                    altura
                    -
                    self.altura
                ) < self.EPS:
                    contato += largura

                score = (
                    -contato,
                    area_sobra,
                    menor_sobra,
                    espaco.y,
                    espaco.x
                )

            else:
                score = (
                    menor_sobra,
                    maior_sobra,
                    area_sobra,
                    espaco.y,
                    espaco.x
                )

            if (
                melhor_score is None
                or score < melhor_score
            ):
                melhor_score = score
                melhor = (
                    espaco,
                    girada,
                    largura,
                    altura
                )

        if melhor is None:
            return None, False

        return melhor[0], melhor[1]

    # ------------------------------------------------------
    # INSERÇÃO
    # ------------------------------------------------------

    def inserir_peca(
        self,
        peca: Peca,
        estrategia: str = "bssf"
    ) -> bool:

        encontrado = None
        encontrado_score = None

        candidatos = self._candidatos(peca)

        for (
            espaco,
            girada,
            largura,
            altura,
            sobra_largura,
            sobra_altura
        ) in candidatos:

            area_sobra = (
                espaco.area
                -
                largura * altura
            )

            menor_sobra = min(
                sobra_largura,
                sobra_altura
            )

            maior_sobra = max(
                sobra_largura,
                sobra_altura
            )

            if estrategia == "bssf":
                score = (
                    menor_sobra,
                    maior_sobra,
                    area_sobra,
                    espaco.y,
                    espaco.x
                )

            elif estrategia == "bl":
                score = (
                    espaco.y,
                    espaco.x,
                    menor_sobra,
                    area_sobra
                )

            elif estrategia == "baf":
                score = (
                    area_sobra,
                    menor_sobra,
                    maior_sobra,
                    espaco.y,
                    espaco.x
                )

            elif estrategia == "bsl":
                score = (
                    maior_sobra,
                    menor_sobra,
                    area_sobra,
                    espaco.y,
                    espaco.x
                )

            else:
                contato = 0.0

                if abs(espaco.x) < self.EPS:
                    contato += altura
                if abs(espaco.y) < self.EPS:
                    contato += largura
                if abs(
                    espaco.x
                    +
                    largura
                    -
                    self.largura
                ) < self.EPS:
                    contato += altura
                if abs(
                    espaco.y
                    +
                    altura
                    -
                    self.altura
                ) < self.EPS:
                    contato += largura

                score = (
                    -contato,
                    area_sobra,
                    menor_sobra,
                    espaco.y,
                    espaco.x
                )

            if (
                encontrado_score is None
                or score < encontrado_score
            ):
                encontrado_score = score
                encontrado = (
                    espaco,
                    girada,
                    largura,
                    altura
                )

        if encontrado is None:
            return False

        espaco, girada, largura, altura = encontrado

        x = espaco.x
        y = espaco.y

        self._dividir_espacos(
            x,
            y,
            largura,
            altura
        )

        self.pecas.append(
            Posicionamento(
                peca=peca,
                x=x,
                y=y,
                largura=largura,
                altura=altura,
                girada=girada
            )
        )

        self._podar_espacos()

        return True

    # ------------------------------------------------------
    # MAXRECTS: DIVIDE TODOS OS RETÂNGULOS INTERSECTADOS
    # ------------------------------------------------------

    def _dividir_espacos(
        self,
        x: float,
        y: float,
        largura: float,
        altura: float
    ):

        novos = []

        for espaco in self.espacos:

            if not self._intersecta(
                espaco,
                x,
                y,
                largura,
                altura
            ):
                novos.append(espaco)
                continue

            # Esquerda
            if x > espaco.x + self.EPS:
                novos.append(
                    Espaco(
                        espaco.x,
                        espaco.y,
                        x - espaco.x,
                        espaco.altura
                    )
                )

            # Direita
            direita = (
                espaco.x
                +
                espaco.largura
                -
                (
                    x + largura
                )
            )

            if direita > self.EPS:
                novos.append(
                    Espaco(
                        x + largura,
                        espaco.y,
                        direita,
                        espaco.altura
                    )
                )

            # Abaixo
            if y > espaco.y + self.EPS:
                novos.append(
                    Espaco(
                        espaco.x,
                        espaco.y,
                        espaco.largura,
                        y - espaco.y
                    )
                )

            # Acima
            acima = (
                espaco.y
                +
                espaco.altura
                -
                (
                    y + altura
                )
            )

            if acima > self.EPS:
                novos.append(
                    Espaco(
                        espaco.x,
                        y + altura,
                        espaco.largura,
                        acima
                    )
                )

        self.espacos = novos

    # ------------------------------------------------------
    # PODA DE RETÂNGULOS LIVRES
    # ------------------------------------------------------

    def _podar_espacos(self):

        filtrados = []

        for i, atual in enumerate(self.espacos):

            if (
                atual.largura <= self.EPS
                or
                atual.altura <= self.EPS
            ):
                continue

            contido = False

            for j, outro in enumerate(self.espacos):

                if i == j:
                    continue

                if self._contido(
                    atual,
                    outro
                ):
                    contido = True
                    break

            if not contido:
                filtrados.append(atual)

        # Remove duplicações quase idênticas.
        unicos = []
        vistos = set()

        for espaco in filtrados:
            chave = (
                round(espaco.x, 5),
                round(espaco.y, 5),
                round(espaco.largura, 5),
                round(espaco.altura, 5)
            )

            if chave in vistos:
                continue

            vistos.add(chave)
            unicos.append(espaco)

        self.espacos = sorted(
            unicos,
            key=lambda e: (
                e.y,
                e.x,
                e.area
            )
        )


# ==========================================================
# ORDENAÇÃO
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

    elif estrategia == "lado_maior":
        chave = lambda p: (
            max(
                p.largura_corte,
                p.altura_corte
            ),
            p.area
        )

    elif estrategia == "lado_menor":
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

    elif estrategia == "alongamento":
        chave = lambda p: (
            max(
                p.largura_corte,
                p.altura_corte
            )
            /
            max(
                1.0,
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

    elif estrategia == "area_compacta":
        chave = lambda p: (
            p.area,
            -abs(
                p.largura_corte
                -
                p.altura_corte
            )
        )

    else:
        chave = lambda p: p.area

    return sorted(
        pecas,
        key=chave,
        reverse=True
    )


# ==========================================================
# VERIFICAÇÃO DE DIMENSÃO
# ==========================================================

def _peca_cabe_em_chapa(
    peca: Peca,
    largura_chapa: float,
    altura_chapa: float
) -> bool:

    w = peca.largura_corte
    h = peca.altura_corte

    return (
        (
            w <= largura_chapa + 1e-7
            and
            h <= altura_chapa + 1e-7
        )
        or
        (
            h <= largura_chapa + 1e-7
            and
            w <= altura_chapa + 1e-7
        )
    )


# ==========================================================
# MÉTRICAS
# ==========================================================

def _metricas(
    chapas: List[Chapa]
):

    if not chapas:
        return {
            "qtd_chapas": 0,
            "area_total": 0.0,
            "area_utilizada": 0.0,
            "desperdicio": 0.0,
            "aproveitamento": 0.0
        }

    area_total = sum(
        c.area_total
        for c in chapas
    )

    area_utilizada = sum(
        c.area_utilizada
        for c in chapas
    )

    desperdicio = (
        area_total
        -
        area_utilizada
    )

    aproveitamento = (
        area_utilizada
        /
        area_total
        *
        100
        if area_total > 0
        else 0
    )

    return {
        "qtd_chapas": len(chapas),
        "area_total": area_total,
        "area_utilizada": area_utilizada,
        "desperdicio": desperdicio,
        "aproveitamento": aproveitamento
    }


# ==========================================================
# CHAVE DE COMPARAÇÃO
# ==========================================================

def _chave_solucao(
    chapas: List[Chapa]
):
    """
    Objetivo industrial atual:

    1. minimizar desperdício absoluto;
    2. maximizar aproveitamento;
    3. minimizar número de chapas.

    Não há retalhos nesta versão.
    """

    m = _metricas(chapas)

    return (
        round(m["desperdicio"], 5),
        -round(m["aproveitamento"], 5),
        m["qtd_chapas"]
    )


# ==========================================================
# UMA TENTATIVA
# ==========================================================

def _otimizar_tentativa(
    pecas: List[Peca],
    largura_chapa: float,
    altura_chapa: float,
    ordem: str,
    estrategia: str,
    seed: int = 0
) -> List[Chapa]:

    ordenadas = _ordenar_pecas(
        pecas,
        ordem
    )

    if seed:
        rng = random.Random(seed)

        # Pequena perturbação somente em empates.
        grupos = []
        atual = []

        for p in ordenadas:

            if not atual:
                atual.append(p)
                continue

            anterior = atual[-1]

            if abs(
                anterior.area - p.area
            ) < 0.0001:
                atual.append(p)
            else:
                grupos.append(atual)
                atual = [p]

        if atual:
            grupos.append(atual)

        ordenadas = []

        for grupo in grupos:
            rng.shuffle(grupo)
            ordenadas.extend(grupo)

    chapas: List[Chapa] = []

    for peca in ordenadas:

        melhor_chapa = None
        melhor_score = None

        for chapa in chapas:

            candidatos = chapa._candidatos(
                peca
            )

            if not candidatos:
                continue

            # Avalia a inserção sem alterar a chapa.
            for (
                espaco,
                girada,
                largura,
                altura,
                sobra_largura,
                sobra_altura
            ) in candidatos:

                sobra_area = (
                    espaco.area
                    -
                    largura * altura
                )

                score = (
                    sobra_area,
                    min(
                        sobra_largura,
                        sobra_altura
                    ),
                    max(
                        sobra_largura,
                        sobra_altura
                    ),
                    len(chapa.pecas),
                    espaco.y,
                    espaco.x
                )

                if (
                    melhor_score is None
                    or score < melhor_score
                ):
                    melhor_score = score
                    melhor_chapa = chapa

        if melhor_chapa is None:

            nova = Chapa(
                largura_chapa,
                altura_chapa
            )

            if not nova.inserir_peca(
                peca,
                estrategia
            ):
                # A peça não cabe nem em uma chapa
                # vazia. Ela é incompatível com a
                # configuração de chapa.
                continue

            chapas.append(nova)

        else:

            if not melhor_chapa.inserir_peca(
                peca,
                estrategia
            ):
                # Proteção: se a escolha mudou por
                # tolerância numérica, tenta abrir uma
                # nova chapa em vez de perder a peça.
                nova = Chapa(
                    largura_chapa,
                    altura_chapa
                )

                if nova.inserir_peca(
                    peca,
                    estrategia
                ):
                    chapas.append(nova)

    return chapas


# ==========================================================
# MELHORIA LOCAL
# ==========================================================

def _melhorar_solucao(
    chapas: List[Chapa],
    largura_chapa: float,
    altura_chapa: float,
    estrategia: str,
    limite_passos: int = 4
) -> List[Chapa]:
    """
    Tenta remover a última chapa e redistribuir suas peças
    nas demais. Se conseguir sem piorar o objetivo, mantém
    a melhoria.

    É uma busca local conservadora: não desmonta uma solução
    inteira e não arrisca perder peças.
    """

    melhor = chapas

    for _ in range(limite_passos):

        if len(melhor) <= 1:
            break

        base = melhor[:-1]
        ultima = melhor[-1]

        pecas = [
            pos.peca
            for pos in ultima.pecas
        ]

        if not pecas:
            break

        # Reconstrói cópias das chapas-base.
        reconstruidas = []

        for chapa in base:
            nova = Chapa(
                chapa.largura,
                chapa.altura
            )

            ok = True

            for pos in chapa.pecas:

                if not nova.inserir_peca(
                    pos.peca,
                    estrategia
                ):
                    ok = False
                    break

            if not ok:
                reconstruidas = []
                break

            reconstruidas.append(nova)

        if not reconstruidas:
            break

        # Peças maiores primeiro para aumentar a
        # chance de recolocar tudo.
        pecas.sort(
            key=lambda p: p.area,
            reverse=True
        )

        sucesso = True

        for peca in pecas:

            melhor_chapa = None
            melhor_score = None

            for chapa in reconstruidas:

                for (
                    espaco,
                    girada,
                    largura,
                    altura,
                    sobra_largura,
                    sobra_altura
                ) in chapa._candidatos(
                    peca
                ):

                    score = (
                        espaco.area
                        -
                        largura * altura,
                        min(
                            sobra_largura,
                            sobra_altura
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

            if melhor_chapa is None:
                sucesso = False
                break

            if not melhor_chapa.inserir_peca(
                peca,
                estrategia
            ):
                sucesso = False
                break

        if not sucesso:
            break

        nova_chave = _chave_solucao(
            reconstruidas
        )

        velha_chave = _chave_solucao(
            melhor
        )

        if nova_chave < velha_chave:
            melhor = reconstruidas
        else:
            break

    return melhor


# ==========================================================
# OTIMIZA UM MATERIAL
# ==========================================================

def otimizar_material(
    codigo: str,
    pecas: List[Peca],
    largura_chapa: float = LARGURA_CHAPA,
    altura_chapa: float = ALTURA_CHAPA
):

    if not pecas:
        return []

    # Remove somente peças fisicamente impossíveis.
    # As peças válidas continuam obrigatoriamente na
    # otimização.
    pecas_validas = [
        p
        for p in pecas
        if _peca_cabe_em_chapa(
            p,
            largura_chapa,
            altura_chapa
        )
    ]

    if not pecas_validas:
        return []

    ordens = [
        "area",
        "lado_maior",
        "lado_menor",
        "perimetro",
        "alongamento",
        "largura",
        "altura",
        "area_compacta"
    ]

    estrategias = [
        "bssf",
        "baf",
        "bsl",
        "bl",
        "contact"
    ]

    melhor = None
    melhor_chave = None

    # Multi-start controlado.
    for ordem in ordens:

        for estrategia in estrategias:

            tentativas = 2

            for tentativa in range(tentativas):

                chapas = _otimizar_tentativa(
                    pecas_validas,
                    largura_chapa,
                    altura_chapa,
                    ordem,
                    estrategia,
                    seed=(
                        tentativa
                        +
                        len(pecas_validas) * 17
                    )
                )

                # Só considera solução completa.
                colocadas = sum(
                    len(c.pecas)
                    for c in chapas
                )

                if colocadas != len(
                    pecas_validas
                ):
                    continue

                chapas = _melhorar_solucao(
                    chapas,
                    largura_chapa,
                    altura_chapa,
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
                    melhor = chapas

    # Fallback robusto: se nenhuma estratégia anterior
    # encontrou solução completa, usa uma construção simples
    # que continua colocando todas as peças possíveis.
    if melhor is None:

        chapas = []

        for peca in sorted(
            pecas_validas,
            key=lambda p: p.area,
            reverse=True
        ):

            inserida = False

            for chapa in chapas:

                if chapa.inserir_peca(
                    peca,
                    "bssf"
                ):
                    inserida = True
                    break

            if not inserida:

                nova = Chapa(
                    largura_chapa,
                    altura_chapa
                )

                if nova.inserir_peca(
                    peca,
                    "bssf"
                ):
                    chapas.append(nova)

        if (
            sum(
                len(c.pecas)
                for c in chapas
            )
            ==
            len(pecas_validas)
        ):
            melhor = chapas
        else:
            melhor = chapas

    return melhor


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
