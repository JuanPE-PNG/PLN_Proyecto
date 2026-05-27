"""
Escape Room RPG en Español
"""
from src.grammar import GRAMATICA, formatear_gramatica
from src.lexer import formatear_tokens, tokenizar
from src.parser import formatear_arboles, parsear
from src.semantica import formatear_acciones, interpretar_todos

BANNER = """
============================================================
   ESCAPE ROOM RPG — DFA + CFG + Parser Earley + DCG
============================================================
Escribe un comando en español. Verás: tokens, árbol y la
intención semántica final (estilo DCG / unificación).
Comandos especiales:
   'gramatica' muestra la CFG completa
   'salir'     termina la demo
"""


def main():
    print(BANNER)
    while True:
        try:
            entrada = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not entrada:
            continue
        cmd = entrada.lower()
        if cmd in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        if cmd in {"gramatica", "gramática", "reglas"}:
            print(formatear_gramatica(GRAMATICA))
            print()
            continue

        tokens = tokenizar(entrada)
        print("Tokens:")
        print(formatear_tokens(tokens))

        print("\nÁrbol de derivación:")
        arboles = parsear(tokens)
        print(formatear_arboles(arboles))

        print("\nIntención:")
        print(formatear_acciones(interpretar_todos(arboles)))
        print()


if __name__ == "__main__":
    main()
