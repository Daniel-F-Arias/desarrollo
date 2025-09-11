from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Q
from productos.models import Producto
from .forms import CrearUsuarioForm
from django.urls import reverse

#Activar entorno virtual: venv\Scripts\activate.bat

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_home')
            else:
                return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirige a la página de login

@login_required
def home(request):
    productos = Producto.objects.all()
    return render(request, 'usuarios/home.html', {'productos': productos})

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, "El usuario ya existe")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "El email ya está registrado")
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                messages.success(request, "Cuenta creada exitosamente.")
                return redirect('login')
        else:
            messages.error(request, "Las contraseñas no coinciden")

    return render(request, 'usuarios/register.html')


def es_admin(user):
    return user.is_superuser


@login_required
def actualizar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    # Solo el propio usuario o el administrador puede editar
    if request.user != usuario and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar esta cuenta.")
        return redirect('home')

    if request.method == 'POST':
        nuevo_usuario = request.POST.get('username', '').strip()
        nuevo_email = request.POST.get('email', '').strip()
        nueva_pass1 = request.POST.get('password1', '').strip()
        nueva_pass2 = request.POST.get('password2', '').strip()

        if nuevo_usuario:
            usuario.username = nuevo_usuario

        if nuevo_email:
            usuario.email = nuevo_email

        if nueva_pass1 or nueva_pass2:
            if nueva_pass1 == nueva_pass2:
                usuario.set_password(nueva_pass1)
                messages.success(request, "Contraseña actualizada. Por favor, inicia sesión nuevamente.")
                usuario.save()
                return redirect('login')
            else:
                messages.error(request, "Las contraseñas no coinciden.")
                return redirect('editar_usuario', user_id=usuario.id)

        usuario.save()
        messages.success(request, "Los datos fueron actualizados correctamente.")
    
        if request.user.is_superuser:
            return redirect('admin_home')
        else:
            return redirect('home')  

    else:
        es_admin = request.user.is_superuser
        # Captura la URL de donde vino el usuario, por si quiere cancelar
        volver_url = request.META.get('HTTP_REFERER', reverse('home'))

        return render(request, 'usuarios/editar_usuario.html', {
            'usuario': usuario,
            'es_admin': es_admin,
            'volver_url': volver_url
        })




# ❌ Eliminar cuenta
@login_required
def eliminar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user != user and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para eliminar este usuario.")
        return redirect('home')

    if request.method == "POST":
        es_mismo_usuario = request.user == user
        user.delete()
        messages.success(request, "Cuenta eliminada correctamente.")
        return redirect('login' if es_mismo_usuario else 'lista_usuarios')

    # 👇 Definir correctamente el destino al cancelar
    if request.user == user:
        if request.user.is_superuser:
            destino_cancelar = 'admin_home'  # ⚠️ si el admin cancela eliminarse a sí mismo
        else:
            destino_cancelar = 'home'
    else:
        destino_cancelar = 'lista_usuarios'

    return render(request, 'usuarios/eliminar_usuario.html', {
        'usuario': user,
        'destino_cancelar': destino_cancelar
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def lista_usuarios(request):
    usuarios = User.objects.all()
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('lista_usuarios')
        else:
            messages.error(request, "Hubo un error al crear el usuario.")

    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'form': form
    })


def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado exitosamente.")
            return redirect('lista_usuarios')
    else:
        form = CrearUsuarioForm()
    return render(request, 'usuarios/crear_usuario.html', {'form': form})

@login_required
def admin_home(request):
    if request.user.is_superuser:  # Solo para administradores
        return render(request, 'usuarios/admin_home.html')
    else:
        return redirect('home')  # Si no es admin, va a la página normal
    
    

