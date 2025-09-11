from django.urls import path, include
from .views import login_view, logout_view, home, actualizar_usuario, eliminar_usuario,register_view, lista_usuarios, admin_home,crear_usuario


urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),  # Nueva ruta de registro
    path('home/', home, name='home'),
    path('editar/<int:user_id>/', actualizar_usuario, name='editar_usuario'),
    path('eliminar/<int:user_id>/', eliminar_usuario, name='eliminar_usuario'),
    path('lista/', lista_usuarios, name='lista_usuarios'),
    path('admin_home/', admin_home, name='admin_home'),
    path('productos/', include('productos.urls')),
    path('crear/', crear_usuario, name='crear_usuario'),

]


