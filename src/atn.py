"""
ATN del Escape Room RPG

Este módulo modela el mundo del juego mediante un Autómata de Transición
Aumentado (ATN). A diferencia del parser, que valida la estructura lingüística
del comando, la ATN valida si la acción tiene sentido dentro del estado actual
del juego.

La ATN contiene:
- Estados: salas del juego.
- Transiciones: conexiones entre salas.
- Registros aumentados: inventario, objetos por sala y banderas del mundo.
- Condiciones: requisitos para ejecutar ciertas acciones.
- Acciones semánticas: efectos sobre el estado global.
"""

from dataclasses import dataclass, field

from src.semantica import Accion, Objeto, Complemento


#esto sirve pa que pueda tomar, mirar o mostrar en la sala
@dataclass
class ObjetoMundo:
    nombre: str
    descripcion: str
    portable: bool = True
    visible: bool = True
    descripcion_inventario: str | None = None


# esto es la conexion entre las salas, puede estar bloqueada o no, y puede tener una condicion para desbloquearse
@dataclass
class Conexion:
    destino: str
    bloqueada: bool = False
    condicion: str | None = None
    mensaje_bloqueo: str = "No puedes avanzar por ahí todavía."


@dataclass
class Sala:
    nombre: str
    descripcion: str
    objetos: dict[str, ObjetoMundo] = field(default_factory=dict)
    conexiones: dict[str, Conexion] = field(default_factory=dict)


@dataclass
class EstadoJuego:
    sala_actual: str
    inventario: dict[str, ObjetoMundo] = field(default_factory=dict)
    banderas: dict[str, bool] = field(default_factory=dict)
    terminado: bool = False



class ATNJuego:
    def __init__(self):
        self.salas = self._crear_mundo()
        self.estado = EstadoJuego(
            sala_actual="celda",
            banderas={
                "puerta_celda_abierta": False,
                "cofre_abierto": False,
                "pergamino_leido": False,
            }
        )

    #Es la definicion del mundo, salas, objetos, conexiones, banderas, etc
    def _crear_mundo(self) -> dict[str, Sala]:
        celda = Sala(
            nombre="celda",
            descripcion=(
                "Estás en una celda antigua de piedra. Hay humedad en las paredes "
                "y un silencio incómodo en el ambiente..."
            ),
            objetos={
                "llave": ObjetoMundo(
                    nombre="llave",
                    descripcion=(
                        "La llave está en la mano rígida de un cadáver. "
                        "Tiene una etiqueta vieja que dice: 'llave maestra'."
                    ),
                    descripcion_inventario=(
                        "Tienes en la mano la llave maestra. La etiqueta vieja todavía cuelga de ella."
                    ),
                    portable=True,
                ),
                "cadaver": ObjetoMundo(
                    nombre="cadaver",
                    descripcion=(
                        "Es un cadáver antiguo apoyado contra la pared. "
                        "Su mano parece haber sostenido algo durante mucho tiempo."
                    ),
                    portable=False,
                ),
                "pared": ObjetoMundo(
                    nombre="pared",
                    descripcion=(
                        "La pared tiene marcas extrañas, como si alguien hubiera contado "
                        "los días encerrado aquí."
                    ),
                    portable=False,
                ),
                "puerta": ObjetoMundo(
                    nombre="puerta",
                    descripcion="Una puerta vieja de madera reforzada con metal.",
                    portable=False,
                ),
            },
            conexiones={
                "norte": Conexion(
                    destino="pasillo",
                    bloqueada=True,
                    condicion="puerta_celda_abierta",
                    mensaje_bloqueo="La puerta de la celda está cerrada. Necesitas abrirla primero."
                )
            }
        )

        pasillo = Sala(
            nombre="pasillo",
            descripcion=(
                "Llegas a un pasillo oscuro de piedra. El aire es frío y se escucha "
                "un eco lejano."
            ),
            objetos={
                "antorcha": ObjetoMundo(
                    nombre="antorcha",
                    descripcion="Una antorcha encendida está fijada a la pared del pasillo.",
                    descripcion_inventario="Tienes la antorcha encendida en la mano. Ilumina débilmente el camino.",
                    portable=True,
                )
            },
            conexiones={
                "sur": Conexion(destino="celda"),
                "este": Conexion(destino="biblioteca"),
            }
        )

        biblioteca = Sala(
            nombre="biblioteca",
            descripcion=(
                "Estás en una biblioteca antigua. El polvo cubre los estantes "
                "y hay una mesa en el centro de la sala."
            ),
            objetos={
                "cofre": ObjetoMundo(
                    nombre="cofre",
                    descripcion="Un cofre viejo con una cerradura pequeña.",
                    portable=False,
                ),
                "libro": ObjetoMundo(
                    nombre="libro",
                    descripcion="Un libro antiguo descansa sobre uno de los estantes.",
                    descripcion_inventario="Tienes un libro antiguo en las manos. Su cubierta está deteriorada.",
                    portable=True,
                ),
            },
            conexiones={
                "oeste": Conexion(destino="pasillo"),
                "norte": Conexion(
                    destino="salida",
                    bloqueada=True,
                    condicion="pergamino_leido",
                    mensaje_bloqueo="Una fuerza mágica bloquea la salida. Debes leer el pergamino primero."
                )
            }
        )

        salida = Sala(
            nombre="salida",
            descripcion=(
                "Has llegado a la salida de la torre. La puerta se abre lentamente "
                "y logras escapar."
            ),
            objetos={},
            conexiones={}
        )

        return {
            "celda": celda,
            "pasillo": pasillo,
            "biblioteca": biblioteca,
            "salida": salida,
        }

    def ejecutar(self, accion: Accion) -> str:
        """
        Ejecuta una acción semántica sobre el estado actual del mundo.
        """
        verbo = accion.verbo

        if verbo in {"ir", "mover", "moverse", "caminar", "correr", "subir", "bajar", "entrar", "salir"}:
            return self._mover(accion)

        if verbo in {"tomar", "coger", "agarrar", "recoger"}:
            return self._tomar(accion)

        if verbo in {"soltar", "dejar", "tirar"}:
            return self._soltar(accion)

        if verbo in {"examinar", "mirar", "observar", "ver", "inspeccionar"}:
            return self._examinar(accion)

        if verbo == "abrir":
            return self._abrir(accion)

        if verbo == "leer":
            return self._leer(accion)

        if verbo == "inventario":
            return self._inventario()

        if verbo == "ayuda":
            return self._ayuda()

        return f"Entendí la acción '{verbo}', pero todavía no tiene efecto implementado en la ATN."


    def _mover(self, accion: Accion) -> str:
        sala = self.salas[self.estado.sala_actual]

        direccion = self._extraer_direccion(accion.complemento)

        if direccion is None:
            return "¿Hacia dónde quieres ir? Puedes indicar una dirección como norte, sur, este u oeste."

        if direccion not in sala.conexiones:
            return f"No hay salida hacia {direccion} desde {sala.nombre}."

        conexion = sala.conexiones[direccion]

        #si la conexion esta bloqueada, revisa si hay una condicion, y si esa condicion no se cumple, devuelve el mensaje de bloqueo
        if conexion.bloqueada:
            condicion = conexion.condicion
            if condicion and not self.estado.banderas.get(condicion, False):
                return conexion.mensaje_bloqueo

        #si no esta bloqueada, o si la condicion se cumple, entonces se mueve a la nueva sala
        self.estado.sala_actual = conexion.destino
        nueva_sala = self.salas[self.estado.sala_actual]

        if nueva_sala.nombre == "salida":
            self.estado.terminado = True

        return self._describir_sala()


    def _tomar(self, accion: Accion) -> str:
        if accion.objeto is None:
            return "¿Qué quieres tomar?"

        nombre = accion.objeto.nucleo
        sala = self.salas[self.estado.sala_actual]

        if nombre not in sala.objetos:
            return f"No veo ningún objeto llamado '{nombre}' en esta sala."

        objeto = sala.objetos[nombre]

        if not objeto.portable:
            return f"No puedes tomar {nombre}."

        # sino se encuentra bloqueado, entonces se mueve el objeto al inventario y se elimina de la sala
        self.estado.inventario[nombre] = objeto
        del sala.objetos[nombre]

        return f"Has tomado {nombre}."

    def _soltar(self, accion: Accion) -> str:
        if accion.objeto is None:
            return "¿Qué quieres soltar?"

        nombre = accion.objeto.nucleo

        if nombre not in self.estado.inventario:
            return f"No tienes {nombre} en tu inventario."

        objeto = self.estado.inventario[nombre]
        sala = self.salas[self.estado.sala_actual]

        sala.objetos[nombre] = objeto
        del self.estado.inventario[nombre]

        return f"Has dejado {nombre} en la sala."


    def _examinar(self, accion: Accion) -> str:
        sala = self.salas[self.estado.sala_actual]

        if accion.objeto is None:
            return self._describir_sala()

        nombre = accion.objeto.nucleo

        # Casos especiales dependientes del estado
        if nombre == "puerta" and self.estado.sala_actual == "celda":
            if self.estado.banderas.get("puerta_celda_abierta", False):
                return "La puerta de la celda está abierta. Ahora puedes avanzar hacia el norte."
            return "La puerta de la celda está cerrada. Parece que necesita una llave."

        if nombre == "antorcha":
            if "antorcha" in self.estado.inventario:
                return "Tienes la antorcha encendida en la mano. Su luz te ayuda a ver mejor."
            if "antorcha" in sala.objetos:
                return sala.objetos["antorcha"].descripcion
            return "No ves ninguna antorcha aquí."

        if nombre == "llave":
            if "llave" in self.estado.inventario:
                return "Tienes la llave maestra en la mano. Su etiqueta vieja confirma su importancia."
            if "llave" in sala.objetos:
                return sala.objetos["llave"].descripcion
            return "La llave ya no está en esta sala."

        if nombre == "libro":
            if "libro" in self.estado.inventario:
                return "Tienes el libro antiguo en tus manos. La cubierta está gastada y cubierta de polvo."
            if "libro" in sala.objetos:
                return sala.objetos["libro"].descripcion
            return "No ves ningún libro aquí."

        if nombre == "cofre":
            if self.estado.sala_actual != "biblioteca":
                return "No ves ningún cofre aquí."

            if self.estado.banderas.get("cofre_abierto", False):
                return "El cofre está abierto. Ya reveló lo que guardaba en su interior."

            return "El cofre está cerrado. Su cerradura parece compatible con la llave maestra."

        if nombre == "cadaver":
            if self.estado.sala_actual != "celda":
                return "No hay ningún cadáver aquí."

            if "llave" in self.salas["celda"].objetos:
                return (
                    "El cadáver sostiene una llave en su mano. "
                    "La etiqueta de la llave dice: 'llave maestra'."
                )

            return "El cadáver sigue apoyado contra la pared, pero su mano ahora está vacía."

        if nombre == "mano":
            if self.estado.sala_actual != "celda":
                return "No ves ninguna mano relevante aquí."

            if "llave" in self.salas["celda"].objetos:
                return "La mano del cadáver sostiene una llave con una etiqueta vieja."

            return "La mano del cadáver está vacía."

        if nombre == "etiqueta":
            if "llave" in self.estado.inventario:
                return "La etiqueta de la llave dice: 'llave maestra'."

            if self.estado.sala_actual == "celda" and "llave" in self.salas["celda"].objetos:
                return "La etiqueta colgada de la llave dice: 'llave maestra'."

            return "No ves ninguna etiqueta importante aquí."


        # Revisión normal: primero sala, luego inventario
        if nombre in sala.objetos:
            return sala.objetos[nombre].descripcion

        # Si no está en la sala, revisa el inventario, ayuda a ver si se ha tomado el objeto o no y muestra descripcion
        if nombre in self.estado.inventario:
            objeto = self.estado.inventario[nombre]
            if objeto.descripcion_inventario:
                return objeto.descripcion_inventario
            return objeto.descripcion

        return f"No encuentras nada especial sobre '{nombre}'."

  

    def _abrir(self, accion: Accion) -> str:
        if accion.objeto is None:
            return "¿Qué quieres abrir?"

        nombre = accion.objeto.nucleo

        if nombre == "puerta":
            if self.estado.sala_actual != "celda":
                return "No hay una puerta cerrada que puedas abrir aquí."

            if "llave" not in self.estado.inventario:
                return "La puerta está cerrada. Necesitas una llave."

            self.estado.banderas["puerta_celda_abierta"] = True

            # Desbloquea la conexión norte de la celda
            self.salas["celda"].conexiones["norte"].bloqueada = False

            return "Usas la llave oxidada y abres la puerta de la celda."

        if nombre == "cofre":
            if self.estado.sala_actual != "biblioteca":
                return "No ves ningún cofre aquí."

            if self.estado.banderas.get("cofre_abierto", False):
                return "El cofre ya está abierto."

            if "llave" not in self.estado.inventario:
                return "El cofre está cerrado. Parece necesitar una llave."

            self.estado.banderas["cofre_abierto"] = True

            pergamino = ObjetoMundo(
                nombre="pergamino",
                descripcion=(
                    "Un pergamino antiguo. Dice: 'Solo quien comprende las palabras "
                    "del encierro podrá abandonar la torre'."
                ),
                portable=True
            )

            self.salas["biblioteca"].objetos["pergamino"] = pergamino

            return "Abres el cofre con la llave. Dentro aparece un pergamino antiguo."

        if nombre == "libro":
            if "libro" not in self.estado.inventario and "libro" not in self.salas[self.estado.sala_actual].objetos:
                return "No ves ningún libro que puedas abrir."

            return (
                "Abres el libro antiguo. Sus páginas están escritas en un lenguaje antiguo "
                "que no puedes entender, así que no vale la pena intentar leerlo."
            )

        return f"No puedes abrir '{nombre}'."

    def _leer(self, accion: Accion) -> str:
        if accion.objeto is None:
            return "¿Qué quieres leer?"

        nombre = accion.objeto.nucleo

        if nombre == "pergamino":
            sala = self.salas[self.estado.sala_actual]

            tiene_pergamino = (
                "pergamino" in self.estado.inventario
                or "pergamino" in sala.objetos
            )

            if not tiene_pergamino:
                return "No tienes ningún pergamino para leer."

            #cuando se lea el pergamino, se activa la bandera y se desbloquea la conexion norte de la biblioteca
            self.estado.banderas["pergamino_leido"] = True
            self.salas["biblioteca"].conexiones["norte"].bloqueada = False

            return (
                "Lees el pergamino. Las palabras brillan por un instante. "
                "Sientes que el bloqueo mágico de la salida ha desaparecido."
            )

        if nombre == "libro":
            tiene_libro = (
                "libro" in self.estado.inventario
                or "libro" in self.salas[self.estado.sala_actual].objetos
            )

            if not tiene_libro:
                return "No ves ningún libro que puedas leer."

            return (
                "Intentas leer el libro, pero está escrito en un lenguaje antiguo "
                "que no puedes entender. No vale la pena seguir intentándolo."
            )

        if nombre == "etiqueta":
            if "llave" in self.estado.inventario:
                return "Lees la etiqueta de la llave: 'llave maestra'."

            if self.estado.sala_actual == "celda" and "llave" in self.salas["celda"].objetos:
                return "Lees la etiqueta que cuelga de la llave: 'llave maestra'."

            return "No ves ninguna etiqueta que puedas leer."

        return f"No puedes leer '{nombre}'."


    def _inventario(self) -> str:
        if not self.estado.inventario:
            return "Tu inventario está vacío."

        objetos = ", ".join(self.estado.inventario.keys())
        return f"Inventario: {objetos}."

    def _ayuda(self) -> str:
        return (
            "Puedes escribir comandos como: 'tomar la llave', 'abrir la puerta', "
            "'ir al norte', 'examinar la pared', 'leer el pergamino' o 'inventario'."
        )

    def _describir_sala(self) -> str:
        sala = self.salas[self.estado.sala_actual]
        texto = sala.descripcion

        #  descripciones por cada sala, depende si el objeto sigue en la sala o si ya se tomó, etc
        if sala.nombre == "celda":
            if "llave" in sala.objetos:
                texto += (
                    "\nEn una esquina hay un cadáver apoyado contra la pared. "
                    "En una de sus manos se encuentra una llave con una etiqueta que dice: 'llave maestra'."
                )
            else:
                texto += (
                    "\nEn una esquina hay un cadáver apoyado contra la pared. "
                    "Su mano está vacía; ya tomaste la llave que sostenía."
                )

            if self.estado.banderas.get("puerta_celda_abierta", False):
                texto += "\nLa puerta de la celda está abierta hacia el norte."
            else:
                texto += "\nLa puerta de la celda está cerrada hacia el norte."

        elif sala.nombre == "pasillo":
            if "antorcha" in sala.objetos:
                texto += "\nUna antorcha encendida está fijada a la pared."
            elif "antorcha" in self.estado.inventario:
                texto += "\nEn la pared queda el soporte vacío donde antes estaba la antorcha."

        elif sala.nombre == "biblioteca":
            if "libro" in sala.objetos:
                texto += "\nUn libro antiguo descansa sobre uno de los estantes."
            elif "libro" in self.estado.inventario:
                texto += "\nEn el estante queda un espacio vacío donde antes estaba el libro."

            if self.estado.banderas.get("cofre_abierto", False):
                texto += "\nEl cofre está abierto sobre la mesa."
            else:
                texto += "\nSobre la mesa hay un cofre cerrado."

        # Objetos visibles restantes
        objetos_visibles = [
            obj.nombre
            for obj in sala.objetos.values()
            # se ignora la puerta y cadaver, porque ya se describen a detalle en cada sala
            if obj.visible and obj.nombre not in {"puerta", "cadaver"}
        ]

        if objetos_visibles:
            texto += "\nVes aquí: " + ", ".join(objetos_visibles) + "."

        if sala.conexiones:
            texto += "\nSalidas: " + ", ".join(sala.conexiones.keys()) + "."

        return texto

    def _extraer_direccion(self, complemento: Complemento | None) -> str | None:
        if complemento is None:
            return None

        if complemento.rol == "direccion" and isinstance(complemento.valor, str):
            return complemento.valor

        if complemento.rol == "destino" and isinstance(complemento.valor, str):
            return complemento.valor

        return None

    def estado_actual(self) -> str:
        return self._describir_sala()