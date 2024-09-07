import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser
from tkinter.scrolledtext import ScrolledText
from component_manager import ComponentManager

class ReportDesigner(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Diseñador de Reportes para Odoo - Arrastrar y Soltar")
        self.geometry("1500x800")

        # Configuración de la cuadrícula (12 columnas, 75 filas, con altura de 10px por fila)
        self.grid_cols = 12
        self.grid_rows = 75
        self.cell_width = 576 // self.grid_cols  # Cada columna tendrá el mismo ancho
        self.cell_height = 10  # Cada fila tendrá una altura fija de 10px

        # Componentes en la cuadrícula
        self.grid_components = [[None for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        self.component_data = {}

        # Canvas para representar la página
        self.canvas = tk.Canvas(self, bg='white', width=576, height=self.cell_height * self.grid_rows)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Dibujar la cuadrícula inicial
        self.draw_grid()

        # Barra de herramientas
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botones para agregar componentes
        self.add_draggable_button(toolbar, "Agregar H1", "h1")
        self.add_draggable_button(toolbar, "Agregar H2", "h2")
        self.add_draggable_button(toolbar, "Agregar Span", "span")
        self.add_draggable_button(toolbar, "Agregar Tabla", "table")
        self.add_draggable_button(toolbar, "Agregar Span Odoo", "span_odoo")
        self.add_draggable_button(toolbar, "Agregar Span Odoo con Condicional", "span_odoo_conditional")

        # Botón para generar el código HTML
        ttk.Button(toolbar, text="Generar Código", command=self.generate_code).pack(pady=20)

        # Cuadro de texto para mostrar el código generado, con scroll
        self.code_output = ScrolledText(self, height=10, width=150)
        self.code_output.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Frame para mostrar información del componente seleccionado y botones de acción
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Gestor de componentes
        self.component_manager = ComponentManager(self)

        # Bind left-click to show component info
        self.canvas.bind("<Button-1>", self.show_component_info)

    def draw_grid(self):
        """Dibujar una cuadrícula de 12 columnas y 75 filas con altura de 10px cada una"""
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x1 = col * self.cell_width
                y1 = row * self.cell_height
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="gray", fill="white")

    def add_draggable_button(self, toolbar, text, component_type):
        """Crear botones que permiten arrastrar y soltar componentes"""
        button = ttk.Button(toolbar, text=text)
        button.pack(pady=5)
        button.bind("<ButtonPress-1>", lambda event, arg=component_type: self.component_manager.start_drag(event, arg))

    def show_component_info(self, event):
        """Show the info of the clicked component and provide action buttons."""
        col = event.x // self.cell_width
        row = event.y // self.cell_height

        component_id = self.grid_components[row][col]

        if component_id:
            component_data = self.component_data[component_id]

            # Clear previous info
            for widget in self.info_frame.winfo_children():
                widget.destroy()

            # Display component info
            info_label = ttk.Label(self.info_frame, text=f"Component ID: {component_id} in Cell ({row}, {col}), Span: {component_data['cols_to_span']}")
            info_label.pack(pady=5)

            # Button to change background color
            bg_color_button = ttk.Button(self.info_frame, text="Change Background Color", command=lambda: self.component_manager.edit_background_color_by_id(component_id))
            bg_color_button.pack(pady=5)

            # Button to change font color
            font_color_button = ttk.Button(self.info_frame, text="Change Font Color", command=lambda: self.component_manager.edit_font_color_by_id(component_id))
            font_color_button.pack(pady=5)

            # Button to change font size
            font_size_button = ttk.Button(self.info_frame, text="Change Font Size", command=lambda: self.component_manager.edit_font_size_by_id(component_id))
            font_size_button.pack(pady=5)

            # Button to edit text or Odoo field
            edit_text_button = ttk.Button(self.info_frame, text="Edit Text / Field", command=lambda: self.component_manager.edit_text_by_id(component_id))
            edit_text_button.pack(pady=5)

            # Button to delete the component
            delete_button = ttk.Button(self.info_frame, text="Delete Component", command=lambda: self.component_manager.delete_component_by_id(component_id))
            delete_button.pack(pady=5)

    def generate_code(self):
        """Generate the HTML code and display it in the code output area."""
        html_code = self.component_manager.generate_html()  # Generate the HTML

        # Clear the previous code output
        self.code_output.delete(1.0, tk.END)

        # Display the new code with highlighting
        self.component_manager.display_code_with_highlighting(html_code) # Display new code
