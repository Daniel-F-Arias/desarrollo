from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from carrito.models import Carrito
from .models import Factura, DetalleFactura
import uuid
from usuarios.utils import registrar_accion

@login_required
def previsualizar_factura(request):
    carrito = Carrito.objects.filter(usuario=request.user).first()
    if not carrito or not carrito.items.exists():
        messages.error(request, "Tu carrito está vacío. No se puede generar una factura.")
        return redirect("ver_carrito")

    total_sin_iva = carrito.total
    total_con_iva = carrito.total_con_iva
    iva_total = total_con_iva - total_sin_iva

    contexto = {
        "usuario": request.user,
        "carrito": carrito,
        "fecha": datetime.now(),
        "total_sin_iva": total_sin_iva,
        "iva_total": iva_total,
        "total_con_iva": total_con_iva,
    }
    return render(request, "facturas/previsualizar_factura.html", contexto)



@login_required
def generar_factura(request):
    # Obtener carrito
    carrito = Carrito.objects.filter(usuario=request.user).first()
    if not carrito or not carrito.items.exists():
        messages.error(request, "El carrito está vacío, no se puede generar la factura.")
        return redirect("ver_carrito")

    # --------------------
    # Datos fijos / inventados del vendedor / impresor (puedes cambiarlos)
    # --------------------
    VENDEDOR_RAZON = "Austral Coffee S.A.S."
    VENDEDOR_NIT = "900.000.000-0"
    VENDEDOR_DIRECCION = "Calle 72e #3bn43"
    VENDEDOR_TELEFONO = "(300) 750 5911"
    VENDEDOR_EMAIL = "brayancr221@gmail.com"
    REGIMEN = "Régimen: Común"
    IMPRESOR_NOMBRE = "Imprenta CaféPrint S.A.S."
    IMPRESOR_NIT = "900.654.321-5"
    RESOLUCION = "Resolución 000042 de 2020"
    FORMA_PAGO = "Contado"

    # --------------------
    # Totales y IVA (usar Decimal para dinero)
    # --------------------
    # Si carrito.total y carrito.total_con_iva ya son Decimal, ok; si no, convertimos.
    total_sin_iva = Decimal(carrito.total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_con_iva = Decimal(carrito.total_con_iva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva_total = (total_con_iva - total_sin_iva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # --------------------
    # Crear registro Factura en BD (usa números que la BD genera)
    # --------------------
    factura = Factura.objects.create(
        usuario=request.user,
        total=total_sin_iva,
        total_con_iva=total_con_iva
    )
    
    registrar_accion(request.user, "Generó una factura", f"Factura FV-{factura.id:06d}")

    # --------------------
    # Crear detalles (guardamos FK al producto)
    # --------------------
    for item in carrito.items.all():
        precio_unit = Decimal(item.producto.precio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva_item = (Decimal(item.iva) if getattr(item, "iva", None) is not None else Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_item = Decimal(item.total_con_iva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        DetalleFactura.objects.create(
            factura=factura,
            producto=item.producto,                # FK
            cantidad=item.cantidad,
            precio_unitario=precio_unit,
            iva=iva_item,
            total=total_item
        )

    # --------------------
    # Generar CUFE simulado
    # --------------------
    cufe_simulado = str(uuid.uuid4())

    # --------------------
    # Generar PDF en memoria
    # --------------------
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Función auxiliar para nueva página si se acaba el espacio
    def check_newpage(y_pos):
        if y_pos < 120:  # margen inferior
            p.showPage()
            return height - 80  # nueva y
        return y_pos

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 50, "Factura de venta")

    # Metadatos (número, fecha, forma de pago)
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 80, f"Número de factura: FV-{factura.id:06d}")
    p.drawString(40, height - 95, f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(40, height - 110, f"Forma de pago: {FORMA_PAGO}")

    # Datos vendedor (lado derecho)
    p.drawString(320, height - 80, "Vendedor:")
    p.setFont("Helvetica", 9)
    p.drawString(320, height - 95, f"{VENDEDOR_RAZON} - NIT: {VENDEDOR_NIT}")
    p.drawString(320, height - 110, f"NIT: {VENDEDOR_NIT}")
    p.drawString(320, height - 125, f"{VENDEDOR_DIRECCION}")
    p.drawString(320, height - 140, f"Tel: {VENDEDOR_TELEFONO}")
    p.drawString(320, height - 155, f"Email: {VENDEDOR_EMAIL}")
    p.drawString(320, height - 170, REGIMEN)

    # Datos comprador
    y = height - 170
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Datos del comprador:")
    p.setFont("Helvetica", 10)
    y -= 15
    comprador_nombre = request.user.username or "Cliente Final"
    comprador_id = request.user.first_name or str(request.user.id)  # usas first_name como identificacion si guardaste ahí
    p.drawString(40, y, f"Nombre: {comprador_nombre}")
    y -= 12
    p.drawString(40, y, f"CC: {comprador_id}")

    # Tabla encabezados
    y -= 28
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Cant.")
    p.drawString(80, y, "Descripción")
    p.drawRightString(360, y, "P. Unitario")
    p.drawRightString(450, y, "IVA")
    p.drawRightString(540, y, "Total")

    # Filas de productos
    p.setFont("Helvetica", 10)
    y -= 18
    for item in carrito.items.all():
        # crear nueva página si hace falta
        y = check_newpage(y)

        precio_unit = Decimal(item.producto.precio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva_item = (Decimal(item.iva) if getattr(item, "iva", None) is not None else Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_item = Decimal(item.total_con_iva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        p.drawString(40, y, str(item.cantidad))
        # descripcion acotada si muy larga
        descripcion = item.producto.nombre
        if len(descripcion) > 40:
            descripcion = descripcion[:37] + "..."
        p.drawString(80, y, descripcion)
        p.drawRightString(360, y, f"${precio_unit:,.2f}")
        p.drawRightString(450, y, f"${iva_item:,.2f}")
        p.drawRightString(540, y, f"${total_item:,.2f}")
        y -= 18

    # Totales al final (derecha)
    y -= 12
    y = check_newpage(y)
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(480, y, "Subtotal:")
    p.drawRightString(550, y, f"${total_sin_iva:,.2f}")
    y -= 16
    p.drawRightString(480, y, "IVA:")
    p.drawRightString(550, y, f"${iva_total:,.2f}")
    y -= 16
    p.drawRightString(480, y, "Total a pagar:")
    p.drawRightString(550, y, f"${total_con_iva:,.2f}")

    # Info de impresor, CUFE y notas legales (abajo)
    y -= 36
    y = check_newpage(y)
    p.setFont("Helvetica", 9)
    p.drawString(40, y, f"Impresor autorizado: {IMPRESOR_NOMBRE} - NIT: {IMPRESOR_NIT}")
    y -= 12
    p.drawString(40, y, f"CUFE (simulado): {cufe_simulado}")
    y -= 12
    p.drawString(40, y, f"Resolución: {RESOLUCION}")
    y -= 12
    p.drawString(40, y, "Notas: Documento generado en modo demo. No es válido fiscalmente.")
    y -= 12
    p.drawString(40, y, "Firma digital: Firma simulada Austral Coffee S.A.S.")
    y -= 12

    # Finalizar PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Vaciar carrito (si quieres conservarlo, comenta esta línea)
    carrito.items.all().delete()

    # Devolver PDF
    filename = f"FV-{factura.id:06d}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)
