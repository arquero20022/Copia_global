import dearpygui.dearpygui as dpg
from pygments import highlight
from pygments.lexers import HtmlLexer
from pygments.token import Token


# Crear una función que convierte los tokens de Pygments a estilos de Dear PyGui
def pygments_to_dearpygui(text):
    lexer = HtmlLexer()
    tokens = lexer.get_tokens(text)

    # Limpiar el contenido del widget antes de añadir el código resaltado
    dpg.delete_item("output_text", children_only=True)

    for token_type, token_value in tokens:
        # Asignamos colores basados en el tipo de token
        if token_type in Token.Keyword:
            color = [255, 0, 0, 255]  # Rojo
        elif token_type in Token.Name:
            color = [0, 255, 0, 255]  # Verde
        elif token_type in Token.Literal.String:
            color = [0, 0, 255, 255]  # Azul
        elif token_type in Token.Comment:
            color = [128, 128, 128, 255]  # Gris
        else:
            color = [255, 255, 255, 255]  # Blanco (color por defecto)

        # Añadimos el texto con color al widget
        dpg.add_text(token_value, color=color, parent="output_text")


# Función que se ejecuta cuando se presiona el botón
def procesar_codigo_html(sender, app_data):
    codigo_html = dpg.get_value("input_text")
    pygments_to_dearpygui(codigo_html)


# Crear la ventana principal
dpg.create_context()

with dpg.window(label="Resaltador de Código HTML", width=800, height=600):
    dpg.add_text("Ingresa el código HTML:")

    # Área de texto para ingresar el HTML
    dpg.add_input_text(multiline=True, width=780, height=150, tag="input_text")

    # Botón para procesar y resaltar el código HTML
    dpg.add_button(label="Resaltar Código HTML", callback=procesar_codigo_html)

    dpg.add_text("Código resaltado:")

    # Contenedor para el código resaltado
    dpg.add_group(horizontal=False, tag="output_text", width=780, height=300)

dpg.create_viewport(title='Resaltador de Código HTML', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
