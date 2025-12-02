# -*- coding: cp1251 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from pathlib import Path

class ImageProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка изображений - Глобальная и адаптивная пороговая обработка")
        self.root.geometry("1400x900")
        
        self.original_image = None
        self.processed_image = None
        self.image_path = None
        
        self.create_widgets()
        
        self.create_test_images()
        
    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(main_frame, width=300, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.original_frame = tk.LabelFrame(right_frame, text="Оригинальное изображение")
        self.original_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.original_label = tk.Label(self.original_frame, text="Загрузите изображение", bg="lightgray")
        self.original_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.processed_frame = tk.LabelFrame(right_frame, text="Обработанное изображение")
        self.processed_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.processed_label = tk.Label(self.processed_frame, text="Результат обработки", bg="lightgray")
        self.processed_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(left_frame, text="Обработка изображений", font=("Arial", 14, "bold"), 
                bg="#f0f0f0").pack(pady=10)
        
        tk.Button(left_frame, text="Загрузить изображение", command=self.load_image,
                 bg="#4CAF50", fg="white", font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        tk.Button(left_frame, text="Сохранить результат", command=self.save_image,
                 bg="#2196F3", fg="white", font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="Линейное контрастирование", font=("Arial", 12, "bold"),
                bg="#f0f0f0").pack(pady=5)
        
        tk.Button(left_frame, text="Применить линейное контрастирование", 
                 command=self.apply_linear_contrast, bg="#FF9800", fg="white",
                 font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        param_frame = tk.Frame(left_frame, bg="#f0f0f0")
        param_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(param_frame, text="Min:", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.min_contrast = tk.Entry(param_frame, width=6)
        self.min_contrast.pack(side=tk.LEFT, padx=2)
        self.min_contrast.insert(0, "0")
        
        tk.Label(param_frame, text="Max:", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.max_contrast = tk.Entry(param_frame, width=6)
        self.max_contrast.pack(side=tk.LEFT, padx=2)
        self.max_contrast.insert(0, "255")
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="Глобальная пороговая обработка", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        self.global_method = tk.StringVar(value="otsu")
        
        tk.Radiobutton(left_frame, text="Метод Оцу", variable=self.global_method, 
                      value="otsu", bg="#f0f0f0").pack(anchor=tk.W, padx=20)
        tk.Radiobutton(left_frame, text="Метод Треугольника", variable=self.global_method, 
                      value="triangle", bg="#f0f0f0").pack(anchor=tk.W, padx=20)
        
        tk.Button(left_frame, text="Применить глобальный порог", 
                 command=self.apply_global_threshold, bg="#9C27B0", fg="white",
                 font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="Адаптивная пороговая обработка", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        adapt_frame = tk.Frame(left_frame, bg="#f0f0f0")
        adapt_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(adapt_frame, text="Размер блока:", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.block_size = tk.Entry(adapt_frame, width=6)
        self.block_size.pack(side=tk.LEFT, padx=2)
        self.block_size.insert(0, "11")
        
        tk.Label(adapt_frame, text="Константа C:", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.c_value = tk.Entry(adapt_frame, width=6)
        self.c_value.pack(side=tk.LEFT, padx=2)
        self.c_value.insert(0, "2")
        
        tk.Button(left_frame, text="Применить адаптивный порог", 
                 command=self.apply_adaptive_threshold, bg="#E91E63", fg="white",
                 font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="Поэлементные операции", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        self.element_op = tk.StringVar(value="add")
        
        op_frame = tk.Frame(left_frame, bg="#f0f0f0")
        op_frame.pack(pady=5)
        
        operations = [("Сложение", "add"), ("Вычитание", "subtract"), 
                     ("Умножение", "multiply"), ("Деление", "divide")]
        
        for text, value in operations:
            tk.Radiobutton(op_frame, text=text, variable=self.element_op, 
                          value=value, bg="#f0f0f0").pack(anchor=tk.W)
        
        tk.Button(left_frame, text="Применить операцию", 
                 command=self.apply_element_operation, bg="#00BCD4", fg="white",
                 font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        tk.Button(left_frame, text="Загрузить второе изображение", 
                 command=self.load_second_image, bg="#607D8B", fg="white",
                 font=("Arial", 10)).pack(pady=5, fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="Тестовая база изображений", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        test_frame = tk.Frame(left_frame, bg="#f0f0f0")
        test_frame.pack(fill=tk.X, pady=5)
        
        test_images = ["Зашумленное", "Размытое", "Малоконтрастное", "Текст"]
        self.test_var = tk.StringVar(value=test_images[0])
        
        test_combo = ttk.Combobox(test_frame, textvariable=self.test_var, 
                                 values=test_images, state="readonly", width=15)
        test_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Button(test_frame, text="Загрузить", command=self.load_test_image,
                 bg="#795548", fg="white").pack(side=tk.RIGHT, padx=5)
        
        self.status_bar = tk.Label(self.root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.second_image = None
        self.second_image_path = None
        
    def create_test_images(self):
        test_dir = "test_images"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        img = np.ones((300, 400), dtype=np.uint8) * 128
        noise = np.random.normal(0, 50, (300, 400)).astype(np.uint8)
        noisy_img = cv2.add(img, noise)
        cv2.imwrite(f"{test_dir}/noisy.png", noisy_img)
        
        img = np.zeros((300, 400), dtype=np.uint8)
        cv2.circle(img, (200, 150), 50, 255, -1)
        cv2.circle(img, (100, 150), 30, 200, -1)
        blurred = cv2.GaussianBlur(img, (15, 15), 5)
        cv2.imwrite(f"{test_dir}/blurred.png", blurred)
        
        img = np.random.randint(100, 150, (300, 400), dtype=np.uint8)
        cv2.imwrite(f"{test_dir}/low_contrast.png", img)
        
        img = np.ones((300, 400), dtype=np.uint8) * 200
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'Test Text', (50, 150), font, 2, 50, 3, cv2.LINE_AA)
        cv2.putText(img, 'For Thresholding', (30, 220), font, 1, 30, 2, cv2.LINE_AA)
        cv2.imwrite(f"{test_dir}/text.png", img)
        
        self.status_bar.config(text="Создана тестовая база изображений")
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")]
        )
        
        if file_path:
            self.image_path = file_path
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                self.display_image(self.original_image, self.original_label)
                self.status_bar.config(text=f"Загружено: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
                
    def load_second_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")]
        )
        
        if file_path:
            self.second_image_path = file_path
            self.second_image = cv2.imread(file_path)
            if self.second_image is not None:
                self.status_bar.config(text=f"Загружено второе изображение: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
                
    def load_test_image(self):
        test_type = self.test_var.get()
        test_files = {
            "Зашумленное": "test_images/noisy.png",
            "Размытое": "test_images/blurred.png",
            "Малоконтрастное": "test_images/low_contrast.png",
            "Текст": "test_images/text.png"
        }
        
        file_path = test_files.get(test_type)
        if file_path and os.path.exists(file_path):
            self.image_path = file_path
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                self.display_image(self.original_image, self.original_label)
                self.status_bar.config(text=f"Загружено тестовое изображение: {test_type}")
                
    def apply_linear_contrast(self):
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
            
        try:
            min_val = int(self.min_contrast.get())
            max_val = int(self.max_contrast.get())
            
            if min_val >= max_val:
                messagebox.showerror("Ошибка", "Min должен быть меньше Max")
                return
                
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = self.original_image.copy()
            
            current_min = gray.min()
            current_max = gray.max()
            
            stretched = ((gray - current_min) / (current_max - current_min) * 
                        (max_val - min_val) + min_val).astype(np.uint8)
            
            self.processed_image = stretched
            self.display_image(stretched, self.processed_label)
            self.status_bar.config(text="Применено линейное контрастирование")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")
            
    def apply_global_threshold(self):
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
            
        if len(self.original_image.shape) == 3:
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.original_image.copy()
        
        method = self.global_method.get()
        
        if method == "otsu":
            _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            method_name = "Метод Оцу"
        elif method == "triangle":
            _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
            method_name = "Метод треугольника"
        else:
            _, thresholded = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            method_name = "Простой порог"
        
        self.processed_image = thresholded
        self.display_image(thresholded, self.processed_label)
        self.status_bar.config(text=f"Применена глобальная пороговая обработка: {method_name}")
        
    def apply_adaptive_threshold(self):
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
            
        try:
            block_size = int(self.block_size.get())
            c = int(self.c_value.get())
            
            if block_size % 2 == 0:
                block_size += 1
                self.block_size.delete(0, tk.END)
                self.block_size.insert(0, str(block_size))
            
            if len(self.original_image.shape) == 3:
                gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = self.original_image.copy()
            
            thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY, block_size, c)
            
            self.processed_image = thresholded
            self.display_image(thresholded, self.processed_label)
            self.status_bar.config(text=f"Применена адаптивная пороговая обработка (блок={block_size}, C={c})")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")
            
    def apply_element_operation(self):
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите основное изображение")
            return
            
        if self.second_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите второе изображение")
            return
            
        if self.original_image.shape != self.second_image.shape:
            messagebox.showerror("Ошибка", "Изображения должны быть одинакового размера")
            return
            
        operation = self.element_op.get()
        
        try:
            if operation == "add":
                result = cv2.add(self.original_image, self.second_image)
                op_name = "Сложение"
            elif operation == "subtract":
                result = cv2.subtract(self.original_image, self.second_image)
                op_name = "Вычитание"
            elif operation == "multiply":
                img1_norm = self.original_image.astype(np.float32) / 255
                img2_norm = self.second_image.astype(np.float32) / 255
                result_norm = img1_norm * img2_norm
                result = (result_norm * 255).astype(np.uint8)
                op_name = "Умножение"
            elif operation == "divide":
                img2 = self.second_image.astype(np.float32)
                img2[img2 == 0] = 1
                result_norm = self.original_image.astype(np.float32) / img2
                result = np.clip(result_norm * 255, 0, 255).astype(np.uint8)
                op_name = "Деление"
            else:
                result = self.original_image.copy()
                op_name = "Нет операции"
            
            self.processed_image = result
            self.display_image(result, self.processed_label)
            self.status_bar.config(text=f"Применена поэлементная операция: {op_name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить операцию: {str(e)}")
            
    def display_image(self, image, label_widget):
        h, w = image.shape[:2]
        max_size = 500
        
        if h > w:
            new_h = max_size
            new_w = int(w * max_size / h)
        else:
            new_w = max_size
            new_h = int(h * max_size / w)
            
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(image_rgb)
        else:
            img = Image.fromarray(image)
        
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        
        label_widget.configure(image=img_tk, text="")
        label_widget.image = img_tk
        
    def save_image(self):
        if self.processed_image is None:
            messagebox.showwarning("Предупреждение", "Нет обработанного изображения для сохранения")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), 
                      ("All files", "*.*")]
        )
        
        if file_path:
            cv2.imwrite(file_path, self.processed_image)
            self.status_bar.config(text=f"Изображение сохранено: {os.path.basename(file_path)}")
            messagebox.showinfo("Успех", "Изображение успешно сохранено")

def main():
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()