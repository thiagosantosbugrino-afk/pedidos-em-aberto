from dataclasses import dataclass
from typing import List


# ======================================================
# CONFIGURAÇÃO DA CHAPA
# ======================================================

LARGURA_CHAPA = 3210
ALTURA_CHAPA = 2400


# ======================================================
# ESTRUTURAS
# ======================================================

@dataclass
class Peca:

    codigo: str

    largura: float

    altura: float

    pedido: str = ""

    cliente: str = ""

    pc: str = ""

    rota: str = ""


@dataclass
class EspacoLivre:

    x: float

    y: float

    largura: float

    altura: float


@dataclass
class Posicionamento:

    peca: Peca

    x: float

    y: float

    girada: bool


# ======================================================
# CHAPA
# ======================================================

class Chapa:

    def __init__(self):

        self.largura = LARGURA_CHAPA

        self.altura = ALTURA_CHAPA

        self.pecas: List[Posicionamento] = []

        self.espacos: List[EspacoLivre] = [

            EspacoLivre(

                0,

                0,

                self.largura,

                self.altura

            )

        ]

    # --------------------------------------------------

    def area_total(self):

        return self.largura * self.altura

    # --------------------------------------------------

    def area_utilizada(self):

        total = 0

        for item in self.pecas:

            if item.girada:

                total += (

                    item.peca.altura

                    *

                    item.peca.largura

                )

            else:

                total += (

                    item.peca.largura

                    *

                    item.peca.altura

                )

        return total

    # --------------------------------------------------

    def aproveitamento(self):

        return (

            self.area_utilizada()

            /

            self.area_total()

        ) * 100
      # ======================================================
# FUNÇÕES DA CHAPA
# ======================================================

    def cabe_no_espaco(

        self,

        espaco,

        largura,

        altura

    ):

        return (

            largura <= espaco.largura

            and

            altura <= espaco.altura

        )

    # --------------------------------------------------

    def procurar_melhor_espaco(

        self,

        largura,

        altura

    ):

        melhor = None

        menor_sobra = None

        girada = False

        for espaco in self.espacos:

            # posição normal

            if self.cabe_no_espaco(

                espaco,

                largura,

                altura

            ):

                sobra = (

                    espaco.largura

                    *

                    espaco.altura

                ) - (

                    largura

                    *

                    altura

                )

                if (

                    menor_sobra is None

                    or

                    sobra < menor_sobra

                ):

                    melhor = espaco

                    menor_sobra = sobra

                    girada = False

            # posição girada

            if self.cabe_no_espaco(

                espaco,

                altura,

                largura

            ):

                sobra = (

                    espaco.largura

                    *

                    espaco.altura

                ) - (

                    largura

                    *

                    altura

                )

                if (

                    menor_sobra is None

                    or

                    sobra < menor_sobra

                ):

                    melhor = espaco

                    menor_sobra = sobra

                    girada = True

        return (

            melhor,

            girada

        )
          # --------------------------------------------------

    def inserir_peca(

        self,

        peca

    ):

        espaco, girada = (

            self.procurar_melhor_espaco(

                peca.largura,

                peca.altura

            )

        )

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

                peca,

                espaco.x,

                espaco.y,

                girada

            )

        )

        self.espacos.remove(

            espaco

        )

        sobra_direita = (

            espaco.largura

            -

            largura

        )

        sobra_baixo = (

            espaco.altura

            -

            altura

        )

        if sobra_direita > 0:

            self.espacos.append(

                EspacoLivre(

                    espaco.x + largura,

                    espaco.y,

                    sobra_direita,

                    altura

                )

            )

                if sobra_baixo > 0:

            self.espacos.append(

                EspacoLivre(

                    espaco.x,

                    espaco.y + altura,

                    espaco.largura,

                    sobra_baixo

                )

            )

        self.limpar_espacos()

        return True
          # --------------------------------------------------

    def limpar_espacos(

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

        self.espacos = novos
      # ======================================================
# OTIMIZAÇÃO DE UM MATERIAL
# ======================================================

def otimizar_material(

    codigo,

    pecas

):

    # Ordena da maior para a menor
    pecas = sorted(

        pecas,

        key=lambda p: (

            p.largura *

            p.altura

        ),

        reverse=True

    )

    chapas = []

    for peca in pecas:

        colocada = False

        for chapa in chapas:

            if chapa.inserir_peca(

                peca

            ):

                colocada = True

                break

        if not colocada:

            nova = Chapa()

            nova.inserir_peca(

                peca

            )

            chapas.append(

                nova

            )

    return chapas
  # ======================================================
# OTIMIZA TODOS OS MATERIAIS
# ======================================================

def otimizar_lista(

    lista_pecas

):

    materiais = {}

    for peca in lista_pecas:

        materiais.setdefault(

            peca.codigo,

            []

        ).append(

            peca

        )

    resultado = {}

    for codigo in materiais:

        resultado[codigo] = (

            otimizar_material(

                codigo,

                materiais[codigo]

            )

        )

    return resultado
  # ======================================================
# RESUMO
# ======================================================

def resumo_otimizacao(

    resultado

):

    linhas = []

    for codigo, chapas in resultado.items():

        aproveitamento = 0

        area = 0

        utilizadas = 0

        for chapa in chapas:

            utilizadas += chapa.area_utilizada()

            area += chapa.area_total()

            aproveitamento += (

                chapa.aproveitamento()

            )

        linhas.append(

            {

                "Codigo": codigo,

                "Qtd Chapas": len(

                    chapas

                ),

                "Área Utilizada": utilizadas,

                "Área Total": area,

                "Aproveitamento (%)":

                    round(

                        utilizadas

                        /

                        area

                        *

                        100,

                        2

                    )

                    if area

                    else 0

            }

        )

    return linhas
