import pytest

from src.lexer import TipoToken, Token, tokenizar
from src.parser import (
    Item,
    NodoArbol,
    formatear_arbol,
    formatear_arboles,
    parsear,
)
from src.grammar import GRAMATICA, Produccion


def parse_texto(s: str) -> list[NodoArbol]:
    return parsear(tokenizar(s))


def recolectar_hojas(nodo: NodoArbol) -> list[str]:
    if nodo.es_hoja:
        return [nodo.simbolo]
    out: list[str] = []
    for h in nodo.hijos:
        out.extend(recolectar_hojas(h))
    return out


def buscar_simbolo(nodo: NodoArbol, simbolo: str) -> list[NodoArbol]:
    encontrados: list[NodoArbol] = []
    if nodo.simbolo == simbolo:
        encontrados.append(nodo)
    for h in nodo.hijos:
        encontrados.extend(buscar_simbolo(h, simbolo))
    return encontrados

class TestAceptacionBasica:
    def test_comando_solo_verbo(self):
        # FV  →  Comando → FV  →  S
        arboles = parse_texto("inventario")
        assert len(arboles) >= 1

    def test_verbo_mas_fn_simple(self):
        arboles = parse_texto("tomar la llave")
        assert len(arboles) >= 1

    def test_verbo_mas_fn_con_adjetivo(self):
        arboles = parse_texto("tomar la llave dorada")
        assert len(arboles) >= 1

    def test_verbo_mas_fn_mas_fp(self):
        arboles = parse_texto("abrir el cofre con la llave")
        assert len(arboles) >= 1

    def test_verbo_mas_fp_con_direccion(self):
        arboles = parse_texto("ir al norte")
        assert len(arboles) >= 1

    def test_verbo_mas_fn_sin_articulo(self):
        # FN → SUSTANTIVO
        arboles = parse_texto("tomar llave")
        assert len(arboles) >= 1


class TestRechazo:
    def test_entrada_vacia(self):
        assert parsear([]) == []

    def test_solo_articulo(self):
        assert parse_texto("la") == []

    def test_dos_articulos_seguidos(self):
        assert parse_texto("la el") == []

    def test_falta_verbo(self):
        # Sin VERBO al inicio no hay Comando posible.
        assert parse_texto("la llave") == []

    def test_palabra_desconocida(self):
        # "foobar" entra como DESCONOCIDO, que no es terminal en T.
        assert parse_texto("tomar foobar") == []

    def test_preposicion_suelta(self):
        assert parse_texto("tomar con") == []


class TestEstructuraArbol:
    def test_raiz_es_S(self):
        arbol = parse_texto("tomar la llave")[0]
        assert arbol.simbolo == "S"

    def test_S_tiene_un_hijo_Comando(self):
        arbol = parse_texto("tomar la llave")[0]
        assert len(arbol.hijos) == 1
        assert arbol.hijos[0].simbolo == "Comando"

    def test_hojas_recuperan_la_oracion_en_orden(self):
        arbol = parse_texto("abrir el cofre con la llave")[0]
        assert recolectar_hojas(arbol) == [
            "abrir", "el", "cofre", "con", "la", "llave",
        ]

    def test_arbol_contiene_FV_FN_FP(self):
        arbol = parse_texto("abrir el cofre con la llave")[0]
        assert buscar_simbolo(arbol, "FV")
        assert buscar_simbolo(arbol, "FN")
        assert buscar_simbolo(arbol, "FP")

    def test_FP_de_direccion_contiene_DIRECCION(self):
        arbol = parse_texto("ir al norte")[0]
        fps = buscar_simbolo(arbol, "FP")
        assert fps
        hojas_fp = recolectar_hojas(fps[0])
        assert "norte" in hojas_fp

    def test_FN_con_adjetivo_anidado(self):
        arbol = parse_texto("tomar la llave dorada")[0]
        fns = buscar_simbolo(arbol, "FN")
        assert fns
        # Debe haber un nodo ADJETIVO dentro del FN
        assert buscar_simbolo(fns[0], "ADJETIVO")

    def test_terminales_son_tipos_de_token_validos(self):
        arbol = parse_texto("tomar la llave")[0]
        tipos_validos = {t.value for t in TipoToken if t is not TipoToken.DESCONOCIDO}

        def chequear(n: NodoArbol):
            if n.es_hoja:
                return
            # Si todos sus hijos son una hoja única → es un terminal
            if len(n.hijos) == 1 and n.hijos[0].es_hoja:
                assert n.simbolo in tipos_validos
            else:
                for h in n.hijos:
                    chequear(h)

        chequear(arbol)


class TestItem:
    def test_item_completo_detectado(self):
        p = Produccion("FV", ("VERBO",))
        it = Item(p, 1, 0)
        assert it.completo
        assert it.siguiente is None

    def test_item_incompleto_apunta_a_siguiente_simbolo(self):
        p = Produccion("Comando", ("FV", "FN", "FP"))
        it = Item(p, 1, 0)
        assert not it.completo
        assert it.siguiente == "FN"

    def test_repr_muestra_el_punto(self):
        p = Produccion("FN", ("ARTICULO", "SUSTANTIVO"))
        it = Item(p, 1, 3)
        s = repr(it)
        assert "•" in s
        assert "ARTICULO" in s
        assert "SUSTANTIVO" in s
        assert "[3]" in s

    def test_clave_no_depende_de_hijos(self):
        p = Produccion("FV", ("VERBO",))
        t = Token("tomar", TipoToken.VERBO, 0)
        a = Item(p, 1, 0, hijos=())
        b = Item(p, 1, 0, hijos=(t,))
        assert a.clave() == b.clave()


class TestFormato:
    def test_incluye_simbolo_inicial(self):
        salida = formatear_arbol(parse_texto("ir al norte")[0])
        assert salida.splitlines()[0] == "S"

    def test_incluye_lexemas_entre_comillas(self):
        salida = formatear_arbol(parse_texto("tomar la llave")[0])
        assert "'tomar'" in salida
        assert "'la'" in salida
        assert "'llave'" in salida

    def test_usa_conectores_de_arbol(self):
        salida = formatear_arbol(parse_texto("tomar la llave")[0])
        assert "└──" in salida
        assert "├──" in salida

    def test_formatear_arboles_lista_vacia(self):
        s = formatear_arboles([])
        assert "no es un comando válido" in s

    def test_formatear_arboles_uno(self):
        arboles = parse_texto("ir al norte")
        s = formatear_arboles(arboles)
        # Un solo árbol no debe llevar encabezado "Árbol #1:"
        assert "Árbol #" not in s
        assert s.splitlines()[0] == "S"


class TestAmbiguedad:

    def test_comando_con_pp_es_ambiguo(self):
        arboles = parse_texto("examinar el cofre con la llave")
        assert len(arboles) == 2

    def test_los_dos_arboles_son_estructuralmente_distintos(self):
        arboles = parse_texto("examinar el cofre con la llave")
        assert formatear_arbol(arboles[0]) != formatear_arbol(arboles[1])

    def test_ambos_arboles_recuperan_la_misma_oracion(self):
        arboles = parse_texto("abrir el cofre con la llave")
        hojas = {tuple(recolectar_hojas(a)) for a in arboles}
        assert hojas == {("abrir", "el", "cofre", "con", "la", "llave")}

    def test_arbol_principal_es_adjuncion_alta(self):
        arbol = parse_texto("examinar el cofre con la llave")[0]
        comando = arbol.hijos[0]
        assert any(h.simbolo == "FP" for h in comando.hijos)

    def test_comando_sin_pp_no_es_ambiguo(self):
        assert len(parse_texto("tomar la llave dorada")) == 1
        assert len(parse_texto("ir al norte")) == 1


class TestEjemplosDelJuego:
    @pytest.mark.parametrize("frase", [
        "tomar la llave",
        "abrir el cofre con la llave",
        "ir al norte",
        "examinar el pergamino",
        "leer el libro",
    ])
    def test_todos_los_ejemplos_del_readme_parsean(self, frase):
        assert len(parse_texto(frase)) >= 1, f"No parsea: {frase!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
