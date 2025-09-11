from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    #path('', views.lista_productos, name='inicio_productos'), 
    path('productos/', views.listar_productos, name='listar_productos'),   
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
