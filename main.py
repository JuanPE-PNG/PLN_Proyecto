"""
Escape Room RPG en Español
"""
from src.lexer import formatear_tokens, tokenizar

BANNER = """
============================================================
   ESCAPE ROOM RPG — DFA
============================================================
No va a hacer mucho, pero tenemos DFA
Escribe un comando en español.
Comandos especiales: 'salir' termina la demo.
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
        if entrada.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break

        tokens = tokenizar(entrada)
        print(formatear_tokens(tokens))
        print()


if __name__ == "__main__":
    main()
