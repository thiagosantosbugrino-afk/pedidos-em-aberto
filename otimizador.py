from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable
import math
import random

# ==========================================================
# CONFIGURAÇÃO PADRÃO DA CHAPA
# ==========================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400
AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA

# Acréscimo usado no corte/lapidação.
LAPIDACAO = 4

# Número máximo de tentativas do otimizador por material.
# Mais tentativas = maior chance de encontrar uma solução melhor,
# porém aumenta o tempo de processamento.
MAX_TENTATIVAS = 16


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
        return float(self.largura) + LAPIDACAO

    @property
    def altura_corte(self) -> float:
        return float(self.altura) + LAPIDACAO

    @property
    def area(self) -> float:
        return self.largura_corte * self.altura_corte

    @property
    def distancia_minima(self) -> float:
        """Distância mínima entre peças conforme o código/material."""
        codigo = str(self.codigo).upper()

        if codigo.startswith("LM"):
            return 30.0

        numeros = "".join(c for c in codigo if c.isdigit())

        if numeros:
            try:
                espessura = int(numeros)
            except ValueError:
                espessura = 0

            if espessura in (3, 4):
                return 12.0
            if espessura in (6, 8):
                return 20.0
            if espessura >= 10:
                return 30.0

        return 12.0


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
        return max(0.0, self.largura) * max(0.0, self.altura)

    @property
    def direita(self) -> float:
        return self.x + self.largura

    @property
    def topo(self) -> float:
        return self.y + self.altura


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
    """
    Representa uma chapa e seus espaços livres.

    A versão V2 usa uma abordagem semelhante ao MaxRects:
    - testa diferentes posições dentro do espaço livre;
    - testa rotação;
    - escolhe o encaixe que deixa a menor sobra;
    - divide o espaço ocupado em regiões livres menores;
    - elimina espaços redundantes/contidos.
    """

    def __init__(
        self,
        largura: float = LARGURA_CHAPA,
        altura: float = ALTURA_CHAPA,
    ):
        self.largura = float(largura)
        self.altura = float(altura)
        self.pecas: List[Posicionamento] = []
        self.espacos: List[Espaco] = [
            Espaco(0.0, 0.0, self.largura, self.altura)
        ]

    @property
    def area_total(self) -> float:
        return self.largura * self.altura

    @property
    def area_utilizada(self) -> float:
        return sum(p.largura * p.altura for p in self.pecas)

    @property
    def desperdicio(self) -> float:
        return max(0.0, self.area_total - self.area_utilizada)

    @property
    def aproveitamento(self) -> float:
        if self.area_total <= 0:
            return 0.0
        return (self.area_utilizada / self.area_total) * 100.0

    def _orientacoes(self, peca: Peca):
        """Retorna as duas orientações sem duplicar quadrados."""
        normal = (peca.largura_corte, peca.altura_corte, False)
        yield normal

        if abs(peca.largura_corte - peca.altura_corte) > 1e-9:
            yield (peca.altura_corte, peca.largura_corte, True)

    def _cabe(
        self,
        espaco: Espaco,
        largura: float,
        altura: float,
        distancia: float,
    ) -> bool:
        eps = 1e-9

        if largura > espaco.largura + eps:
            return False
        if altura > espaco.altura + eps:
            return False

        sobra_direita = espaco.largura - largura
        sobra_superior = espaco.altura - altura

        # Mantém a regra industrial existente: se sobra uma faixa,
        # ela precisa comportar a distância mínima; se a peça fecha
        # exatamente o espaço, não há faixa a reservar.
        if sobra_direita > eps and sobra_direita < distancia - eps:
            return False
        if sobra_superior > eps and sobra_superior < distancia - eps:
            return False

        return True

    @staticmethod
    def _score_posicao(
        espaco: Espaco,
        largura: float,
        altura: float,
        modo: str,
        indice: int,
    ) -> Tuple:
        sobra_direita = max(0.0, espaco.largura - largura)
        sobra_superior = max(0.0, espaco.altura - altura)
        area_sobra = max(0.0, espaco.area - largura * altura)
        menor_sobra = min(sobra_direita, sobra_superior)
        maior_sobra = max(sobra_direita, sobra_superior)

        # Os modos produzem soluções diferentes para o mesmo conjunto
        # de peças. O otimizador compara todas posteriormente.
        if modo == "best_short_side":
            return (
                menor_sobra,
                maior_sobra,
                area_sobra,
                espaco.y,
                espaco.x,
                indice,
            )

        if modo == "best_long_side":
            return (
                maior_sobra,
                menor_sobra,
                area_sobra,
                espaco.y,
                espaco.x,
                indice,
            )

        if modo == "best_area":
            return (
                area_sobra,
                menor_sobra,
                maior_sobra,
                espaco.y,
                espaco.x,
                indice,
            )

        if modo == "bottom_left":
            return (
                espaco.y,
                espaco.x,
                menor_sobra,
                maior_sobra,
                area_sobra,
                indice,
            )

        if modo == "compact":
            return (
                menor_sobra + maior_sobra,
                menor_sobra,
                area_sobra,
                espaco.y,
                espaco.x,
                indice,
            )

        return (
            area_sobra,
            menor_sobra,
            maior_sobra,
            espaco.y,
            espaco.x,
            indice,
        )

    def procurar_melhor_espaco(
        self,
        peca: Peca,
        modo: str = "best_area",
    ) -> Tuple[Optional[Espaco], bool]:
        """Procura o melhor espaço e orientação para uma peça."""
        melhor: Optional[Espaco] = None
        melhor_girada = False
        melhor_score = None
        distancia = peca.distancia_minima

        for indice, espaco in enumerate(self.espacos):
            for largura, altura, girada in self._orientacoes(peca):
                if not self._cabe(
                    espaco,
                    largura,
                    altura,
                    distancia,
                ):
                    continue

                score = self._score_posicao(
                    espaco,
                    largura,
                    altura,
                    modo,
                    indice,
                )

                if melhor_score is None or score < melhor_score:
                    melhor_score = score
                    melhor = espaco
                    melhor_girada = girada

        return melhor, melhor_girada

    def inserir_peca(
        self,
        peca: Peca,
        modo: str = "best_area",
        espaco: Optional[Espaco] = None,
        girada: Optional[bool] = None,
    ) -> bool:
        if espaco is None or girada is None:
            espaco, girada = self.procurar_melhor_espaco(
                peca,
                modo=modo,
            )

        if espaco is None or girada is None:
            return False

        if espaco not in self.espacos:
            return False

        if girada:
            largura = peca.altura_corte
            altura = peca.largura_corte
        else:
            largura = peca.largura_corte
            altura = peca.altura_corte

        if not self._cabe(
            espaco,
            largura,
            altura,
            peca.distancia_minima,
        ):
            return False

        posicionamento = Posicionamento(
            peca=peca,
            x=espaco.x,
            y=espaco.y,
            largura=largura,
            altura=altura,
            girada=girada,
        )

        self.pecas.append(posicionamento)
        self.espacos.remove(espaco)

        self._dividir_espacos(espaco, largura, altura)
        self._limpar_espacos()

        return True

    def _dividir_espacos(
        self,
        espaco: Espaco,
        largura: float,
        altura: float,
    ) -> None:
        """
        Divide o espaço usado em quatro possíveis regiões.
        Como a peça é colocada no canto inferior esquerdo do espaço,
        na prática duas regiões são as principais; as quatro direções
        tornam o algoritmo mais robusto para as diferentes estratégias.
        """
        eps = 1e-9

        sobra_direita = espaco.largura - largura
        sobra_superior = espaco.altura - altura

        if sobra_direita > eps:
            self.espacos.append(
                Espaco(
                    espaco.x + largura,
                    espaco.y,
                    sobra_direita,
                    espaco.altura,
                )
            )

        if sobra_superior > eps:
            self.espacos.append(
                Espaco(
                    espaco.x,
                    espaco.y + altura,
                    largura,
                    sobra_superior,
                )
            )

    def _limpar_espacos(self) -> None:
        """Remove espaços vazios, inválidos e contidos em outros."""
        eps = 1e-9

        validos = [
            e
            for e in self.espacos
            if e.largura > eps and e.altura > eps
        ]

        novos: List[Espaco] = []

        for i, espaco1 in enumerate(validos):
            contido = False

            for j, espaco2 in enumerate(validos):
                if i == j:
                    continue

                if (
                    espaco1.x >= espaco2.x - eps
                    and espaco1.y >= espaco2.y - eps
                    and espaco1.direita <= espaco2.direita + eps
                    and espaco1.topo <= espaco2.topo + eps
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
                e.area,
            ),
        )


# ==========================================================
# ORDENAÇÕES / ESTRATÉGIAS
# ==========================================================

def _ordens_base(pecas: List[Peca]):
    """Gera diferentes ordens determinísticas para multi-start."""
    estrategias: List[Tuple[str, List[Peca]]] = []

    estrategias.append((
        "area",
        sorted(
            pecas,
            key=lambda p: (
                p.area,
                max(p.largura_corte, p.altura_corte),
                min(p.largura_corte, p.altura_corte),
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "maior_lado",
        sorted(
            pecas,
            key=lambda p: (
                max(p.largura_corte, p.altura_corte),
                p.area,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "menor_lado",
        sorted(
            pecas,
            key=lambda p: (
                min(p.largura_corte, p.altura_corte),
                p.area,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "perimetro",
        sorted(
            pecas,
            key=lambda p: (
                2 * (p.largura_corte + p.altura_corte),
                p.area,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "alongadas",
        sorted(
            pecas,
            key=lambda p: (
                max(p.largura_corte, p.altura_corte)
                / max(1.0, min(p.largura_corte, p.altura_corte)),
                p.area,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "largura",
        sorted(
            pecas,
            key=lambda p: (
                p.largura_corte,
                p.altura_corte,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "altura",
        sorted(
            pecas,
            key=lambda p: (
                p.altura_corte,
                p.largura_corte,
            ),
            reverse=True,
        ),
    ))

    estrategias.append((
        "quadrados",
        sorted(
            pecas,
            key=lambda p: (
                -abs(p.largura_corte - p.altura_corte),
                p.area,
            ),
            reverse=True,
        ),
    ))

    return estrategias


# ==========================================================
# AVALIAÇÃO DE UMA SOLUÇÃO
# ==========================================================

def _avaliar_chapas(chapas: List[Chapa]) -> Tuple:
    """
    Critério principal:
      1) menos chapas;
      2) maior aproveitamento global;
      3) menor desperdício global;
      4) melhor utilização da última chapa.
    """
    if not chapas:
        return (0, 0.0, 0.0, 0.0)

    qtd = len(chapas)
    area_total = sum(c.area_total for c in chapas)
    area_utilizada = sum(c.area_utilizada for c in chapas)
    desperdicio = max(0.0, area_total - area_utilizada)

    aproveitamento = (
        area_utilizada / area_total
        if area_total > 0
        else 0.0
    )

    ultima = chapas[-1]
    ultima_aproveitamento = (
        ultima.area_utilizada / ultima.area_total
        if ultima.area_total > 0
        else 0.0
    )

    # Menor é melhor para o primeiro item; portanto usamos negativos
    # nos indicadores que queremos maximizar.
    return (
        qtd,
        -aproveitamento,
        desperdicio,
        -ultima_aproveitamento,
    )


# ==========================================================
# OTIMIZAÇÃO DE UM MATERIAL — V2
# ==========================================================

def otimizar_material(
    codigo: str,
    pecas: List[Peca],
    largura_chapa: float = LARGURA_CHAPA,
    altura_chapa: float = ALTURA_CHAPA,
    tentativas: int = MAX_TENTATIVAS,
) -> List[Chapa]:
    """
    Otimizador híbrido/multi-start.

    Em vez de executar uma única heurística, ele monta várias soluções
    com ordens diferentes e estratégias de encaixe e retorna a melhor.
    """
    if not pecas:
        return []

    # Remove dimensões impossíveis antes de iniciar.
    pecas_validas = [
        p for p in pecas
        if p.largura_corte > 0
        and p.altura_corte > 0
    ]

    if not pecas_validas:
        return []

    estrategias_espaco = [
        "best_area",
        "best_short_side",
        "best_long_side",
        "bottom_left",
        "compact",
    ]

    ordens = _ordens_base(pecas_validas)

    # Aumenta a diversidade com tentativas pseudoaleatórias,
    # mantendo resultado reproduzível para o mesmo conjunto de peças.
    rng = random.Random(
        20260811 + sum(ord(c) for c in str(codigo))
    )

    quantidade_aleatoria = max(
        0,
        min(
            8,
            tentativas - len(ordens),
        ),
    )

    for i in range(quantidade_aleatoria):
        lista = list(pecas_validas)
        rng.shuffle(lista)
        ordens.append((f"random_{i}", lista))

    melhor_chapas: Optional[List[Chapa]] = None
    melhor_score = None

    for indice, (_, ordem) in enumerate(
        ordens[:max(1, tentativas)]
    ):
        modo = estrategias_espaco[
            indice % len(estrategias_espaco)
        ]

        chapas: List[Chapa] = []

        sucesso = True

        for peca in ordem:
            melhor_chapa = None
            melhor_encaixe = None
            melhor_girada = False
            melhor_local_score = None

            # Procura o melhor espaço considerando TODAS as chapas já abertas.
            for chapa_index, chapa in enumerate(chapas):
                espaco, girada = chapa.procurar_melhor_espaco(
                    peca,
                    modo=modo,
                )

                if espaco is None:
                    continue

                if girada:
                    largura = peca.altura_corte
                    altura = peca.largura_corte
                else:
                    largura = peca.largura_corte
                    altura = peca.altura_corte

                sobra_direita = max(
                    0.0,
                    espaco.largura - largura,
                )
                sobra_superior = max(
                    0.0,
                    espaco.altura - altura,
                )
                menor_sobra = min(
                    sobra_direita,
                    sobra_superior,
                )
                maior_sobra = max(
                    sobra_direita,
                    sobra_superior,
                )
                area_sobra = max(
                    0.0,
                    espaco.area - largura * altura,
                )

                # Favorece o fechamento de espaços pequenos e, depois,
                # a compactação da chapa.
                if modo == "best_short_side":
                    local_score = (
                        menor_sobra,
                        maior_sobra,
                        area_sobra,
                        chapa_index,
                    )
                elif modo == "best_long_side":
                    local_score = (
                        maior_sobra,
                        menor_sobra,
                        area_sobra,
                        chapa_index,
                    )
                elif modo == "bottom_left":
                    local_score = (
                        espaco.y,
                        espaco.x,
                        menor_sobra,
                        area_sobra,
                        chapa_index,
                    )
                elif modo == "compact":
                    local_score = (
                        menor_sobra + maior_sobra,
                        menor_sobra,
                        area_sobra,
                        chapa_index,
                    )
                else:
                    local_score = (
                        area_sobra,
                        menor_sobra,
                        maior_sobra,
                        chapa_index,
                    )

                if (
                    melhor_local_score is None
                    or local_score < melhor_local_score
                ):
                    melhor_local_score = local_score
                    melhor_chapa = chapa
                    melhor_encaixe = espaco
                    melhor_girada = girada

            if melhor_chapa is None:
                # Abre uma nova chapa.
                nova_chapa = Chapa(
                    largura=largura_chapa,
                    altura=altura_chapa,
                )

                if not nova_chapa.inserir_peca(
                    peca,
                    modo=modo,
                ):
                    sucesso = False
                    break

                chapas.append(nova_chapa)
            else:
                # Reutiliza exatamente o espaço que foi escolhido na
                # comparação entre todas as chapas.
                if not melhor_chapa.inserir_peca(
                    peca,
                    espaco=melhor_encaixe,
                    girada=melhor_girada,
                ):
                    sucesso = False
                    break

        if not sucesso:
            continue

        score = _avaliar_chapas(chapas)

        if melhor_score is None or score < melhor_score:
            melhor_score = score
            melhor_chapas = chapas

    return melhor_chapas or []


# ==========================================================
# OTIMIZA TODOS OS MATERIAIS
# ==========================================================

def otimizar_lista(
    lista_pecas: List[Peca],
    configuracao_chapas: Dict = None,
):
    """Otimiza cada material separadamente."""
    materiais: Dict[str, List[Peca]] = {}

    for peca in lista_pecas:
        materiais.setdefault(
            str(peca.codigo),
            [],
        ).append(peca)

    resultado = {}

    for codigo in sorted(materiais.keys()):
        largura_chapa = float(LARGURA_CHAPA)
        altura_chapa = float(ALTURA_CHAPA)

        if configuracao_chapas:
            dados_chapa = configuracao_chapas.get(
                str(codigo)
            )

            if isinstance(dados_chapa, dict):
                try:
                    largura_chapa = float(
                        dados_chapa.get(
                            "largura",
                            largura_chapa,
                        )
                    )
                    altura_chapa = float(
                        dados_chapa.get(
                            "altura",
                            altura_chapa,
                        )
                    )
                except (ValueError, TypeError):
                    largura_chapa = float(LARGURA_CHAPA)
                    altura_chapa = float(ALTURA_CHAPA)

        # Reduz tentativas para listas muito grandes para manter o app responsivo.
        qtd_pecas = len(materiais[codigo])
        if qtd_pecas >= 500:
            tentativas = 8
        elif qtd_pecas >= 250:
            tentativas = 10
        else:
            tentativas = MAX_TENTATIVAS

        resultado[codigo] = otimizar_material(
            codigo,
            materiais[codigo],
            largura_chapa,
            altura_chapa,
            tentativas=tentativas,
        )

    return resultado


# ==========================================================
# RESUMO
# ==========================================================

def resumo_otimizacao(resultado):
    linhas = []

    for codigo, chapas in resultado.items():
        qtd_chapas = len(chapas)

        area_total = sum(
            chapa.largura * chapa.altura
            for chapa in chapas
        )

        area_utilizada = sum(
            chapa.area_utilizada
            for chapa in chapas
        )

        desperdicio = max(
            0.0,
            area_total - area_utilizada,
        )

        aproveitamento = (
            (area_utilizada / area_total) * 100.0
            if area_total > 0
            else 0.0
        )

        linhas.append({
            "Codigo": codigo,
            "Qtd Chapas": qtd_chapas,
            "Área Total": round(
                area_total / 1_000_000,
                2,
            ),
            "Área Utilizada": round(
                area_utilizada / 1_000_000,
                2,
            ),
            "Desperdício Total": round(
                desperdicio / 1_000_000,
                2,
            ),
            "Aproveitamento (%)": round(
                aproveitamento,
                2,
            ),
        })

    linhas.sort(
        key=lambda x: str(x["Codigo"])
    )

    return linhas
