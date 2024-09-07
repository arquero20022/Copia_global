class AnimationHandler:
    def __init__(self, master):
        self.master = master

    def smooth_drag(self, event):
        """Add smooth dragging behavior"""
        self.master.canvas.move("drag_preview", event.x - self.master.drag_data["x"], event.y - self.master.drag_data["y"])
        self.master.update_idletasks()
