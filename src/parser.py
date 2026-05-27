"""
Parser Chart (Earley) — construye árboles de derivación

Recibe la lista de tokens producida por el DFA (src.lexer) y la CFG definida
en src.grammar, y devuelve uno o más árboles de derivación.

¿Por qué Earley y no CYK?
    CYK exige que la gramática esté en Forma Normal de Chomsky (todas las
    producciones de la forma A → BC ó A → a). Nuestra gramática tiene
    producciones como  Comando → FV FN FP  y  FN → ARTICULO ADJETIVO SUSTANTIVO,
    de longitud 3. Earley acepta cualquier CFG sin reescribirla, así que la
    gramática del COMMIT 3 se usa tal cual.

Algoritmo (resumen):
    Un "ítem" Earley es una producción con un punto en alguna posición del RHS
    y un índice de origen i:
            [A → α • β, i]
    El parser construye un "chart" con n+1 columnas (n = #tokens) aplicando
    tres operaciones hasta el punto fijo:

      PREDICT   si el ítem es  [A → α • B β, i]  y B es no terminal,
                añadir  [B → • γ, j]  en la columna j actual,
                para cada producción B → γ.

      SCAN      si el ítem es  [A → α • a β, i]  y a es terminal y
                token[j].tipo == a, añadir  [A → α a • β, i]  en la
                columna j+1.

      COMPLETE  si el ítem es  [B → γ •, k]  (completo) en la columna j,
                para cada ítem  [A → α • B β, i]  en la columna k,
                añadir  [A → α B • β, i]  en la columna j.

    La entrada es aceptada si alguna columna final contiene un ítem
    [S → α •, 0]. Cada ítem guarda referencias a los ítems/tokens que lo
    "completaron", lo que permite reconstruir el árbol.
"""

from dataclasses import dataclass, field
from typing import Union

from src.grammar import GRAMATICA, Gramatica, Produccion
from src.lexer import Token


@dataclass
class NodoArbol:
    """Nodo del árbol de derivación.

    - Nodos internos: simbolo ∈ V (no terminales) ó simbolo ∈ T (terminales),
      con hijos.
    - Hojas: simbolo = lexema concreto del token, token != None, sin hijos.
    """
    simbolo: str
    hijos: list["NodoArbol"] = field(default_factory=list)
    token: Token | None = None

    @property
    def es_hoja(self) -> bool:
        return self.token is not None and not self.hijos


Hijo = Union["Item", Token]


@dataclass
class Item:
    produccion: Produccion
    punto: int          # posición del punto dentro de produccion.rhs
    origen: int         # columna del chart donde nació este ítem
    hijos: tuple = field(default_factory=tuple)

    @property
    def completo(self) -> bool:
        return self.punto >= len(self.produccion.rhs)

    @property
    def siguiente(self) -> str | None:
        if self.completo:
            return None
        return self.produccion.rhs[self.punto]

    def clave(self) -> tuple:
        """Identidad del estado Earley, ignorando los backpointers."""
        return (self.produccion, self.punto, self.origen)

    def __repr__(self) -> str:
        rhs = list(self.produccion.rhs)
        rhs.insert(self.punto, "•")
        return f"[{self.origen}] {self.produccion.lhs} → {' '.join(rhs)}"


def parsear(tokens: list[Token], gram: Gramatica = GRAMATICA) -> list[NodoArbol]:
    """Parsea la lista de tokens y devuelve todos los árboles de derivación.

    Lista vacía → la entrada no pertenece al lenguaje generado por la CFG.
    """
    if not tokens:
        return []

    n = len(tokens)
    chart: list[list[Item]] = [[] for _ in range(n + 1)]
    visto: list[dict[tuple, Item]] = [dict() for _ in range(n + 1)]

    def añadir(col: int, item: Item) -> None:
        # Deduplicamos por clave (produccion, punto, origen). Para gramáticas
        # ambiguas esto descarta derivaciones alternativas; nuestra gramática
        # del juego es de hecho no ambigua para los comandos válidos.
        if item.clave() in visto[col]:
            return
        visto[col][item.clave()] = item
        chart[col].append(item)

    # Inicialización: S → • α  por cada producción de S, en la columna 0.
    for p in gram.producciones_de(gram.S):
        añadir(0, Item(p, 0, 0))

    # Bucle principal: cada columna se procesa hasta el punto fijo.
    for i in range(n + 1):
        j = 0
        while j < len(chart[i]):
            item = chart[i][j]
            j += 1

            if item.completo:
                # COMPLETE
                # Snapshot porque podemos añadir a la misma columna (origen==i)
                for cand in list(chart[item.origen]):
                    if cand.siguiente == item.produccion.lhs:
                        añadir(i, Item(
                            cand.produccion,
                            cand.punto + 1,
                            cand.origen,
                            cand.hijos + (item,),
                        ))
                continue

            siguiente = item.siguiente
            if gram.es_no_terminal(siguiente):
                # PREDICT
                for p in gram.producciones_de(siguiente):
                    añadir(i, Item(p, 0, i))
            elif i < n and tokens[i].tipo.value == siguiente:
                # SCAN
                añadir(i + 1, Item(
                    item.produccion,
                    item.punto + 1,
                    item.origen,
                    item.hijos + (tokens[i],),
                ))

    # Recolectar ítems aceptantes en la última columna.
    arboles: list[NodoArbol] = []
    for item in chart[n]:
        if item.completo and item.produccion.lhs == gram.S and item.origen == 0:
            arboles.append(_construir_arbol(item))
    return arboles


def _construir_arbol(item: Item) -> NodoArbol:
    """Reconstruye el árbol a partir de los backpointers del ítem completo."""
    hijos: list[NodoArbol] = []
    for h in item.hijos:
        if isinstance(h, Item):
            hijos.append(_construir_arbol(h))
        else:
            # Hoja: nodo terminal (VERBO, ARTICULO, ...) con el lexema debajo.
            hoja = NodoArbol(h.lexema, token=h)
            hijos.append(NodoArbol(h.tipo.value, hijos=[hoja]))
    return NodoArbol(item.produccion.lhs, hijos=hijos)



def formatear_arbol(nodo: NodoArbol) -> str:
    """Imprime el árbol en formato ASCII estilo `tree`."""
    lineas: list[str] = []
    _formatear(nodo, prefijo="", es_ultimo=True, lineas=lineas, raiz=True)
    return "\n".join(lineas)


def formatear_arboles(arboles: list[NodoArbol]) -> str:
    if not arboles:
        return "(sin árbol: la entrada no es un comando válido)"
    if len(arboles) == 1:
        return formatear_arbol(arboles[0])
    partes = []
    for k, a in enumerate(arboles, 1):
        partes.append(f"Árbol #{k}:")
        partes.append(formatear_arbol(a))
    return "\n\n".join(partes)


def _formatear(
    nodo: NodoArbol,
    prefijo: str,
    es_ultimo: bool,
    lineas: list[str],
    raiz: bool = False,
) -> None:
    if raiz:
        lineas.append(nodo.simbolo)
        nuevo_prefijo = ""
    else:
        conector = "└── " if es_ultimo else "├── "
        etiqueta = f"'{nodo.simbolo}'" if nodo.es_hoja else nodo.simbolo
        lineas.append(prefijo + conector + etiqueta)
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")

    for i, hijo in enumerate(nodo.hijos):
        es_ult = i == len(nodo.hijos) - 1
        _formatear(hijo, nuevo_prefijo, es_ult, lineas)
