from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from productos.models import Producto
from .forms import CrearUsuarioForm
from django.urls import reverse
from usuarios.utils import registrar_accion

#Activar entorno virtual: venv\Scripts\activate.bat

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            registrar_accion(user, "Inicio de sesión")
            if user.is_superuser:
                return redirect('admin_home')
            else:
                return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, 'usuarios/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        registrar_accion(request.user,"Cierre de sesión")
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login')

@login_required
def home(request):
    productos = Producto.objects.all()
    return render(request, 'usuarios/home.html', {'productos': productos})

def register_view(request):
    if request.method == "POST":
        identificacion = request.POST['identificacion']  
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            usuario_inactivo = User.objects.filter(username=username, is_active=False).first() \
                               or User.objects.filter(email=email, is_active=False).first()
            if usuario_inactivo:
                # Reactivar usuario
                usuario_inactivo.username = username
                usuario_inactivo.email = email
                usuario_inactivo.set_password(password1)
                usuario_inactivo.first_name = identificacion
                usuario_inactivo.is_active = True
                usuario_inactivo.save()
                messages.success(request, "Cuenta reactivada exitosamente.")
                return redirect('login')
            
            elif User.objects.filter(email=email, is_active=True).exists():
                messages.error(request, "El email ya está registrado")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                user.first_name = identificacion  
                user.is_active = True   # por si acaso
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
        nueva_identificacion = request.POST.get('identificacion', '').strip()
        nuevo_usuario = request.POST.get('username', '').strip()
        nuevo_email = request.POST.get('email', '').strip()
        nueva_pass1 = request.POST.get('password1', '').strip()
        nueva_pass2 = request.POST.get('password2', '').strip()

        if nueva_identificacion:
            usuario.first_name = nueva_identificacion  

        if nuevo_usuario:
            if User.objects.filter(username=nuevo_usuario).exclude(pk=usuario.pk).exists():
                messages.error(request, "Ese nombre de usuario ya está en uso.")
                return redirect('editar_usuario', user_id=usuario.id)
            usuario.username = nuevo_usuario

        if nuevo_email:
            if User.objects.filter(email=nuevo_email, is_active=True).exclude(pk=usuario.pk).exists():
                messages.error(request, "Ese email ya está en uso.")
                return redirect('editar_usuario', user_id=usuario.id)
            usuario.email = nuevo_email

        if nueva_pass1 or nueva_pass2:
            if nueva_pass1 == nueva_pass2:
                usuario.set_password(nueva_pass1)
                usuario.save()
                messages.success(request, "Contraseña actualizada. Por favor, inicia sesión nuevamente.")
                return redirect('login')
            else:
                messages.error(request, "Las contraseñas no coinciden.")
                return redirect('editar_usuario', user_id=usuario.id)

        usuario.save()
        registrar_accion(request.user, "Actualizó su perfil", f"Usuario: {usuario.username}")
        messages.success(request, "Los datos fueron actualizados correctamente.")
    
        if request.user.is_superuser:
            return redirect('admin_home')
        else:
            return redirect('home')  

    else:
        es_admin = request.user.is_superuser
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
        messages.error(request, "No tienes permiso para desactivar este usuario.")
        return redirect('home')

    if request.method == "POST":
        es_mismo_usuario = request.user == user
        user.is_active = False  
        user.save()
        registrar_accion(request.user, "Desactivó una cuenta", f"Usuario afectado: {user.username}")
        messages.success(request, "Cuenta desactivada correctamente.")

        # si el propio usuario se desactiva, lo sacamos de la sesión
        if es_mismo_usuario:
            logout(request)
            return redirect('login')
        else:
            return redirect('lista_usuarios')

    # 👇 Definir correctamente el destino al cancelar
    if request.user == user:
        destino_cancelar = 'admin_home' if request.user.is_superuser else 'home'
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
    
    
@user_passes_test(lambda u: u.is_superuser)
def ver_acciones(request):
    from .models import AccionUsuario
    acciones = AccionUsuario.objects.select_related("usuario").order_by("-fecha")
    return render(request, "usuarios/ver_acciones.html", {"acciones": acciones})

