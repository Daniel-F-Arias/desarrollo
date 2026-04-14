from django.shortcuts import render, redirect, get_object_or_404
from .models import Carrito, CarritoItem
from productos.models import Producto
from django.contrib import messages
import io
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from usuarios.utils import registrar_accion


def ver_carrito(request):
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, "carrito.html", {"carrito": carrito})


def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)

    # 🔹 Obtener la cantidad desde el formulario, si no hay usar 1
    cantidad = int(request.POST.get("cantidad", 1))

    # Buscar si el producto ya estaba en el carrito
    item, creado = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)

    if creado:
        item.cantidad = cantidad
    else:
        item.cantidad += cantidad  # sumamos a lo que ya tenía
    registrar_accion(request.user, "Agregó producto al carrito", f"{producto.nombre} x{cantidad}")
    item.save()

    # Mensaje de confirmación
    messages.success(request, f"Se agregaron {cantidad} unidad(es) de {producto.nombre} al carrito 🛒")

    # Redirigir a la misma página
    return redirect(request.META.get("HTTP_REFERER", "ver_carrito"))


def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)

    if request.method == "POST":
        cantidad_a_eliminar = int(request.POST.get("cantidad", 1))

        if cantidad_a_eliminar >= item.cantidad:
            
            item.delete()
            registrar_accion(request.user, "Eliminó producto del carrito", f"{item.producto.nombre}")
        else:
            item.cantidad -= cantidad_a_eliminar
            item.save()

    return redirect('ver_carrito')
