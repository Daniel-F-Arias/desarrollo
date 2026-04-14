from django.db import models
from django.contrib.auth.models import User
from productos.models import Producto  
from decimal import Decimal

class Carrito(models.Model):
    usuario = models.OneToOneField("auth.User", on_delete=models.CASCADE)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_con_iva(self):
        return sum(item.total_con_iva for item in self.items.all())


class CarritoItem(models.Model):
    carrito = models.ForeignKey("Carrito", related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey("productos.Producto", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    @property
    def iva(self):
        return self.subtotal * Decimal("0.19")  

    @property
    def total_con_iva(self):
        return self.subtotal + self.iva
