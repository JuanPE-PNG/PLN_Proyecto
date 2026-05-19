"""
Escape Room RPG en Español
"""
from src.grammar import GRAMATICA, formatear_gramatica
from src.lexer import formatear_tokens, tokenizar

BANNER = """
============================================================
   ESCAPE ROOM RPG — DFA + CFG
============================================================
Todavía no parsea, pero ya hay DFA y gramática.
Escribe un comando en español para tokenizarlo.
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
        print(formatear_tokens(tokens))
        print()


if __name__ == "__main__":
    main()
