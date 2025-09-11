from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto
from .forms import ProductoForm
from django.contrib.auth.decorators import login_required, user_passes_test

# Vista pública
#def lista_productos(request):
#    productos = Producto.objects.all()
#    return render(request, 'productos/lista.html', {'productos': productos})


def listar_productos(request):
    productos = Producto.objects.all()
    return render(request, 'productos/lista.html', {'productos': productos})

# Solo admins
def es_admin(user):
    return user.is_superuser

@user_passes_test(es_admin)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')  # Cambia según tu URL
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_producto.html', {'form': form})


@user_passes_test(es_admin)
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/formulario.html', {'form': form, 'accion': 'Editar'})

@user_passes_test(es_admin)

def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    return redirect('listar_productos')

