import os
import sys
import time
import struct
import threading
import queue
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import concurrent.futures
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
from PIL import Image, ImageTk

try:
    import jpegio
    HAS_JPEGIO = True
except ImportError:
    HAS_JPEGIO = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

@dataclass
class ImageInfo:
    filename: str
    filepath: str
    file_size: int
    width: int
    height: int
    resolution_x: Optional[float] = None
    resolution_y: Optional[float] = None
    color_depth: int = 0
    compression: str = "Unknown"
    format: str = "Unknown"
    has_palette: bool = False
    palette_colors: int = 0
    additional_info: Dict = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}

class ImageFileAnalyzer:
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx'}
        self.total_files_processed = 0
        self.processing_time = 0
        
    def analyze_file(self, filepath: str) -> Optional[ImageInfo]:
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                return None
                
            file_size = filepath.stat().st_size
            extension = filepath.suffix.lower()
            
            if extension in ['.jpg', '.jpeg']:
                return self._analyze_jpeg(filepath, file_size)
            elif extension == '.gif':
                return self._analyze_gif(filepath, file_size)
            elif extension in ['.tif', '.tiff']:
                return self._analyze_tiff(filepath, file_size)
            elif extension == '.bmp':
                return self._analyze_bmp(filepath, file_size)
            elif extension == '.png':
                return self._analyze_png(filepath, file_size)
            elif extension == '.pcx':
                return self._analyze_pcx(filepath, file_size)
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка при анализе файла {filepath}: {e}")
            return None
    
    def _analyze_jpeg(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                color_depth = img.bits if hasattr(img, 'bits') else 24
                
                dpi_value = img.info.get('dpi')
                if dpi_value:
                    resolution_x, resolution_y = dpi_value
                    if resolution_x == 0:
                        resolution_x = 72
                    if resolution_y == 0:
                        resolution_y = 72
                else:
                    resolution_x = resolution_y = 72
                
                compression = img.info.get('compression', 'JPEG')
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=resolution_x,
                    resolution_y=resolution_y,
                    color_depth=color_depth,
                    compression=compression,
                    format="JPEG"
                )
                
                if HAS_JPEGIO:
                    try:
                        jpeg_obj = jpegio.read(str(filepath))
                        quant_tables = []
                        for i, table in enumerate(jpeg_obj.quant_tables):
                            if table is not None:
                                if HAS_NUMPY:
                                    table_data = np.array(table).flatten()
                                    quant_tables.append(f"Table {i}: {table_data[:4].tolist()}...")
                                else:
                                    quant_tables.append(f"Table {i}: {len(table)} коэффициентов")
                        
                        if quant_tables:
                            info.additional_info["quantization_tables"] = quant_tables
                    except:
                        pass
                
                return info
        except Exception as e:
            print(f"Ошибка при анализе JPEG {filepath}: {e}")
        
        return self._analyze_jpeg_header(filepath, file_size)
    
    def _analyze_jpeg_header(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with open(filepath, 'rb') as f:
                data = f.read(512)
                
                pos = 0
                while pos < len(data) - 1:
                    if data[pos] == 0xFF and data[pos + 1] == 0xC0:
                        f.seek(pos + 5)
                        height = struct.unpack('>H', f.read(2))[0]
                        width = struct.unpack('>H', f.read(2))[0]
                        
                        info = ImageInfo(
                            filename=filepath.name,
                            filepath=str(filepath),
                            file_size=file_size,
                            width=width,
                            height=height,
                            resolution_x=72,
                            resolution_y=72,
                            color_depth=24,
                            compression="JPEG",
                            format="JPEG"
                        )
                        return info
                    pos += 1
        except:
            pass
        
        return None
    
    def _analyze_gif(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                
                has_palette = img.palette is not None
                palette_colors = 0
                if has_palette and hasattr(img.palette, 'palette'):
                    palette_colors = len(img.palette.palette) // 3
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=72,
                    resolution_y=72,
                    color_depth=8,
                    compression="LZW",
                    format="GIF",
                    has_palette=has_palette,
                    palette_colors=palette_colors
                )
                
                info.additional_info["has_palette"] = has_palette
                info.additional_info["palette_colors"] = palette_colors
                
                return info
        except Exception as e:
            print(f"Ошибка при анализе GIF {filepath}: {e}")
        
        try:
            with open(filepath, 'rb') as f:
                signature = f.read(6)
                if signature in [b'GIF87a', b'GIF89a']:
                    width = struct.unpack('<H', f.read(2))[0]
                    height = struct.unpack('<H', f.read(2))[0]
                    
                    flags = f.read(1)[0]
                    has_palette = (flags & 0x80) != 0
                    palette_colors = 2 << (flags & 0x07)
                    
                    info = ImageInfo(
                        filename=filepath.name,
                        filepath=str(filepath),
                        file_size=file_size,
                        width=width,
                        height=height,
                        resolution_x=72,
                        resolution_y=72,
                        color_depth=8,
                        compression="LZW",
                        format="GIF",
                        has_palette=has_palette,
                        palette_colors=palette_colors
                    )
                    
                    info.additional_info["has_palette"] = has_palette
                    info.additional_info["palette_colors"] = palette_colors
                    
                    return info
        except:
            pass
        
        return None
    
    def _analyze_bmp(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                
                dpi_value = img.info.get('dpi')
                if dpi_value:
                    resolution_x, resolution_y = dpi_value
                    if resolution_x == 0:
                        resolution_x = 96
                    if resolution_y == 0:
                        resolution_y = 96
                else:
                    resolution_x = resolution_y = 96
                
                color_depth = img.bits if hasattr(img, 'bits') else 24
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=resolution_x,
                    resolution_y=resolution_y,
                    color_depth=color_depth,
                    compression="None" if img.mode == 'RGB' else "RLE",
                    format="BMP"
                )
                
                return info
        except Exception as e:
            print(f"Ошибка при анализе BMP {filepath}: {e}")
        
        try:
            with open(filepath, 'rb') as f:
                if f.read(2) == b'BM':
                    f.seek(18)
                    width = struct.unpack('<I', f.read(4))[0]
                    height = struct.unpack('<I', f.read(4))[0]
                    
                    f.seek(28)
                    color_depth = struct.unpack('<H', f.read(2))[0]
                    
                    f.seek(38)
                    ppm_x = struct.unpack('<I', f.read(4))[0]
                    ppm_y = struct.unpack('<I', f.read(4))[0]
                    
                    dpi_x = ppm_x / 39.3701 if ppm_x > 0 else 96
                    dpi_y = ppm_y / 39.3701 if ppm_y > 0 else 96
                    
                    info = ImageInfo(
                        filename=filepath.name,
                        filepath=str(filepath),
                        file_size=file_size,
                        width=width,
                        height=height,
                        resolution_x=dpi_x,
                        resolution_y=dpi_y,
                        color_depth=color_depth,
                        compression="None",
                        format="BMP"
                    )
                    
                    return info
        except:
            pass
        
        return None
    
    def _analyze_png(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                
                dpi_value = img.info.get('dpi')
                
                if dpi_value and dpi_value != (0, 0):
                    resolution_x, resolution_y = dpi_value
                else:
                    resolution_x = None
                    resolution_y = None
                
                color_depth = img.bits if hasattr(img, 'bits') else 24
                
                compression = img.info.get('compression', 'DEFLATE')
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=resolution_x,
                    resolution_y=resolution_y,
                    color_depth=color_depth,
                    compression=compression,
                    format="PNG"
                )
                
                if 'gamma' in img.info:
                    info.additional_info["gamma"] = img.info['gamma']
                
                return info
        except Exception as e:
            print(f"Ошибка при анализе PNG {filepath}: {e}")
        
        return None
    
    def _analyze_tiff(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                
                dpi_value = img.info.get('dpi')
                if dpi_value:
                    resolution_x, resolution_y = dpi_value
                    if resolution_x == 0:
                        resolution_x = 72
                    if resolution_y == 0:
                        resolution_y = 72
                else:
                    resolution_x = resolution_y = 72
                
                color_depth = img.bits if hasattr(img, 'bits') else 24
                
                compression = img.info.get('compression', 'None')
                if compression == 'tiff_lzw':
                    compression = "LZW"
                elif compression == 'tiff_ccitt':
                    compression = "CCITT"
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=resolution_x,
                    resolution_y=resolution_y,
                    color_depth=color_depth,
                    compression=compression,
                    format="TIFF"
                )
                
                return info
        except Exception as e:
            print(f"Ошибка при анализе TIFF {filepath}: {e}")
        
        return None
    
    def _analyze_pcx(self, filepath: Path, file_size: int) -> Optional[ImageInfo]:
        try:
            with open(filepath, 'rb') as f:
                manufacturer = f.read(1)[0]
                if manufacturer != 0x0A:
                    return None
                
                version = f.read(1)[0]
                encoding = f.read(1)[0]
                bits_per_pixel = f.read(1)[0]
                
                xmin = struct.unpack('<H', f.read(2))[0]
                ymin = struct.unpack('<H', f.read(2))[0]
                xmax = struct.unpack('<H', f.read(2))[0]
                ymax = struct.unpack('<H', f.read(2))[0]
                
                width = xmax - xmin + 1
                height = ymax - ymin + 1
                
                hdpi = struct.unpack('<H', f.read(2))[0]
                vdpi = struct.unpack('<H', f.read(2))[0]
                
                resolution_x = hdpi if hdpi > 0 else 96
                resolution_y = vdpi if vdpi > 0 else 96
                
                f.seek(128)
                
                compression = "RLE" if encoding == 1 else "None"
                
                color_depth = bits_per_pixel
                
                info = ImageInfo(
                    filename=filepath.name,
                    filepath=str(filepath),
                    file_size=file_size,
                    width=width,
                    height=height,
                    resolution_x=resolution_x,
                    resolution_y=resolution_y,
                    color_depth=color_depth,
                    compression=compression,
                    format="PCX"
                )
                
                info.additional_info["pcx_version"] = version
                
                return info
                
        except Exception as e:
            print(f"Ошибка при анализе PCX {filepath}: {e}")
        
        return None
    
    def analyze_folder(self, folder_path: str, max_files: int = 100000, 
                      use_multithreading: bool = True, progress_callback=None) -> List[ImageInfo]:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return []
        
        image_files = []
        for ext in self.supported_formats:
            image_files.extend(folder.glob(f"*{ext}"))
            image_files.extend(folder.glob(f"*{ext.upper()}"))
        
        image_files = image_files[:max_files]
        
        start_time = time.time()
        
        if use_multithreading and len(image_files) > 10:
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_file = {executor.submit(self.analyze_file, str(file)): file 
                                for file in image_files}
                
                for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    if progress_callback and i % 10 == 0:
                        progress_callback(i, len(image_files))
        else:
            results = []
            for i, file in enumerate(image_files):
                result = self.analyze_file(str(file))
                if result:
                    results.append(result)
                
                if progress_callback and i % 10 == 0:
                    progress_callback(i, len(image_files))
        
        end_time = time.time()
        self.processing_time = end_time - start_time
        self.total_files_processed = len(results)
        
        if progress_callback:
            progress_callback(len(image_files), len(image_files))
        
        return results

class ImageAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор графических файлов")
        self.root.geometry("1200x700")
        
        self.analyzer = ImageFileAnalyzer()
        self.current_results = []
        
        self.queue = queue.Queue()
        
        self.is_processing = False
        self.processing_thread = None
        
        self.setup_ui()
        
        self.check_queue()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        title_label = ttk.Label(
            main_frame, 
            text="Анализатор графических файлов", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="Выбрать папку", 
            command=self.select_folder,
            width=15
        ).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="Анализировать файл", 
            command=self.select_file,
            width=15
        ).grid(row=0, column=1, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Остановить", 
            command=self.stop_processing,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2, padx=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            control_frame, 
            variable=self.progress_var,
            maximum=100,
            length=200
        )
        self.progress_bar.grid(row=0, column=3, padx=(20, 10))
        
        self.status_label = ttk.Label(control_frame, text="Готов к работе")
        self.status_label.grid(row=0, column=4, padx=(10, 0))
        
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Макс. файлов:").grid(row=0, column=0, padx=(0, 5))
        self.max_files_var = tk.StringVar(value="100000")
        max_files_spinbox = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=100000,
            textvariable=self.max_files_var,
            width=10
        )
        max_files_spinbox.grid(row=0, column=1, padx=(0, 20))
        
        self.multithreading_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text="Использовать многопоточность",
            variable=self.multithreading_var
        ).grid(row=0, column=2, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Форматы:").grid(row=0, column=3, padx=(0, 5))
        formats_text = ", ".join(sorted(self.analyzer.supported_formats))
        ttk.Label(settings_frame, text=formats_text, foreground="blue").grid(row=0, column=4)
        
        results_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        columns = ("filename", "size", "resolution", "depth", "compression", "format", "filesize")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("filename", text="Имя файла")
        self.tree.heading("size", text="Размер (пикс)")
        self.tree.heading("resolution", text="Разрешение (DPI)")
        self.tree.heading("depth", text="Глубина цвета")
        self.tree.heading("compression", text="Сжатие")
        self.tree.heading("format", text="Формат")
        self.tree.heading("filesize", text="Размер файла")
        
        self.tree.column("filename", width=200)
        self.tree.column("size", width=100)
        self.tree.column("resolution", width=120)
        self.tree.column("depth", width=100)
        self.tree.column("compression", width=100)
        self.tree.column("format", width=80)
        self.tree.column("filesize", width=100)
        
        scrollbar_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.bind("<Double-1>", self.show_file_details)
        
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.total_files_label = ttk.Label(stats_frame, text="Файлов: 0")
        self.total_files_label.grid(row=0, column=0, padx=(0, 20))
        
        self.total_size_label = ttk.Label(stats_frame, text="Общий размер: 0 MB")
        self.total_size_label.grid(row=0, column=1, padx=(0, 20))
        
        self.time_label = ttk.Label(stats_frame, text="Время: 0.00 сек")
        self.time_label.grid(row=0, column=2, padx=(0, 20))
        
        export_frame = ttk.Frame(stats_frame)
        export_frame.grid(row=0, column=3, sticky=tk.E)
        
        ttk.Button(
            export_frame,
            text="Экспорт в CSV",
            command=self.export_csv,
            width=15
        ).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(
            export_frame,
            text="Экспорт в TXT",
            command=self.export_txt,
            width=15
        ).grid(row=0, column=1)
        
        ttk.Button(
            export_frame,
            text="Справка",
            command=self.show_help,
            width=15
        ).grid(row=0, column=2, padx=(5, 0))
    
    def select_folder(self):
        if self.is_processing:
            messagebox.showwarning("Внимание", "Анализ уже выполняется")
            return
        
        folder_path = filedialog.askdirectory(title="Выберите папку с изображениями")
        if folder_path:
            self.start_processing(folder_path)
    
    def select_file(self):
        if self.is_processing:
            messagebox.showwarning("Внимание", "Анализ уже выполняется")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл изображения",
            filetypes=[
                ("Все поддерживаемые", "*.jpg;*.jpeg;*.gif;*.tif;*.tiff;*.bmp;*.png;*.pcx"),
                ("JPEG", "*.jpg;*.jpeg"),
                ("GIF", "*.gif"),
                ("TIFF", "*.tif;*.tiff"),
                ("BMP", "*.bmp"),
                ("PNG", "*.png"),
                ("PCX", "*.pcx"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            self.start_processing_single(file_path)
    
    def start_processing(self, folder_path):
        self.is_processing = True
        self.current_results = []
        self.clear_table()
        self.update_status("Начинаю анализ...")
        self.progress_var.set(0)
        
        try:
            max_files = int(self.max_files_var.get())
        except:
            max_files = 100000
        
        use_threads = self.multithreading_var.get()
        
        self.processing_thread = threading.Thread(
            target=self.process_folder,
            args=(folder_path, max_files, use_threads),
            daemon=True
        )
        self.processing_thread.start()
        
        self.stop_button.configure(state=tk.NORMAL)
    
    def start_processing_single(self, file_path):
        self.is_processing = True
        self.current_results = []
        self.clear_table()
        self.update_status("Анализирую файл...")
        self.progress_var.set(0)
        
        self.processing_thread = threading.Thread(
            target=self.process_single_file,
            args=(file_path,),
            daemon=True
        )
        self.processing_thread.start()
        
        self.stop_button.configure(state=tk.NORMAL)
    
    def process_folder(self, folder_path, max_files, use_threads):
        try:
            def progress_callback(current, total):
                if total > 0:
                    progress = (current / total) * 100
                    self.queue.put(("progress", progress))
                    self.queue.put(("status", f"Обработано {current} из {total} файлов"))
            
            results = self.analyzer.analyze_folder(
                folder_path, 
                max_files, 
                use_threads,
                progress_callback
            )
            
            self.queue.put(("results", results))
            self.queue.put(("status", f"Анализ завершен. Обработано {len(results)} файлов"))
            self.queue.put(("progress", 100))
            
        except Exception as e:
            self.queue.put(("error", f"Ошибка при анализе: {str(e)}"))
        finally:
            self.queue.put(("finished", None))
    
    def process_single_file(self, file_path):
        try:
            self.queue.put(("progress", 10))
            self.queue.put(("status", "Анализирую файл..."))
            
            result = self.analyzer.analyze_file(file_path)
            
            if result:
                results = [result]
                self.queue.put(("results", results))
                self.queue.put(("status", "Файл успешно проанализирован"))
            else:
                self.queue.put(("error", "Не удалось проанализировать файл"))
            
            self.queue.put(("progress", 100))
            
        except Exception as e:
            self.queue.put(("error", f"Ошибка при анализе: {str(e)}"))
        finally:
            self.queue.put(("finished", None))
    
    def stop_processing(self):
        if self.is_processing:
            self.is_processing = False
            self.update_status("Остановка...")
            messagebox.showinfo("Информация", "Остановка будет выполнена после завершения текущих операций")
    
    def check_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == "progress":
                    self.progress_var.set(data)
                elif msg_type == "status":
                    self.update_status(data)
                elif msg_type == "results":
                    self.display_results(data)
                elif msg_type == "error":
                    messagebox.showerror("Ошибка", data)
                    self.processing_finished()
                elif msg_type == "finished":
                    self.processing_finished()
                
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_queue)
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def display_results(self, results):
        self.current_results = results
        self.clear_table()
        
        for info in results:
            if info.resolution_x is not None and info.resolution_y is not None:
                resolution = f"{info.resolution_x:.1f}×{info.resolution_y:.1f}"
            else:
                resolution = "N/A"
            
            size_mb = info.file_size / (1024 * 1024)
            
            self.tree.insert("", tk.END, values=(
                info.filename,
                f"{info.width}×{info.height}",
                resolution,
                f"{info.color_depth} бит",
                info.compression,
                info.format,
                f"{size_mb:.2f} MB"
            ))
        
        total_size = sum(info.file_size for info in results)
        total_size_mb = total_size / (1024 * 1024)
        
        self.total_files_label.config(text=f"Файлов: {len(results)}")
        self.total_size_label.config(text=f"Общий размер: {total_size_mb:.2f} MB")
        self.time_label.config(text=f"Время: {self.analyzer.processing_time:.2f} сек")
    
    def processing_finished(self):
        self.is_processing = False
        self.progress_var.set(0)
        
        self.stop_button.configure(state=tk.DISABLED)
    
    def show_file_details(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        for info in self.current_results:
            if info.filename == filename:
                self.show_details_window(info)
                break
    
    def show_details_window(self, info):
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали: {info.filename}")
        details_window.geometry("600x500")
        details_window.transient(self.root)
        details_window.grab_set()
        
        main_frame = ttk.Frame(details_window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        details_window.columnconfigure(0, weight=1)
        details_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        ttk.Label(main_frame, text="Имя файла:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=info.filename).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Путь:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        path_label = ttk.Label(main_frame, text=info.filepath, wraplength=400)
        path_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Размер файла:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        size_mb = info.file_size / (1024 * 1024)
        ttk.Label(main_frame, text=f"{info.file_size:,} байт ({size_mb:.2f} MB)").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Размер изображения:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=f"{info.width} × {info.height} пикселей").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Разрешение:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        if info.resolution_x is not None and info.resolution_y is not None:
            resolution = f"{info.resolution_x:.1f} × {info.resolution_y:.1f} DPI"
        else:
            resolution = "N/A"
        ttk.Label(main_frame, text=resolution).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Глубина цвета:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=f"{info.color_depth} бит").grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Сжатие:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=info.compression).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Формат:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=info.format).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        if info.palette_colors > 0:
            ttk.Label(main_frame, text="Цвета в палитре:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
            ttk.Label(main_frame, text=str(info.palette_colors)).grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1
        
        if info.additional_info:
            ttk.Label(main_frame, text="Дополнительная информация:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
            row += 1
            
            for key, value in info.additional_info.items():
                if isinstance(value, list):
                    ttk.Label(main_frame, text=f"{key}:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=2)
                    for i, item in enumerate(value):
                        ttk.Label(main_frame, text=f"  {item}").grid(row=row+i, column=1, sticky=tk.W, pady=2)
                    row += len(value)
                else:
                    ttk.Label(main_frame, text=f"{key}:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=2)
                    ttk.Label(main_frame, text=str(value)).grid(row=row, column=1, sticky=tk.W, pady=2)
                    row += 1
        
        ttk.Button(main_frame, text="Закрыть", command=details_window.destroy).grid(row=row, column=0, columnspan=2, pady=20)
    
    def export_csv(self):
        if not self.current_results:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile=f"image_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Имя файла;Путь;Размер файла (байт);Ширина;Высота;Разрешение X;Разрешение Y;Глубина цвета;Сжатие;Формат;Цвета в палитре\n")
                    
                    for info in self.current_results:
                        f.write(
                            f"{info.filename};"
                            f"{info.filepath};"
                            f"{info.file_size};"
                            f"{info.width};"
                            f"{info.height};"
                            f"{info.resolution_x or 0};"
                            f"{info.resolution_y or 0};"
                            f"{info.color_depth};"
                            f"{info.compression};"
                            f"{info.format};"
                            f"{info.palette_colors}\n"
                        )
                
                messagebox.showinfo("Успех", f"Результаты экспортированы в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def export_txt(self):
        if not self.current_results:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            initialfile=f"image_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 120 + "\n")
                    f.write(f"{'Имя файла':<30} {'Размер (пикс)':<15} {'Разрешение':<15} {'Глубина цвета':<15} {'Сжатие':<15} {'Формат':<10}\n")
                    f.write("-" * 120 + "\n")
                    
                    for info in self.current_results:
                        if info.resolution_x is not None and info.resolution_y is not None:
                            resolution = f"{info.resolution_x:.1f}×{info.resolution_y:.1f}"
                        else:
                            resolution = "N/A"
                        f.write(
                            f"{info.filename:<30} "
                            f"{info.width}×{info.height:<12} "
                            f"{resolution:<15} "
                            f"{info.color_depth} бит{'':<9} "
                            f"{info.compression:<15} "
                            f"{info.format:<10}\n"
                        )
                    
                    f.write("=" * 120 + "\n")
                    
                    total_size = sum(info.file_size for info in self.current_results)
                    f.write(f"\nСтатистика:\n")
                    f.write(f"Всего файлов: {len(self.current_results)}\n")
                    f.write(f"Общий размер: {total_size / (1024*1024):.2f} MB\n")
                    f.write(f"Время обработки: {self.analyzer.processing_time:.2f} сек\n")
                
                messagebox.showinfo("Успех", f"Результаты экспортированы в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def show_help(self):
        help_text = """Анализатор графических файлов

Поддерживаемые форматы:
• JPEG (.jpg, .jpeg)
• GIF (.gif)
• TIFF (.tif, .tiff)
• BMP (.bmp)
• PNG (.png)
• PCX (.pcx)

Функции:
1. Анализ папки - обработка всех графических файлов в выбранной папке
2. Анализ одного файла - детальный анализ выбранного файла
3. Экспорт результатов - сохранение в CSV или TXT формате
4. Детальная информация - двойной клик по файлу в таблице

Настройки:
• Максимальное количество файлов - ограничение для анализа папки
• Многопоточность - ускорение обработки больших папок

Требования:
• Установленный Python 3.7+
• Библиотека Pillow (установка: pip install Pillow)
• Опционально: numpy, jpegio для расширенной функциональности"""
        
        messagebox.showinfo("Справка", help_text)

def main():
    try:
        root = tk.Tk()
        app = ImageAnalyzerGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        messagebox.showerror("Критическая ошибка", str(e))

if __name__ == "__main__":
    try:
        from PIL import Image
        HAS_PIL = True
    except ImportError:
        messagebox.showerror("Ошибка", "Не установлена библиотека Pillow\nУстановите: pip install Pillow")
        sys.exit(1)
    
    main()