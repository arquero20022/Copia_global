import pyperclip
import random

# Función para generar un color aleatorio en formato hexadecimal
def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Función para generar la estructura HTML con colores aleatorios
def generate_div_structure(num_rows=12, num_cols=12):
    html_code = ""

    # Inicializar el contador
    counter = 1

    for row in range(num_rows):
        html_code += '<div class="row" style="height:5px;">\n'
        for col in range(num_cols):
            random_color = generate_random_color()  # Generar un color aleatorio
            html_code += f'    <div class="col-1" style=" background-color:{random_color}; color:white;">\n'
            html_code += f'        <span style="height:10px;"></span>\n'
            html_code += '    </div>\n'
            counter += 1
        html_code += '</div>\n'

    return html_code

# Generar el código con 12 filas y 12 columnas
html_output = generate_div_structure(150, 12)

# Copiar el resultado al portapapeles
pyperclip.copy(html_output)

print("El código HTML con colores aleatorios ha sido copiado al portapapeles.")
