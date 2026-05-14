"""
Lexer/Tokenizador - Autómata Finito Determinista (DFA)

Este módulo convierte una cadena en español en una lista de tokens clasificados por su categoría léxica.

El DFA segmenta la entrada en palabras, y el lexicón clasifica cada palabra.

Definición formal del autómata:
    Q  = {Q0, Q1}
    Σ  = letras_español U separadores
    q0 = Q0
    F  = {Q1}  (se acepta cuando se emite el token al pasar a separador)
    δ:
        δ(Q0, letra)     = Q1
        δ(Q0, separador) = Q0
        δ(Q1, letra)     = Q1
        δ(Q1, separador) = Q0   (emite token)
"""

from dataclasses import dataclass
from enum import Enum

class TipoToken(Enum):
    VERBO = "VERBO"
    ARTICULO = "ARTICULO"
    SUSTANTIVO = "SUSTANTIVO"
    PREPOSICION = "PREPOSICION"
    ADJETIVO = "ADJETIVO"
    DIRECCION = "DIRECCION"
    DESCONOCIDO = "DESCONOCIDO"


@dataclass
class Token:
    lexema: str
    tipo: TipoToken
    posicion: int

    def __repr__(self) -> str:
        return f"<{self.tipo.value}:'{self.lexema}'@{self.posicion}>"


# ---------------------------------------------------------------------------
# Lexicón - vocabulario del juego
# ---------------------------------------------------------------------------
VERBOS = {
    # de movimiento
    "ir", "mover", "moverse", "caminar", "correr", "subir", "bajar", "entrar", "salir",

    # de manipulación
    "tomar", "coger", "agarrar", "recoger", "soltar", "dejar", "tirar",

    # de interacción con objetos
    "abrir", "cerrar", "romper", "empujar", "halar", "girar",

    # deobservación
    "examinar", "mirar", "observar", "ver", "inspeccionar", "leer",

    # deuso
    "usar", "combinar", "encender", "apagar",

    # de meta-comandos
    "inventario", "ayuda", "guardar",
}

ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas"}

SUSTANTIVOS = {
    # objetos
    "llave", "cofre", "baul", "pergamino", "libro", "espada", "antorcha",
    "cuerda", "mapa", "amuleto", "moneda", "cadena", "cerradura",
    "pocion", "anillo", "gema", "vela", "daga", "escudo",

    # mobiliario / entorno
    "puerta", "mesa", "silla", "ventana", "pared", "piso", "techo",
    "estante", "armario", "cama", "altar", "trono",

    # lugares
    "torre", "sala", "habitacion", "pasillo", "cuarto", "biblioteca",
    "mazmorra", "celda", "patio", "escalera", "calabozo",
}

PREPOSICIONES = {
    "a", "al", "con", "en", "de", "del", "hacia", "sobre",
    "bajo", "desde", "hasta", "por", "para",

}

ADJETIVOS = {
    "dorado", "dorada", "plateado", "plateada", "oxidado", "oxidada",
    "viejo", "vieja", "nuevo", "nueva", "grande", "pequeno", "pequena",
    "magico", "magica", "roto", "rota", "rojo", "roja", "azul",
    "verde", "negro", "negra", "blanco", "blanca", "brillante", "oscuro", "oscura",
}

DIRECCIONES = {"norte", "sur", "este", "oeste", "arriba", "abajo"}


TABLA_LEXICON: list[tuple[set[str], TipoToken]] = [
    (VERBOS, TipoToken.VERBO),
    (ARTICULOS, TipoToken.ARTICULO),
    (PREPOSICIONES, TipoToken.PREPOSICION),
    (DIRECCIONES, TipoToken.DIRECCION),
    (SUSTANTIVOS, TipoToken.SUSTANTIVO),
    (ADJETIVOS, TipoToken.ADJETIVO),
]


# Normalizacion de las palabras
TABLA_TILDES = str.maketrans("áéíóúüÁÉÍÓÚÜ", "aeiouuAEIOUU")

def normalizar(texto: str) -> str:
    return texto.translate(TABLA_TILDES).lower()

def es_letra(c: str) -> bool:
    return c.isalpha() or c == "ñ"


def es_separador(c: str) -> bool:
    return not es_letra(c)


def clasificar(palabra: str) -> TipoToken:
    for conjunto, tipo in TABLA_LEXICON:
        if palabra in conjunto:
            return tipo
    return TipoToken.DESCONOCIDO

class Estado(Enum):
    Q0 = "Q0"  # fuera de palabra
    Q1 = "Q1"  # dentro de palabra

def tokenizar(entrada: str) -> list[Token]:
    if not entrada:
        return []

    texto = normalizar(entrada) + " "
    tokens: list[Token] = []
    estado = Estado.Q0
    buffer = ""
    inicio = 0

    for i, c in enumerate(texto):
        if estado == Estado.Q0:
            if es_letra(c):
                buffer = c
                inicio = i
                estado = Estado.Q1
            # δ(Q0, separador) = Q0  → no hace nada

        else:  # cuando estado == Q1
            if es_letra(c):
                buffer += c
                # δ(Q1, letra) = Q1

            else:
                # δ(Q1, separador) = Q0, emite token
                tokens.append(Token(buffer, clasificar(buffer), inicio))
                buffer = ""
                estado = Estado.Q0

    return tokens

def formatear_tokens(tokens: list[Token]) -> str:
    if not tokens:
        return "(sin tokens)"
    ancho = max(len(t.lexema) for t in tokens)
    lineas = [f"  {t.lexema:<{ancho}}  →  {t.tipo.value}" for t in tokens]
    return "\n".join(lineas)
 