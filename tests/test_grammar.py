import pytest

from src.grammar import (
    GRAMATICA,
    INICIO,
    NO_TERMINALES,
    PRODUCCIONES,
    TERMINALES,
    Gramatica,
    Produccion,
    formatear_gramatica,
    validar,
)


class TestProduccion:
    def test_repr_simple(self):
        assert repr(Produccion("FV", ("VERBO",))) == "FV → VERBO"

    def test_repr_compuesto(self):
        p = Produccion("FN", ("ARTICULO", "SUSTANTIVO"))
        assert repr(p) == "FN → ARTICULO SUSTANTIVO"

    def test_es_hashable(self):
        p1 = Produccion("FV", ("VERBO",))
        p2 = Produccion("FV", ("VERBO",))
        assert {p1, p2} == {p1}

    def test_no_se_puede_mutar(self):
        # frozen=True
        p = Produccion("FV", ("VERBO",))
        with pytest.raises(Exception):
            p.lhs = "X"  # type: ignore[misc]


class TestEstructuraGramatica:
    def test_simbolo_inicial_es_S(self):
        assert GRAMATICA.S == "S"
        assert INICIO == "S"

    def test_simbolo_inicial_pertenece_a_V(self):
        assert GRAMATICA.S in GRAMATICA.V

    def test_no_terminales_esperados(self):
        for nt in {"S", "Comando", "FV", "FN", "FP"}:
            assert nt in GRAMATICA.V

    def test_terminales_provienen_de_tipos_de_token(self):
        for t in {"VERBO", "ARTICULO", "SUSTANTIVO", "PREPOSICION", "ADJETIVO", "DIRECCION"}:
            assert t in GRAMATICA.T

    def test_desconocido_no_esta_en_T(self):
        # DESCONOCIDO sólo se usa para señalar entrada inválida.
        assert "DESCONOCIDO" not in GRAMATICA.T

    def test_V_y_T_disjuntos(self):
        assert GRAMATICA.V.isdisjoint(GRAMATICA.T)

    def test_hay_al_menos_una_produccion_por_no_terminal(self):
        for nt in GRAMATICA.V:
            assert GRAMATICA.producciones_de(nt), f"{nt} no tiene producciones"


class TestProduccionesDelJuego:
    def test_S_deriva_Comando(self):
        prods = GRAMATICA.producciones_de("S")
        assert any(p.rhs == ("Comando",) for p in prods)

    def test_FV_deriva_VERBO(self):
        prods = GRAMATICA.producciones_de("FV")
        assert any(p.rhs == ("VERBO",) for p in prods)

    def test_FN_acepta_articulo_sustantivo(self):
        prods = GRAMATICA.producciones_de("FN")
        assert any(p.rhs == ("ARTICULO", "SUSTANTIVO") for p in prods)

    def test_FN_acepta_articulo_sustantivo_adjetivo(self):
        prods = GRAMATICA.producciones_de("FN")
        assert any(p.rhs == ("ARTICULO", "SUSTANTIVO", "ADJETIVO") for p in prods)

    def test_FP_acepta_preposicion_FN(self):
        prods = GRAMATICA.producciones_de("FP")
        assert any(p.rhs == ("PREPOSICION", "FN") for p in prods)

    def test_FP_acepta_preposicion_direccion(self):
        prods = GRAMATICA.producciones_de("FP")
        assert any(p.rhs == ("PREPOSICION", "DIRECCION") for p in prods)

    def test_Comando_acepta_FV_FN_FP(self):
        prods = GRAMATICA.producciones_de("Comando")
        assert any(p.rhs == ("FV", "FN", "FP") for p in prods)


class TestValidacion:
    def test_gramatica_principal_es_valida(self):
        assert validar(GRAMATICA) == []

    def test_detecta_simbolo_inicial_fuera_de_V(self):
        g = Gramatica(V={"A"}, T=set(), P=[Produccion("A", ())], S="Z")
        errores = validar(g)
        assert any("inicial" in e.lower() for e in errores)

    def test_detecta_V_y_T_no_disjuntos(self):
        g = Gramatica(V={"X"}, T={"X"}, P=[Produccion("X", ())], S="X")
        errores = validar(g)
        assert any("disjuntos" in e for e in errores)

    def test_detecta_lhs_fuera_de_V(self):
        g = Gramatica(V={"A"}, T={"a"}, P=[Produccion("B", ("a",))], S="A")
        errores = validar(g)
        assert any("LHS" in e for e in errores)

    def test_detecta_simbolo_rhs_invalido(self):
        g = Gramatica(V={"A"}, T={"a"}, P=[Produccion("A", ("a", "Z"))], S="A")
        errores = validar(g)
        assert any("'Z'" in e for e in errores)


class TestUtilidades:
    def test_es_terminal(self):
        assert GRAMATICA.es_terminal("VERBO")
        assert not GRAMATICA.es_terminal("S")

    def test_es_no_terminal(self):
        assert GRAMATICA.es_no_terminal("S")
        assert not GRAMATICA.es_no_terminal("VERBO")

    def test_formato_incluye_cabecera_y_flecha(self):
        salida = formatear_gramatica(GRAMATICA)
        assert "G = (V, T, P, S)" in salida
        assert "→" in salida
        assert "VERBO" in salida


class TestCoberturaDeComandos:
    """Verifica que las secuencias de tokens de ejemplo tengan producciones que las cubran."""

    def test_existe_produccion_para_tomar_la_llave(self):
        # FV FN  con FN = ARTICULO SUSTANTIVO
        assert any(p.rhs == ("FV", "FN") for p in PRODUCCIONES)
        assert any(p.rhs == ("ARTICULO", "SUSTANTIVO") for p in PRODUCCIONES)

    def test_existe_produccion_para_ir_al_norte(self):
        # FV FP  con FP = PREPOSICION DIRECCION
        assert any(p.rhs == ("FV", "FP") for p in PRODUCCIONES)
        assert any(p.rhs == ("PREPOSICION", "DIRECCION") for p in PRODUCCIONES)

    def test_existe_produccion_para_abrir_cofre_con_llave(self):
        # FV FN FP
        assert any(p.rhs == ("FV", "FN", "FP") for p in PRODUCCIONES)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
