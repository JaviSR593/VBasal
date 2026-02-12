# -*- coding: utf-8 -*-
"""
Created on Wed Feb 11 23:58:57 2026

@author: HP
"""

import flet as ft
import time

def main(page: ft.Page):
    # --- 1. CONFIGURACIÓN INICIAL ---
    page.title = "VBasal"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F172A" # Color de fondo azul oscuro
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ==========================================
    #   DEFINICIÓN DE LA APP PRINCIPAL
    # ==========================================
    
    # Variables de estado
    datos = {"R1_con": [], "R8_con": [], "R1_sin": [], "R8_sin": []}
    estado_carga = {"R1_con": False, "R8_con": False, "R1_sin": False, "R8_sin": False}

    # --- FUNCIONES LÓGICAS ---
    def procesar_archivo(e: ft.FilePickerResultEvent, clave, btn, txt):
        """Lee el archivo seleccionado y guarda los datos."""
        if e.files:
            try:
                path = e.files[0].path
                vals = []
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Ignorar líneas vacías o comentarios
                        if not line or line.startswith(('%', '#')): continue
                        parts = line.split()
                        # Asumimos que la fuerza está en la segunda columna (índice 1)
                        if len(parts) >= 2:
                            try: vals.append(float(parts[1]))
                            except: pass
                
                datos[clave] = vals
                estado_carga[clave] = True
                
                # Actualizar interfaz
                btn.icon = ft.icons.CHECK_CIRCLE
                btn.icon_color = ft.colors.GREEN_400
                txt.value = e.files[0].name
                txt.color = ft.colors.GREEN_400
                page.update()
            except Exception as ex:
                txt.value = "Error al leer archivo"
                txt.color = ft.colors.RED_400
                page.update()

    def calcular(e):
        """Realiza los cálculos y actualiza la gráfica."""
        try:
            # Verificar que todos los archivos estén cargados
            if not all(estado_carga.values()):
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ Por favor, carga los 4 archivos."), bgcolor=ft.colors.ORANGE_600)
                page.snack_bar.open = True
                page.update()
                return

            r1c, r8c = datos["R1_con"], datos["R8_con"]
            r1s, r8s = datos["R1_sin"], datos["R8_sin"]
            
            # Validación de datos vacíos
            if not r1c or not r8c or not r1s or not r8s:
                 page.snack_bar = ft.SnackBar(ft.Text("Error: Uno o más archivos están vacíos o son inválidos."), bgcolor=ft.colors.RED_600)
                 page.snack_bar.open = True
                 page.update()
                 return

            # Encontrar la longitud mínima para evitar errores de índice
            n = min(len(r1c), len(r8c), len(r1s), len(r8s))
            
            # Cálculos de Cortante Basal (Suma / 1000 para kN)
            Vb_con = [(r1c[i] + r8c[i]) / 1000.0 for i in range(n)]
            Vb_sin = [(r1s[i] + r8s[i]) / 1000.0 for i in range(n)]
            
            # Máximos absolutos
            max_con = max([abs(x) for x in Vb_con])
            max_sin = max([abs(x) for x in Vb_sin])

            # Preparar datos para el gráfico
            dt = 0.02 # Paso de tiempo asumido
            # Muestreo para no saturar el gráfico si hay muchos puntos
            step = int(n/300) if n > 1000 else 1
            
            pts_con = [ft.LineChartDataPoint(i*dt, Vb_con[i]) for i in range(0, n, step)]
            pts_sin = [ft.LineChartDataPoint(i*dt, Vb_sin[i]) for i in range(0, n, step)]

            # Configurar series del gráfico
            chart.data_series = [
                ft.LineChartData(pts_sin, color=ft.colors.CYAN_400, stroke_width=2, curved=True, stroke_cap_round=True),
                ft.LineChartData(pts_con, color=ft.colors.PINK_400, stroke_width=2, curved=True, stroke_cap_round=True)
            ]
            
            # Ajustar escalas del gráfico
            max_v = max(max_con, max_sin) * 1.1 if max_con > 0 else 10
            chart.max_y = max_v
            chart.min_y = -max_v
            chart.max_x = n * dt
            
            # Actualizar resultados numéricos
            lbl_con.value = f"{max_con:.2f} kN"
            lbl_sin.value = f"{max_sin:.2f} kN"
            
            # Mostrar el contenedor de la gráfica
            cont_grafico.visible = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error en el cálculo: {ex}"), bgcolor=ft.colors.RED_600)
            page.snack_bar.open = True
            page.update()

    # --- COMPONENTES DE LA INTERFAZ ---
    
    # File Pickers
    fp_1c = ft.FilePicker(on_result=lambda e: procesar_archivo(e, "R1_con", b1c, t1c))
    fp_8c = ft.FilePicker(on_result=lambda e: procesar_archivo(e, "R8_con", b8c, t8c))
    fp_1s = ft.FilePicker(on_result=lambda e: procesar_archivo(e, "R1_sin", b1s, t1s))
    fp_8s = ft.FilePicker(on_result=lambda e: procesar_archivo(e, "R8_sin", b8s, t8s))
    page.overlay.extend([fp_1c, fp_8c, fp_1s, fp_8s])

    # Función para crear una fila de carga de archivo
    def crear_fila(txt, picker, col):
        b = ft.IconButton(ft.icons.UPLOAD_FILE_ROUNDED, icon_color=col, on_click=lambda _: picker.pick_files())
        t = ft.Text("Seleccionar archivo...", size=11, color=ft.colors.GREY_400, width=140, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)
        return b, t, ft.Row([
            b,
            ft.Column([
                ft.Text(txt, size=13, weight="bold"),
                t
            ], spacing=2)
        ], alignment="start", vertical_alignment="center")

    # Crear las 4 filas de carga con textos actualizados
    b1c, t1c, r1c = crear_fila("Nodo 1 (Con Damper)", fp_1c, ft.colors.PINK_300)
    b8c, t8c, r8c = crear_fila("Nodo 8 (Con Damper)", fp_8c, ft.colors.PINK_300)
    b1s, t1s, r1s = crear_fila("Nodo 1 (Sin Damper)", fp_1s, ft.colors.CYAN_300)
    b8s, t8s, r8s = crear_fila("Nodo 8 (Sin Damper)", fp_8s, ft.colors.CYAN_300)

    # Gráfico vacío inicial
    chart = ft.LineChart(
        data_series=[],
        min_y=-100, max_y=100,
        expand=True,
        border=ft.border.all(1, ft.colors.WHITE10),
        left_axis=ft.ChartAxis(labels_size=35, title=ft.Text("Fuerza (kN)", size=10)),
        bottom_axis=ft.ChartAxis(labels_size=35, title=ft.Text("Tiempo (s)", size=10)),
        tooltip_bgcolor=ft.colors.with_opacity(0.9, ft.colors.BLACK)
    )
    
    # Etiquetas para resultados numéricos
    lbl_con = ft.Text("-", color=ft.colors.PINK_300, size=22, weight="bold", font_family="monospace")
    lbl_sin = ft.Text("-", color=ft.colors.CYAN_300, size=22, weight="bold", font_family="monospace")

    # Leyenda personalizada para la gráfica
    leyenda_grafica = ft.Row([
        ft.Row([ft.Icon(ft.icons.CIRCLE, color=ft.colors.CYAN_400, size=12), ft.Text("Sin Damper", size=12)], spacing=5),
        ft.Row([ft.Icon(ft.icons.CIRCLE, color=ft.colors.PINK_400, size=12), ft.Text("Con Damper", size=12)], spacing=5),
    ], alignment="center", spacing=20)

    # Contenedor de la gráfica y resultados (inicialmente oculto)
    cont_grafico = ft.Container(
        visible=False,
        content=ft.Column([
            # Título de la gráfica
            ft.Text("Comparación de cortante Basal (Vb)", size=18, weight="bold", text_align="center"),
            ft.Container(height=10),
            # Gráfica
            ft.Container(chart, height=250, border=ft.border.all(1, ft.colors.WHITE12), padding=10, border_radius=12, bgcolor=ft.colors.BLACK12),
            ft.Container(height=15),
            # Leyenda
            leyenda_grafica,
            ft.Container(height=15),
            # Resultados Numéricos
            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text("Max Con Damper", color=ft.colors.PINK_200, size=12), lbl_con], horizontal_alignment="center"),
                    ft.Container(width=1, height=40, bgcolor=ft.colors.WHITE24), # Divisor vertical
                    ft.Column([ft.Text("Max Sin Damper", color=ft.colors.CYAN_200, size=12), lbl_sin], horizontal_alignment="center")
                ], alignment="spaceEvenly"),
                bgcolor=ft.colors.WHITE10, padding=15, border_radius=12
            )
        ], horizontal_alignment="center")
    )

    # Estructura principal de la interfaz
    interfaz_principal = ft.Column([
        # 1. Título Principal Centrado
        ft.Container(
            content=ft.Text("VBasal - Análisis de Cortante Basal", size=24, weight="bold", text_align="center"),
            margin=ft.margin.only(top=20, bottom=20),
            alignment=ft.alignment.center
        ),
        # 2. Tarjeta de Carga de Archivos
        ft.Container(
            content=ft.Column([
                r1c, r8c,
                ft.Divider(color=ft.colors.WHITE12, thickness=1),
                r1s, r8s
            ]),
            bgcolor=ft.colors.WHITE10, padding=15, border_radius=12
        ),
        # 3. Botón Calcular Centrado con Ícono
        ft.Container(
            content=ft.ElevatedButton(
                "CALCULAR",
                icon=ft.icons.CALCULATE_ROUNDED,
                on_click=calcular,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE,
                    padding=18,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    text_style=ft.TextStyle(size=16, weight="bold")
                ),
                width=250 # Botón más ancho
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=25, bottom=25)
        ),
        # 4. Sección de Gráfica y Resultados
        cont_grafico
    ], horizontal_alignment="center") # Centrar todo el contenido de la columna principal

    # ==========================================
    #   PANTALLA DE CARGA (SPLASH SCREEN)
    # ==========================================
    
    # Elementos del Splash
    col_splash = ft.Column([
        ft.Container(height=120),
        ft.Icon(ft.icons.VIBRATION_ROUNDED, size=90, color=ft.colors.CYAN_400),
        ft.Container(height=25),
        ft.Text("VBasal", size=32, weight="black", color=ft.colors.WHITE),
        ft.Text("Análisis Sísmico", color=ft.colors.GREY_400, size=16),
        ft.Container(height=50),
        ft.ProgressRing(width=35, height=35, stroke_width=3, color=ft.colors.PINK_400),
        ft.Container(height=50),
        ft.Text("Desarrollado por", color=ft.colors.GREY_500, size=12),
        ft.Text("Dayana Guanotuña", italic=True, color=ft.colors.CYAN_300, size=14, weight="bold")
    ], horizontal_alignment="center")

    # 1. Mostrar Splash
    page.add(col_splash)
    page.update()

    # 2. Esperar 3 segundos
    time.sleep(3)

    # 3. Limpiar y mostrar App Principal
    page.clean()
    page.add(interfaz_principal)
    page.update()

ft.app(target=main)