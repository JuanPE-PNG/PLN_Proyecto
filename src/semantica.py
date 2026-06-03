"""
DCG y unificación semántica — del árbol de derivación a la intención

Cada producción CFG del COMMIT 3 lleva asociado un término semántico que
se "unifica" con los términos de sus constituyentes. Esto reproduce el
estilo de las Definite Clause Grammars (DCG) de Prolog:

    s(accion(V, O, C))     --> comando(V, O, C).
    comando(V, O, C)       --> fv(V), fn(O), fp(C).
    comando(V, O, None)    --> fv(V), fn(O).
    comando(V, None, C)    --> fv(V), fp(C).
    comando(V, None, None) --> fv(V).
    fv(V)                  --> [verbo(V)].
    fn(objeto(N))          --> [art], [sust(N)].
    fn(objeto(N, M))       --> [art], [adj(M)], [sust(N)].
    fp(instrumento(O))     --> [con],  fn(O).
    fp(ubicacion(O))       --> [en],   fn(O).
    fp(direccion(D))       --> [prep], [dir(D)].
    ...

En Python simulamos esa unificación recorriendo el árbol: cada función
`interpretar_X` recibe un nodo del árbol y devuelve el término asociado.
Las variables del DCG son aquí simplemente los valores de retorno que se
ensamblan al subir.

Forma final:
    accion(verbo, objeto | None, complemento)

Donde `complemento` es siempre un término etiquetado por su rol semántico,
incluso cuando no hay FP en la oración — en ese caso el rol se elige por
el tipo del verbo (movimiento → direccion, resto → ubicacion) y el valor
es None, para que el patrón sea uniforme:

    "tomar la llave"            → accion(tomar, objeto(llave), ubicacion(None))
    "ir al norte"               → accion(ir,    None,           direccion(norte))
    "abrir el cofre con la llave"
                                → accion(abrir, objeto(cofre), instrumento(objeto(llave)))
"""

from dataclasses import dataclass

from src.parser import NodoArbol


# ---------------------------------------------------------------------------
# Tabla preposición → rol semántico (selección clásica del español)
# ---------------------------------------------------------------------------
PREPOSICION_A_ROL: dict[str, str] = {
    "con":   "instrumento",
    "en":    "ubicacion",
    "sobre": "ubicacion",
    "bajo":  "ubicacion",
    "a":     "destino",
    "al":    "destino",
    "hacia": "destino",
    "hasta": "destino",
    "de":    "origen",
    "del":   "origen",
    "desde": "origen",
    "por":   "finalidad",
    "para":  "finalidad",
}

# Verbos de movimiento — cuando no llevan FP, el "hueco" semántico esperado
# es una dirección (aunque venga vacío). El resto cae por defecto a ubicacion.
VERBOS_DE_MOVIMIENTO: set[str] = {
    "ir", "mover", "moverse", "caminar", "correr",
    "subir", "bajar", "entrar", "salir",
}


def rol_por_defecto(verbo: str) -> str:
    return "direccion" if verbo in VERBOS_DE_MOVIMIENTO else "ubicacion"


# ---------------------------------------------------------------------------
# Términos semánticos
# ---------------------------------------------------------------------------
@dataclass
class Objeto:
    nucleo: str                       # sustantivo: llave, cofre, ...
    modificador: str | None = None    # adjetivo:   dorada, oxidado, ...
    complemento: "Complemento | None" = None  # PP que modifica al sustantivo

    def __repr__(self) -> str:
        if self.modificador:
            base = f"objeto({self.nucleo}, {self.modificador})"
        else:
            base = f"objeto({self.nucleo})"
        if self.complemento is not None:
            # Adjunción de PP al sustantivo: "el cofre con la llave".
            return f"{base}[{self.complemento!r}]"
        return base


@dataclass
class Complemento:
    rol: str                            # direccion | instrumento | ubicacion | destino | origen | finalidad
    valor: "Objeto | str | None"        # Objeto si vino de FN, str si vino de DIRECCION, None si no hay FP

    def __repr__(self) -> str:
        return f"{self.rol}({self.valor if self.valor is not None else 'None'})"


@dataclass
class Accion:
    verbo: str
    objeto: Objeto | None = None
    complemento: Complemento | None = None

    def __repr__(self) -> str:
        o = repr(self.objeto) if self.objeto is not None else "None"
        if self.complemento is not None:
            c = repr(self.complemento)
        else:
            # No hubo FP: rellenamos el hueco con el rol esperado por el verbo
            # y valor None, para que la representación tenga aridad uniforme.
            c = f"{rol_por_defecto(self.verbo)}(None)"
        return f"accion({self.verbo}, {o}, {c})"


# ---------------------------------------------------------------------------
# Interpretación (unificación) sobre el árbol
# ---------------------------------------------------------------------------
def interpretar(arbol: NodoArbol) -> Accion:
    """Interpreta el árbol cuya raíz es S y devuelve la `Accion` asociada."""
    if arbol.simbolo != "S":
        raise ValueError(f"Se esperaba raíz S, se recibió {arbol.simbolo!r}")
    # S → Comando
    return _interpretar_comando(arbol.hijos[0])


def interpretar_todos(arboles: list[NodoArbol]) -> list[Accion]:
    return [interpretar(a) for a in arboles]


def _lexema(nodo_terminal: NodoArbol) -> str:
    """Dado un nodo terminal (VERBO, SUSTANTIVO, ...) devuelve su lexema."""
    return nodo_terminal.hijos[0].simbolo


def _interpretar_comando(comando: NodoArbol) -> Accion:
    """Comando → FV | FV FN | FV FN FP | FV FP

    Recorre los hijos y unifica cada constituyente con el slot adecuado.
    """
    verbo: str | None = None
    objeto: Objeto | None = None
    complemento: Complemento | None = None

    for hijo in comando.hijos:
        if hijo.simbolo == "FV":
            verbo = _interpretar_fv(hijo)
        elif hijo.simbolo == "FN":
            objeto = _interpretar_fn(hijo)
        elif hijo.simbolo == "FP":
            complemento = _interpretar_fp(hijo, verbo)

    assert verbo is not None, "Todo Comando deriva al menos un FV"
    return Accion(verbo=verbo, objeto=objeto, complemento=complemento)


def _interpretar_fv(fv: NodoArbol) -> str:
    """FV → VERBO"""
    return _lexema(fv.hijos[0])


def _interpretar_fn(fn: NodoArbol) -> Objeto:
    """FN → ART SUST | ART ADJ SUST | ART SUST ADJ | SUST | ADJ SUST | SUST ADJ
            | FN FP

    El artículo se descarta semánticamente (no aporta intención).
    El adjetivo, si está, se unifica como `modificador` del objeto.
    Si el FN lleva un FP adjunto (FN → FN FP), ese PP se interpreta como
    `complemento` del objeto — es la lectura "el cofre con la llave".
    """
    nucleo: str | None = None
    modificador: str | None = None
    complemento: Complemento | None = None
    for h in fn.hijos:
        if h.simbolo == "SUSTANTIVO":
            nucleo = _lexema(h)
        elif h.simbolo == "ADJETIVO":
            modificador = _lexema(h)
        elif h.simbolo == "FN":
            # FN → FN FP: el núcleo viene del FN interno.
            sub = _interpretar_fn(h)
            nucleo = sub.nucleo
            modificador = sub.modificador
            complemento = sub.complemento
        elif h.simbolo == "FP":
            complemento = _interpretar_fp(h, None)
        # ARTICULO se ignora
    assert nucleo is not None, "Todo FN tiene un SUSTANTIVO"
    return Objeto(nucleo=nucleo, modificador=modificador, complemento=complemento)


def _interpretar_fp(fp: NodoArbol, verbo: str | None) -> Complemento:
    """FP → PREPOSICION FN | PREPOSICION DIRECCION

    El rol del complemento sale de la preposición; si el segundo hijo
    es DIRECCION, el rol se fuerza a 'direccion' independientemente
    de la preposición (porque el contenido es lo determinante).
    """
    prep_lex = _lexema(fp.hijos[0])
    segundo = fp.hijos[1]

    if segundo.simbolo == "DIRECCION":
        return Complemento(rol="direccion", valor=_lexema(segundo))

    # FN
    objeto = _interpretar_fn(segundo)
    rol = PREPOSICION_A_ROL.get(prep_lex)
    if rol is None:
        rol = rol_por_defecto(verbo) if verbo else "ubicacion"
    return Complemento(rol=rol, valor=objeto)


# ---------------------------------------------------------------------------
# Formateo
# ---------------------------------------------------------------------------
def formatear_acciones(acciones: list[Accion]) -> str:
    if not acciones:
        return "(sin intención: la entrada no es un comando válido)"
    if len(acciones) == 1:
        return repr(acciones[0])
    return "\n".join(f"#{k}: {a!r}" for k, a in enumerate(acciones, 1))
