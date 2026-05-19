"""
Gramática de Contexto Libre (CFG) — comandos del escape room

Define formalmente G = (V, T, P, S) donde:
    V = {S, Comando, FV, FN, FP}
    T = {VERBO, ARTICULO, SUSTANTIVO, PREPOSICION, ADJETIVO, DIRECCION}
    S = S
    P = ver lista PRODUCCIONES

Los terminales coinciden con los tipos de token emitidos por el lexer (DFA),
de modo que el parser consume directamente la salida del tokenizador.
"""

from dataclasses import dataclass, field

from src.lexer import TipoToken

@dataclass(frozen=True)
class Produccion:
    lhs: str
    rhs: tuple[str, ...]

    def __repr__(self) -> str:
        cuerpo = " ".join(self.rhs) if self.rhs else "ε"
        return f"{self.lhs} → {cuerpo}"


@dataclass
class Gramatica:
    V: set[str]
    T: set[str]
    P: list[Produccion]
    S: str

    _indice: dict[str, list[Produccion]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._indice = {}
        for p in self.P:
            self._indice.setdefault(p.lhs, []).append(p)

    def producciones_de(self, no_terminal: str) -> list[Produccion]:
        return list(self._indice.get(no_terminal, []))

    def es_terminal(self, simbolo: str) -> bool:
        return simbolo in self.T

    def es_no_terminal(self, simbolo: str) -> bool:
        return simbolo in self.V

INICIO = "S"

NO_TERMINALES = {"S", "Comando", "FV", "FN", "FP"}

TERMINALES = {t.value for t in TipoToken if t is not TipoToken.DESCONOCIDO}

PRODUCCIONES: list[Produccion] = [
    Produccion("S", ("Comando",)),

    Produccion("Comando", ("FV",)),
    Produccion("Comando", ("FV", "FN")),
    Produccion("Comando", ("FV", "FN", "FP")),
    Produccion("Comando", ("FV", "FP")),

    Produccion("FV", ("VERBO",)),

    Produccion("FN", ("ARTICULO", "SUSTANTIVO")),
    Produccion("FN", ("ARTICULO", "ADJETIVO", "SUSTANTIVO")),
    Produccion("FN", ("ARTICULO", "SUSTANTIVO", "ADJETIVO")),
    Produccion("FN", ("SUSTANTIVO",)),
    Produccion("FN", ("ADJETIVO", "SUSTANTIVO")),
    Produccion("FN", ("SUSTANTIVO", "ADJETIVO")),

    Produccion("FP", ("PREPOSICION", "FN")),
    Produccion("FP", ("PREPOSICION", "DIRECCION")),
]


GRAMATICA = Gramatica(
    V=NO_TERMINALES,
    T=TERMINALES,
    P=PRODUCCIONES,
    S=INICIO,
)

def validar(g: Gramatica) -> list[str]:
    """
    Devuelve la lista de errores estructurales. Vacía si la gramática es válida.
    """
    errores: list[str] = []

    if g.S not in g.V:
        errores.append(f"Símbolo inicial '{g.S}' no está en V")

    interseccion = g.V & g.T
    if interseccion:
        errores.append(f"V y T no son disjuntos: {interseccion}")

    union = g.V | g.T
    for p in g.P:
        if p.lhs not in g.V:
            errores.append(f"LHS '{p.lhs}' de la producción '{p}' no está en V")
        for sym in p.rhs:
            if sym not in union:
                errores.append(f"Símbolo '{sym}' en '{p}' no está en V ∪ T")

    return errores

def formatear_gramatica(g: Gramatica) -> str:
    lineas = [
        "G = (V, T, P, S)",
        f"  V = {{ {', '.join(sorted(g.V))} }}",
        f"  T = {{ {', '.join(sorted(g.T))} }}",
        f"  S = {g.S}",
        "  P:",
    ]
    vistos: list[str] = []
    for p in g.P:
        if p.lhs not in vistos:
            vistos.append(p.lhs)
    for lhs in vistos:
        for p in g.producciones_de(lhs):
            lineas.append(f"    {p}")
    return "\n".join(lineas)
