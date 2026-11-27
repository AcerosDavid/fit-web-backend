"""
Clases de dominio para las personas del gimnasio.

Jerarquía:
    Persona          -> atributos y comportamiento comunes
    ├── Miembro      -> cliente del gimnasio (prefijo QR "M")
    └── Entrenador   -> coach del gimnasio (prefijo QR "C")

Implementa POO: encapsulamiento con @property (getters/setters con
validación), herencia y sobrescritura de métodos.
"""

import re


class Persona:
    """Clase base: datos comunes de cualquier persona del gimnasio."""

    prefijo_qr = "P"
    tipo_persona = "Persona"
    MAX_TELEFONO = 20

    _EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, nombre, apellido, email, telefono="", entidad_id=None):
        self.nombre = nombre
        self.apellido = apellido
        self.entidad_id = entidad_id
        self.email = email          # pasa por el setter (valida formato)
        self.telefono = telefono    # pasa por el setter (valida longitud)

    # ── Getters y setters (encapsulamiento) ──────────────────────────────

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        valor = (valor or "").strip()
        if valor and not self._EMAIL_REGEX.match(valor):
            raise ValueError(f"Email inválido: '{valor}'")
        self._email = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        valor = (valor or "").strip()
        if len(valor) > self.MAX_TELEFONO:
            raise ValueError(
                f"El teléfono no puede superar {self.MAX_TELEFONO} caracteres."
            )
        self._telefono = valor

    # ── Comportamiento ───────────────────────────────────────────────────

    @property
    def codigo_qr(self):
        """Código que se codifica en el QR de acceso (FIT-<prefijo>-<id>)."""
        return f"FIT-{self.prefijo_qr}-{self.entidad_id}"

    def tipo(self):
        """Descripción del rol de la persona. Se sobrescribe en las hijas."""
        return self.tipo_persona

    def descripcion(self):
        return f"{self.tipo()}: {self.nombre_completo} ({self.codigo_qr})"

    def registrar_asistencia(self, accion, momento):
        """Devuelve el evento de asistencia en formato de diccionario."""
        return {
            "tipo": self.tipo(),
            "qr_code": self.codigo_qr,
            "nombre": self.nombre_completo,
            "accion": accion,
            "momento": momento.isoformat(),
        }


class _PersonaModelMixin:
    """Permite construir la persona de dominio desde un modelo de Django."""

    @classmethod
    def from_model(cls, obj):
        raise NotImplementedError


class Miembro(Persona, _PersonaModelMixin):
    """Cliente del gimnasio. Hereda de Persona y agrega su estado."""

    prefijo_qr = "M"
    tipo_persona = "Cliente"

    ESTADOS = ("ACTIVE", "INACTIVE", "SUSPENDED")

    def __init__(self, nombre, apellido, email, telefono="",
                 entidad_id=None, estado="ACTIVE", membresia_vigente=False):
        super().__init__(nombre, apellido, email, telefono, entidad_id)
        self.estado = estado
        self.membresia_vigente = membresia_vigente

    @classmethod
    def from_model(cls, member):
        """Construye un Miembro de dominio desde `members.Member`."""
        return cls(
            nombre=member.first_name,
            apellido=member.last_name,
            email=member.email,
            telefono=member.phone,
            entidad_id=member.id,
            estado=member.status,
        )

    @property
    def estado(self):
        return self._estado

    @estado.setter
    def estado(self, valor):
        valor = (valor or "ACTIVE").upper()
        if valor not in self.ESTADOS:
            raise ValueError(
                f"Estado inválido: '{valor}'. Válidos: {', '.join(self.ESTADOS)}"
            )
        self._estado = valor

    def esta_activo(self):
        return self.estado == "ACTIVE"

    def puede_firmar_membresia(self):
        """Solo un cliente activo puede contratar o renovar membresía."""
        return self.esta_activo()


class Entrenador(Persona, _PersonaModelMixin):
    """Entrenador del gimnasio. Hereda de Persona y agrega especialidad."""

    prefijo_qr = "C"
    tipo_persona = "Entrenador"

    def __init__(self, nombre, apellido, email, telefono="",
                 entidad_id=None, especialidad="", activo=True):
        super().__init__(nombre, apellido, email, telefono, entidad_id)
        self.especialidad = especialidad
        self.activo = activo

    @classmethod
    def from_model(cls, coach):
        """Construye un Entrenador de dominio desde `coaches.Coach`."""
        user = getattr(coach, "user", None)
        return cls(
            nombre=coach.first_name,
            apellido=coach.last_name,
            email=user.email if user else "",
            telefono=coach.phone,
            entidad_id=coach.id,
            especialidad=coach.specialty,
            activo=coach.is_active,
        )

    def descripcion(self):
        base = super().descripcion()
        return f"{base} [{self.especialidad}]" if self.especialidad else base
