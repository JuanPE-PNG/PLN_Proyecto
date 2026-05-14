import pytest

from src.lexer import (
    Token,
    TipoToken,
    clasificar,
    es_letra,
    es_separador,
    formatear_tokens,
    normalizar,
    tokenizar,
)

class TestNormalizacion:
    def test_pasa_a_minusculas(self):
        assert normalizar("HOLA") == "hola"

    def test_elimina_tildes(self):
        assert normalizar("habitación") == "habitacion"
        assert normalizar("mágico") == "magico"
        assert normalizar("área") == "area"

    def test_conserva_enie(self):
        assert normalizar("pequeño") == "pequeño"

    def test_mezcla_mayusculas_y_tildes(self):
        assert normalizar("HabitaCIÓN") == "habitacion"

class TestAlfabeto:
    def test_es_letra_acepta_alfabeticos(self):
        for c in "abcdefghijklmnopqrstuvwxyz":
            assert es_letra(c)

    def test_es_letra_acepta_enie(self):
        assert es_letra("ñ")

    def test_es_letra_rechaza_espacio(self):
        assert not es_letra(" ")

    def test_es_letra_rechaza_digito(self):
        assert not es_letra("3")

    def test_es_separador_acepta_espacios_y_signos(self):
        assert es_separador(" ")
        assert es_separador(".")
        assert es_separador(",")
        assert es_separador("\t")

class TestClasificador:
    def test_verbo(self):
        assert clasificar("tomar") == TipoToken.VERBO
        assert clasificar("examinar") == TipoToken.VERBO

    def test_articulo(self):
        assert clasificar("el") == TipoToken.ARTICULO
        assert clasificar("la") == TipoToken.ARTICULO

    def test_sustantivo(self):
        assert clasificar("llave") == TipoToken.SUSTANTIVO
        assert clasificar("cofre") == TipoToken.SUSTANTIVO

    def test_preposicion(self):
        assert clasificar("con") == TipoToken.PREPOSICION
        assert clasificar("hacia") == TipoToken.PREPOSICION

    def test_direccion(self):
        assert clasificar("norte") == TipoToken.DIRECCION
        assert clasificar("arriba") == TipoToken.DIRECCION

    def test_adjetivo(self):
        assert clasificar("dorada") == TipoToken.ADJETIVO

    def test_palabra_fuera_del_lexicon(self):
        assert clasificar("xyzzy") == TipoToken.DESCONOCIDO

class TestTokenizacionBasica:
    def test_palabra_unica(self):
        tokens = tokenizar("llave")
        assert len(tokens) == 1
        assert tokens[0].lexema == "llave"
        assert tokens[0].tipo == TipoToken.SUSTANTIVO

    def test_dos_palabras(self):
        tokens = tokenizar("tomar llave")
        assert len(tokens) == 2
        assert [t.tipo for t in tokens] == [TipoToken.VERBO, TipoToken.SUSTANTIVO]

    def test_comando_con_articulo(self):
        tokens = tokenizar("tomar la llave")
        assert [t.tipo for t in tokens] == [
            TipoToken.VERBO, TipoToken.ARTICULO, TipoToken.SUSTANTIVO,
        ]

    def test_comando_complejo_con_preposicion(self):
        tokens = tokenizar("abrir el cofre con la llave")
        assert [t.tipo for t in tokens] == [
            TipoToken.VERBO, TipoToken.ARTICULO, TipoToken.SUSTANTIVO,
            TipoToken.PREPOSICION, TipoToken.ARTICULO, TipoToken.SUSTANTIVO,
        ]

    def test_comando_con_direccion(self):
        tokens = tokenizar("ir al norte")
        assert [t.tipo for t in tokens] == [
            TipoToken.VERBO, TipoToken.PREPOSICION, TipoToken.DIRECCION,
        ]

    def test_comando_con_adjetivo(self):
        tokens = tokenizar("tomar la llave dorada")
        assert tokens[3].tipo == TipoToken.ADJETIVO
        assert tokens[3].lexema == "dorada"

class TestRobustez:
    def test_cadena_vacia(self):
        assert tokenizar("") == []

    def test_solo_espacios(self):
        assert tokenizar("       ") == []

    def test_multiples_espacios_intermedios(self):
        tokens = tokenizar("tomar      llave")
        assert len(tokens) == 2

    def test_normaliza_mayusculas(self):
        tokens = tokenizar("TOMAR LA LLAVE")
        assert tokens[0].lexema == "tomar"
        assert tokens[0].tipo == TipoToken.VERBO

    def test_normaliza_tildes(self):
        tokens = tokenizar("examinar la habitación")
        assert tokens[2].lexema == "habitacion"
        assert tokens[2].tipo == TipoToken.SUSTANTIVO

    def test_ignora_puntuacion_final(self):
        tokens = tokenizar("tomar llave.")
        assert len(tokens) == 2
        assert tokens[1].lexema == "llave"

    def test_ignora_puntuacion_intermedia(self):
        tokens = tokenizar("tomar, la llave")
        assert len(tokens) == 3

    def test_palabra_desconocida_no_rompe(self):
        tokens = tokenizar("tomar foobar")
        assert tokens[0].tipo == TipoToken.VERBO
        assert tokens[1].tipo == TipoToken.DESCONOCIDO
        assert tokens[1].lexema == "foobar"

    def test_posicion_de_tokens(self):
        tokens = tokenizar("tomar llave")
        assert tokens[0].posicion == 0
        assert tokens[1].posicion == 6

class TestUtilidades:
    def test_formatear_lista_vacia(self):
        assert "sin tokens" in formatear_tokens([])

    def test_formatear_lista_con_tokens(self):
        tokens = tokenizar("tomar llave")
        salida = formatear_tokens(tokens)
        assert "tomar" in salida
        assert "VERBO" in salida
        assert "SUSTANTIVO" in salida


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
