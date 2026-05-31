import pytest

from src.lexer import tokenizar
from src.parser import parsear
from src.semantica import interpretar_todos
from src.atn import ATNJuego


# ---------------------------------------------------------------------------
# Helper para ejecutar comandos completos:
# texto -> tokens -> parser -> semántica -> ATN
# ---------------------------------------------------------------------------

def ejecutar_comando(juego: ATNJuego, texto: str) -> str:
    tokens = tokenizar(texto)
    arboles = parsear(tokens)
    acciones = interpretar_todos(arboles)

    assert acciones, f"El comando no produjo ninguna acción válida: {texto!r}"

    return juego.ejecutar(acciones[0])


# ---------------------------------------------------------------------------
# Estado inicial del mundo
# ---------------------------------------------------------------------------

def test_estado_inicial_del_juego():
    juego = ATNJuego()

    assert juego.estado.sala_actual == "celda"
    assert juego.estado.inventario == {}
    assert juego.estado.terminado is False

    assert "celda" in juego.salas
    assert "pasillo" in juego.salas
    assert "biblioteca" in juego.salas
    assert "salida" in juego.salas

    assert "llave" in juego.salas["celda"].objetos


# ---------------------------------------------------------------------------
# Inventario y objetos
# ---------------------------------------------------------------------------

def test_tomar_llave_la_mueve_al_inventario():
    juego = ATNJuego()

    respuesta = ejecutar_comando(juego, "tomar la llave")

    assert "llave" in juego.estado.inventario
    assert "llave" not in juego.salas["celda"].objetos
    assert "tomado" in respuesta.lower() or "has tomado" in respuesta.lower()


def test_no_puede_tomar_objeto_inexistente_en_la_sala():
    juego = ATNJuego()

    respuesta = ejecutar_comando(juego, "tomar el pergamino")

    assert "pergamino" not in juego.estado.inventario
    assert "no veo" in respuesta.lower() or "no encuentras" in respuesta.lower()


def test_soltar_objeto_lo_devuelve_a_la_sala():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    respuesta = ejecutar_comando(juego, "dejar la llave")

    assert "llave" not in juego.estado.inventario
    assert "llave" in juego.salas["celda"].objetos
    assert "dejado" in respuesta.lower() or "soltado" in respuesta.lower()


# ---------------------------------------------------------------------------
# Condiciones de movimiento
# ---------------------------------------------------------------------------

def test_no_puede_ir_al_norte_si_la_puerta_esta_cerrada():
    juego = ATNJuego()

    respuesta = ejecutar_comando(juego, "ir al norte")

    assert juego.estado.sala_actual == "celda"
    assert "cerrada" in respuesta.lower()


def test_no_puede_abrir_puerta_sin_llave():
    juego = ATNJuego()

    respuesta = ejecutar_comando(juego, "abrir la puerta")

    assert juego.estado.sala_actual == "celda"
    assert juego.estado.banderas["puerta_celda_abierta"] is False
    assert "llave" in respuesta.lower()


def test_abrir_puerta_con_llave_desbloquea_transicion():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    respuesta = ejecutar_comando(juego, "abrir la puerta")

    assert juego.estado.banderas["puerta_celda_abierta"] is True
    assert juego.salas["celda"].conexiones["norte"].bloqueada is False
    assert "abres" in respuesta.lower() or "abierta" in respuesta.lower()


def test_puede_moverse_al_pasillo_despues_de_abrir_puerta():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    ejecutar_comando(juego, "abrir la puerta")
    respuesta = ejecutar_comando(juego, "ir al norte")

    assert juego.estado.sala_actual == "pasillo"
    assert "pasillo" in respuesta.lower()


# ---------------------------------------------------------------------------
# Cofre y pergamino
# ---------------------------------------------------------------------------

def test_abrir_cofre_hace_aparecer_pergamino():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    ejecutar_comando(juego, "abrir la puerta")
    ejecutar_comando(juego, "ir al norte")
    ejecutar_comando(juego, "ir al este")

    respuesta = ejecutar_comando(juego, "abrir el cofre con la llave")

    assert juego.estado.sala_actual == "biblioteca"
    assert juego.estado.banderas["cofre_abierto"] is True
    assert "pergamino" in juego.salas["biblioteca"].objetos
    assert "pergamino" in respuesta.lower()


def test_leer_pergamino_desbloquea_salida():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    ejecutar_comando(juego, "abrir la puerta")
    ejecutar_comando(juego, "ir al norte")
    ejecutar_comando(juego, "ir al este")
    ejecutar_comando(juego, "abrir el cofre con la llave")
    ejecutar_comando(juego, "tomar el pergamino")

    respuesta = ejecutar_comando(juego, "leer el pergamino")

    assert juego.estado.banderas["pergamino_leido"] is True
    assert juego.salas["biblioteca"].conexiones["norte"].bloqueada is False
    assert "bloqueo" in respuesta.lower() or "desaparecido" in respuesta.lower()


# ---------------------------------------------------------------------------
# Final del juego
# ---------------------------------------------------------------------------

def test_puede_llegar_a_la_salida_y_terminar_el_juego():
    juego = ATNJuego()

    ejecutar_comando(juego, "tomar la llave")
    ejecutar_comando(juego, "abrir la puerta")
    ejecutar_comando(juego, "ir al norte")
    ejecutar_comando(juego, "ir al este")
    ejecutar_comando(juego, "abrir el cofre con la llave")
    ejecutar_comando(juego, "tomar el pergamino")
    ejecutar_comando(juego, "leer el pergamino")
    respuesta = ejecutar_comando(juego, "ir al norte")

    assert juego.estado.sala_actual == "salida"
    assert juego.estado.terminado is True
    assert "salida" in respuesta.lower() or "escapar" in respuesta.lower()


# ---------------------------------------------------------------------------
# Comandos inválidos
# ---------------------------------------------------------------------------

def test_comando_invalido_no_produce_accion():
    juego = ATNJuego()

    tokens = tokenizar("la llave")
    arboles = parsear(tokens)
    acciones = interpretar_todos(arboles)

    assert acciones == []
    assert juego.estado.sala_actual == "celda"
    assert juego.estado.terminado is False