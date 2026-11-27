"""
Clase de dominio para las membresías del gimnasio.

Implementa POO: encapsulamiento con @property (precio, días restantes,
estado), métodos de negocio (esta_vigente, renovar) y sobrescritura de
operadores (__str__, __eq__, __lt__, __hash__) para comparar y ordenar
membresías de forma natural.
"""

from datetime import date, timedelta


class Membresia:
    """Representa una suscripción de un cliente a un plan del gimnasio."""

    ESTADOS = ("ACTIVE", "EXPIRED", "CANCELLED")

    def __init__(self, cliente, plan, precio, fecha_inicio, fecha_fin,
                 estado="ACTIVE", membresia_id=None):
        self.cliente = cliente            # Miembro (core.persona) o str
        self.plan = plan                  # nombre del plan (str)
        self.membresia_id = membresia_id
        self.fecha_inicio = fecha_inicio  # datetime.date
        self.fecha_fin = fecha_fin        # datetime.date
        self.precio = precio              # pasa por el setter (>= 0)
        self.estado = estado              # pasa por el setter (enum)

    # ── Getters y setters (encapsulamiento) ──────────────────────────────

    @property
    def precio(self):
        return self._precio

    @precio.setter
    def precio(self, valor):
        valor = float(valor)
        if valor < 0:
            raise ValueError("El precio de la membresía no puede ser negativo.")
        self._precio = valor

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

    @property
    def dias_restantes(self):
        """Días que faltan para el vencimiento. Nunca negativo."""
        return max(0, (self.fecha_fin - date.today()).days)

    # ── Métodos de negocio ───────────────────────────────────────────────

    def esta_vigente(self):
        return self.estado == "ACTIVE" and self.fecha_fin >= date.today()

    def renovar(self, dias, nuevo_precio=None):
        """Extiende la membresía `dias` días a partir de su fin actual."""
        if dias <= 0:
            raise ValueError("Los días de renovación deben ser positivos.")
        base = max(self.fecha_fin, date.today())
        self.fecha_fin = base + timedelta(days=dias)
        if nuevo_precio is not None:
            self.precio = nuevo_precio
        self.estado = "ACTIVE"

    # ── Sobrescritura de operadores ──────────────────────────────────────

    def __str__(self):
        return (
            f"Membresía: {self._cliente_nombre()} — {self.plan} "
            f"(vence {self.fecha_fin}, {self.estado})"
        )

    def __eq__(self, otro):
        if not isinstance(otro, Membresia):
            return NotImplemented
        return (
            self._cliente_key() == otro._cliente_key()
            and self.plan == otro.plan
            and self.fecha_inicio == otro.fecha_inicio
        )

    def __lt__(self, otro):
        if not isinstance(otro, Membresia):
            return NotImplemented
        return self.fecha_fin < otro.fecha_fin

    def __hash__(self):
        return hash((self._cliente_key(), self.plan, self.fecha_inicio))

    # ── Utilidades ───────────────────────────────────────────────────────

    def _cliente_key(self):
        """Identificador estable del cliente para comparar membresías."""
        if hasattr(self.cliente, "codigo_qr"):
            return self.cliente.codigo_qr
        return str(self.cliente)

    def _cliente_nombre(self):
        """Nombre legible del cliente para la representación textual."""
        if hasattr(self.cliente, "nombre_completo"):
            return self.cliente.nombre_completo
        return str(self.cliente)

    @classmethod
    def from_model(cls, membership):
        """
        Construye una Membresia de dominio a partir del modelo Django
        `memberships.Membership` (con member y plan ya cargados).
        """
        from core.persona import Miembro

        member = membership.member
        cliente = Miembro(
            nombre=member.first_name,
            apellido=member.last_name,
            email=member.email,
            telefono=member.phone,
            entidad_id=member.id,
            estado=member.status,
            membresia_vigente=membership.is_valid,
        )
        return cls(
            cliente=cliente,
            plan=membership.plan.name,
            precio=membership.plan.price,
            fecha_inicio=membership.start_date,
            fecha_fin=membership.end_date,
            estado=membership.status,
            membresia_id=membership.id,
        )
