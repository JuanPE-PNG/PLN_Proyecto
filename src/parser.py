"""
Parser Chart (Earley) — construye TODOS los árboles de derivación

Recibe la lista de tokens producida por el DFA (src.lexer) y la CFG definida
en src.grammar, y devuelve uno o más árboles de derivación.

¿Por qué Earley y no CYK?
    CYK exige que la gramática esté en Forma Normal de Chomsky (todas las
    producciones de la forma A → BC ó A → a). Nuestra gramática tiene
    producciones como  Comando → FV FN FP  y  FN → ARTICULO ADJETIVO SUSTANTIVO,
    de longitud 3. Earley acepta cualquier CFG sin reescribirla.

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

"""

from dataclasses import dataclass, field
from itertools import product

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


@dataclass
class Item:
    # Estado Earley
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
    
    if not tokens:
        return []

    n = len(tokens)
    chart: list[list[Item]] = [[] for _ in range(n + 1)]
    visto: list[set[tuple]] = [set() for _ in range(n + 1)]

    derivaciones: dict[tuple, list[tuple]] = {}

    def añadir_estado(col: int, item: Item) -> None:
        if item.clave() not in visto[col]:
            visto[col].add(item.clave())
            chart[col].append(item)

    def añadir_derivacion(clave: tuple, fin: int, hijos: tuple) -> None:
        lista = derivaciones.setdefault((clave, fin), [])
        if hijos not in lista:
            lista.append(hijos)

    # Inicialización: S → • α  por cada producción de S, en la columna 0.
    for p in gram.producciones_de(gram.S):
        it = Item(p, 0, 0)
        añadir_estado(0, it)
        añadir_derivacion(it.clave(), 0, ())

    # Bucle principal: cada columna se procesa hasta el punto fijo.
    for i in range(n + 1):
        j = 0
        while j < len(chart[i]):
            item = chart[i][j]
            j += 1
            ck = item.clave()

            if item.completo:
                lhs = item.produccion.lhs
                for cand in list(chart[item.origen]):
                    if cand.siguiente == lhs:
                        nuevo = Item(cand.produccion, cand.punto + 1, cand.origen)
                        añadir_estado(i, nuevo)
                        for alt in derivaciones.get((cand.clave(), item.origen), [()]):
                            añadir_derivacion(nuevo.clave(), i, alt + ((ck, i),))
                continue

            siguiente = item.siguiente
            if gram.es_no_terminal(siguiente):
                # PREDICT
                for p in gram.producciones_de(siguiente):
                    pit = Item(p, 0, i)
                    añadir_estado(i, pit)
                    añadir_derivacion(pit.clave(), i, ())
            elif i < n and tokens[i].tipo.value == siguiente:
                # SCAN
                nuevo = Item(item.produccion, item.punto + 1, item.origen)
                añadir_estado(i + 1, nuevo)
                for alt in derivaciones.get((ck, i), [()]):
                    añadir_derivacion(nuevo.clave(), i + 1, alt + (tokens[i],))

    memo: dict[tuple, list[NodoArbol]] = {}

    def construir(clave: tuple, fin: int) -> list[NodoArbol]:
        if (clave, fin) in memo:
            return memo[(clave, fin)]
        produccion: Produccion = clave[0]
        arboles_aqui: list[NodoArbol] = []
        for alt in derivaciones.get((clave, fin), []):
            opciones_por_posicion: list[list[NodoArbol]] = []
            for elem in alt:
                if isinstance(elem, Token):
                    hoja = NodoArbol(elem.lexema, token=elem)
                    opciones_por_posicion.append([NodoArbol(elem.tipo.value, hijos=[hoja])])
                else:
                    hijo_clave, hijo_fin = elem
                    opciones_por_posicion.append(construir(hijo_clave, hijo_fin))
            if opciones_por_posicion:
                for combo in product(*opciones_por_posicion):
                    arboles_aqui.append(NodoArbol(produccion.lhs, hijos=list(combo)))
            else:
                arboles_aqui.append(NodoArbol(produccion.lhs, hijos=[]))
        memo[(clave, fin)] = arboles_aqui
        return arboles_aqui

    arboles: list[NodoArbol] = []
    for item in chart[n]:
        if item.completo and item.produccion.lhs == gram.S and item.origen == 0:
            arboles.extend(construir(item.clave(), n))

    arboles.sort(key=_grado_anidamiento)
    return _sin_duplicados(arboles)


def _grado_anidamiento(nodo: NodoArbol) -> int:
    c = 1 if nodo.simbolo == "FN" and any(h.simbolo == "FN" for h in nodo.hijos) else 0
    for h in nodo.hijos:
        c += _grado_anidamiento(h)
    return c

def _sin_duplicados(arboles: list[NodoArbol]) -> list[NodoArbol]:
    vistos: set[str] = set()
    unicos: list[NodoArbol] = []
    for a in arboles:
        clave = formatear_arbol(a)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(a)
    return unicos


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
