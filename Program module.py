import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple
import math

class ChainDrive:
    def __init__(self):
        # Стандартные параметры однорядных цепей по ГОСТ 13568-97
        self.standard_chains = {
            12.7: [18100, 0.80],
            15.875: [28900, 1.25],
            19.05: [44500, 1.80],
            25.4: [89000, 2.60],
            31.75: [137000, 3.80],
            38.1: [198000, 5.50],
        }

    def get_min_teeth_count(self, gear_ratio: float) -> int:
        """Выбор минимального числа зубьев ведущей звездочки в зависимости от передаточного отношения."""
        z1_min = math.ceil(19 - 2 * gear_ratio)
        return max(z1_min, 9)  # Минимум 9 зубьев по ГОСТ

    def select_chain_pitch(self, torque: float, z1: int, k_e: float) -> float:
        """Подбор шага цепи на основе вращающего момента, числа зубьев и коэффициента эксплуатации."""
        p_allow = 20  # Допускаемое давление, МПа, для первого приближения
        pitch = ((2.18 * torque * k_e) / (z1 * p_allow)) ** (1 / 3)
        for standard_pitch in self.standard_chains:
            if standard_pitch >= pitch:
                return standard_pitch
        raise ValueError("Не удалось подобрать подходящий шаг цепи.")

    def calculate_chain_length(self, z1: int, z2: int, a: float, pitch: float) -> Tuple[int, float]:
        """Расчет длины цепи в шагах и уточненного межосевого расстояния."""
        l = 2 * a / pitch + (z1 + z2) / 2 + (z2 - z1) ** 2 / (4 * math.pi * a / pitch)
        l = math.ceil(l)
        a_actual = (pitch / 4) * (
            l - (z1 + z2) / 2 + math.sqrt((l - (z1 + z2) / 2) ** 2 - 8 * (z2 - z1) ** 2 / (4 * math.pi) ** 2)
        )
        return l, a_actual

    def calculate_velocity(self, n1: float, z1: int, pitch: float) -> float:
        """Расчет скорости цепи."""
        return (z1 * pitch * n1) / (60 * 1000)

    def calculate_drive(self, torque: float, n1: float, gear_ratio: float, service_factor: float, min_distance: float) -> Dict:
        """Основной расчет цепной передачи в соответствии с ГОСТ."""
        z1 = self.get_min_teeth_count(gear_ratio)
        z2 = round(z1 * gear_ratio)
        pitch = self.select_chain_pitch(torque, z1, service_factor)
        velocity = self.calculate_velocity(n1, z1, pitch)
        chain_length, actual_distance = self.calculate_chain_length(z1, z2, min_distance, pitch)

        return {
            "малая_звездочка_зубья": z1,
            "большая_звездочка_зубья": z2,
            "шаг_цепи_мм": pitch,
            "длина_цепи_звеньев": chain_length,
            "межосевое_расстояние_мм": round(actual_distance, 1),
            "скорость_цепи_м/с": round(velocity, 2),
        }

class ChainDriveCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор цепной передачи")
        self.chain_drive = ChainDrive()

        self.is_dark_theme = False
        self.setup_styles()

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        for i in range(8):
            self.main_frame.grid_rowconfigure(i, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.create_gost_label()
        self.create_theme_switch_button()
        self.create_input_fields()

        calculate_button = ttk.Button(self.main_frame, text="Рассчитать", command=self.calculate)
        calculate_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")

        self.create_result_area()
        self.add_tooltips()
        self.root.minsize(400, 600)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background='white')
        self.style.configure('TLabel', background='white', foreground='black')
        self.style.configure('TEntry', fieldbackground='white', foreground='black')
        self.style.configure('TButton', background='white', foreground='black')

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.style.configure('TFrame', background='#2e2e2e')
            self.style.configure('TLabel', background='#2e2e2e', foreground='white')
            self.style.configure('TEntry', fieldbackground='#3e3e3e', foreground='white')
            self.style.configure('TButton', background='#2e2e2e', foreground='white')
            self.result_text.configure(bg='#3e3e3e', fg='white', insertbackground='white')
        else:
            self.style.configure('TFrame', background='white')
            self.style.configure('TLabel', background='white', foreground='black')
            self.style.configure('TEntry', fieldbackground='white', foreground='black')
            self.style.configure('TButton', background='white', foreground='black')
            self.result_text.configure(bg='white', fg='black', insertbackground='black')

    def create_theme_switch_button(self):
        theme_button = ttk.Button(self.main_frame, text="Сменить тему", command=self.toggle_theme)
        theme_button.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

    def create_gost_label(self):
        gost_label = ttk.Label(self.main_frame, text="Расчеты в соответствии с ГОСТ 13568-97", font=("Arial", 10, "italic"))
        gost_label.grid(row=0, column=0, columnspan=1, sticky="w", pady=(0, 10))

    def create_input_fields(self):
        self.input_fields = {
            "torque": "Вращающий момент (Н·м):",
            "n1": "Частота вращения (об/мин):",
            "gear_ratio": "Передаточное число:",
            "service_factor": "Коэффициент эксплуатации:",
            "min_distance": "Минимальное межосевое расстояние (мм):"
        }

        self.entries = {}
        for i, (key, label_text) in enumerate(self.input_fields.items()):
            frame = ttk.Frame(self.main_frame)
            frame.grid(row=i+1, column=0, columnspan=2, sticky="ew", pady=5)
            frame.grid_columnconfigure(1, weight=1)

            label = ttk.Label(frame, text=label_text)
            label.grid(row=0, column=0, sticky="w")

            self.entries[key] = ttk.Entry(frame)
            self.entries[key].grid(row=0, column=1, sticky="ew", padx=(10, 0))

    def create_result_area(self):
        result_frame = ttk.Frame(self.main_frame)
        result_frame.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=10)
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.result_text = tk.Text(result_frame, height=10, width=50, yscrollcommand=scrollbar.set)
        self.result_text.grid(row=0, column=0, sticky="nsew")

        scrollbar.config(command=self.result_text.yview)

    def add_tooltips(self):
        tooltips = {
            "torque": "Введите вращающий момент в Н·м",
            "n1": "Введите частоту вращения ведущей звездочки в об/мин",
            "gear_ratio": "Введите требуемое передаточное отношение",
            "service_factor": "Коэффициент, учитывающий условия работы",
            "min_distance": "Минимально допустимое расстояние между осями звездочек"
        }

        for key, tooltip_text in tooltips.items():
            self.create_tooltip(self.entries[key], tooltip_text)
    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            def hide_tooltip():
                tooltip.destroy()
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            tooltip.bind('<Leave>', lambda e: hide_tooltip())
        widget.bind('<Enter>', show_tooltip)
    def validate_inputs(self) -> bool:
        try:
            for key, entry in self.entries.items():
                value = float(entry.get())
                if value <= 0:
                    raise ValueError(f"Значение {self.input_fields[key]} должно быть положительным")
            return True
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return False
    def calculate(self):
        if not self.validate_inputs():
            return
        try:
            params = {
                "torque": float(self.entries["torque"].get()),
                "n1": float(self.entries["n1"].get()),
                "gear_ratio": float(self.entries["gear_ratio"].get()),
                "service_factor": float(self.entries["service_factor"].get()),
                "min_distance": float(self.entries["min_distance"].get())
            }
            results = self.chain_drive.calculate_drive(**params)

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Результаты расчета:\n\n")

            for key, value in results.items():
                self.result_text.insert(tk.END, f"{key}: {value}\n")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расчете: {str(e)}")
def main():
    root = tk.Tk()
    app = ChainDriveCalculatorGUI(root)
    root.mainloop()
if __name__ == "__main__":
    main()
