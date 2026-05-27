import pytest

from src.lexer import tokenizar
from src.parser import parsear
from src.semantica import (
    Accion,
    Complemento,
    Objeto,
    PREPOSICION_A_ROL,
    VERBOS_DE_MOVIMIENTO,
    formatear_acciones,
    interpretar,
    interpretar_todos,
    rol_por_defecto,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def interpretar_texto(s: str) -> Accion:
    arboles = parsear(tokenizar(s))
    assert arboles, f"La frase {s!r} no parseó"
    return interpretar(arboles[0])


# ---------------------------------------------------------------------------
# Términos
# ---------------------------------------------------------------------------
class TestObjeto:
    def test_repr_sin_modificador(self):
        assert repr(Objeto("llave")) == "objeto(llave)"

    def test_repr_con_modificador(self):
        assert repr(Objeto("llave", "dorada")) == "objeto(llave, dorada)"


class TestComplemento:
    def test_repr_con_string(self):
        assert repr(Complemento("direccion", "norte")) == "direccion(norte)"

    def test_repr_con_objeto(self):
        c = Complemento("instrumento", Objeto("llave"))
        assert repr(c) == "instrumento(objeto(llave))"

    def test_repr_con_none(self):
        assert repr(Complemento("ubicacion", None)) == "ubicacion(None)"


class TestAccionRepr:
    def test_accion_sin_objeto_sin_complemento_usa_rol_por_defecto(self):
        a = Accion(verbo="inventario")
        assert repr(a) == "accion(inventario, None, ubicacion(None))"

    def test_accion_movimiento_sin_FP_usa_direccion(self):
        a = Accion(verbo="ir")
        assert repr(a) == "accion(ir, None, direccion(None))"


# ---------------------------------------------------------------------------
# Tabla de roles
# ---------------------------------------------------------------------------
class TestRoles:
    def test_con_es_instrumento(self):
        assert PREPOSICION_A_ROL["con"] == "instrumento"

    def test_al_es_destino(self):
        assert PREPOSICION_A_ROL["al"] == "destino"

    def test_en_es_ubicacion(self):
        assert PREPOSICION_A_ROL["en"] == "ubicacion"

    def test_rol_por_defecto_movimiento(self):
        for v in {"ir", "subir", "bajar", "entrar"}:
            assert rol_por_defecto(v) == "direccion"
            assert v in VERBOS_DE_MOVIMIENTO

    def test_rol_por_defecto_no_movimiento(self):
        for v in {"tomar", "abrir", "examinar", "leer"}:
            assert rol_por_defecto(v) == "ubicacion"


# ---------------------------------------------------------------------------
# Interpretación contra el árbol real
# ---------------------------------------------------------------------------
class TestInterpretacion:
    def test_verbo_solo(self):
        a = interpretar_texto("inventario")
        assert a.verbo == "inventario"
        assert a.objeto is None
        assert a.complemento is None

    def test_tomar_la_llave(self):
        a = interpretar_texto("tomar la llave")
        assert a.verbo == "tomar"
        assert a.objeto == Objeto("llave")
        assert a.complemento is None

    def test_tomar_la_llave_dorada(self):
        a = interpretar_texto("tomar la llave dorada")
        assert a.objeto == Objeto("llave", "dorada")

    def test_ir_al_norte(self):
        a = interpretar_texto("ir al norte")
        assert a.verbo == "ir"
        assert a.objeto is None
        assert a.complemento == Complemento("direccion", "norte")

    def test_abrir_cofre_con_llave(self):
        a = interpretar_texto("abrir el cofre con la llave")
        assert a.verbo == "abrir"
        assert a.objeto == Objeto("cofre")
        assert a.complemento == Complemento("instrumento", Objeto("llave"))

    def test_examinar_el_pergamino_en_la_mesa(self):
        a = interpretar_texto("examinar el pergamino en la mesa")
        assert a.objeto == Objeto("pergamino")
        assert a.complemento == Complemento("ubicacion", Objeto("mesa"))

    def test_articulo_se_descarta(self):
        # Ni "la" ni "el" aparecen como información semántica
        a = interpretar_texto("tomar la llave")
        r = repr(a)
        assert " la" not in r and "el " not in r and "(la" not in r


# ---------------------------------------------------------------------------
# Match exacto contra los ejemplos del enunciado
# ---------------------------------------------------------------------------
class TestEjemplosDelEnunciado:
    def test_tomar_la_llave_repr_exacto(self):
        assert repr(interpretar_texto("tomar la llave")) == (
            "accion(tomar, objeto(llave), ubicacion(None))"
        )

    def test_ir_al_norte_repr_exacto(self):
        assert repr(interpretar_texto("ir al norte")) == (
            "accion(ir, None, direccion(norte))"
        )


# ---------------------------------------------------------------------------
# Casos múltiples / formateo
# ---------------------------------------------------------------------------
class TestUtilidades:
    def test_interpretar_todos(self):
        arboles = parsear(tokenizar("tomar la llave"))
        acciones = interpretar_todos(arboles)
        assert len(acciones) == len(arboles) >= 1
        assert acciones[0].verbo == "tomar"

    def test_formatear_acciones_vacio(self):
        s = formatear_acciones([])
        assert "no es un comando válido" in s

    def test_formatear_acciones_una(self):
        a = interpretar_texto("ir al norte")
        s = formatear_acciones([a])
        assert s == "accion(ir, None, direccion(norte))"

    def test_formatear_acciones_varias(self):
        a1 = interpretar_texto("tomar la llave")
        a2 = interpretar_texto("ir al norte")
        s = formatear_acciones([a1, a2])
        assert "#1:" in s and "#2:" in s

    def test_interpretar_rechaza_raiz_que_no_es_S(self):
        arbol = parsear(tokenizar("ir al norte"))[0]
        # Pasar el subárbol Comando debe fallar
        comando = arbol.hijos[0]
        with pytest.raises(ValueError):
            interpretar(comando)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
