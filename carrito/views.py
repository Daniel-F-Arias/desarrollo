from django.shortcuts import render, redirect, get_object_or_404
from .models import Carrito, CarritoItem
from productos.models import Producto
from django.contrib import messages

def ver_carrito(request):
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, "carrito.html", {"carrito": carrito})


def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    item, creado = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)
    if not creado:
        item.cantidad += 1
    item.save()

    # Mensaje de confirmación
    messages.success(request, f"{producto.nombre} fue agregado al carrito 🛒")

    # Redirigir a la misma página desde la que vino el usuario
    return redirect(request.META.get("HTTP_REFERER", "ver_carrito"))


def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    item.delete()
    return redirect("ver_carrito")
