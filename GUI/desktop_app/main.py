import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pytesseract
import sqlite3
import os
from datetime import datetime

os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# ABSTRAKSI: Kelas utama sebagai abstraksi aplikasi
class ImageTextExtractorApp:
    # ENKAPSULASI: Variabel internal dan metode database
    def __init__(self, root):
        # ENKAPSULASI: Variabel internal
        self.root = root
        self.current_edit_id = None  # ID data yang sedang diedit
        self.current_delete_id = None  # ID data yang akan dihapus
        
        # Inisialisasi database dan UI
        self.check_database()
        self.create_main_page()

    # ENKAPSULASI: Metode untuk manajemen database
    def check_database(self):
        """Abstraksi proses setup database"""
        conn = sqlite3.connect('../data/ekstraksi.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_ekstraksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_file TEXT,
                lokasi_file TEXT,
                hasil_ekstraksi TEXT,
                tanggal_input TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

     # ABSTRAKSI: Metode untuk membuat halaman utama
    def create_main_page(self):
        self.clear_window()
        self.root.title("Aplikasi Ekstraksi Teks dari Citra")

    # Warna tema
        bg_main = "#f8f9fa"
        bg_section = "#e9ecef"
        btn_color = "#007bff"
        btn_fg = "#ffffff"

    # Main container dengan warna background
        main_frame = tk.Frame(self.root, bg=bg_main)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

    # Search Section
        search_frame = tk.Frame(main_frame, bg=bg_main)
        search_frame.grid(row=0, column=0, sticky="ew", pady=5)

        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.insert(0, "Tulis lalu Enter untuk mencari")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END))
        self.search_entry.bind("<Return>", self.search_data)
        self.search_entry.pack(side=tk.LEFT, padx=5)

    # Table Section
        table_frame = tk.Frame(main_frame, bg=bg_main)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.table = ttk.Treeview(table_frame, columns=("id", "Nomor", "Nama File", "Lokasi File", "Tanggal Input", "Hasil Ekstraksi"), show="headings", height=10)
        self.table.column("id", width=0, stretch=tk.NO)
        self.table.column("Nomor", width=50, anchor="center")
        self.table.column("Nama File", width=150)
        self.table.column("Lokasi File", width=200)
        self.table.column("Tanggal Input", width=100, anchor="center")  # Kolom tanggal dipindah ke sebelum hasil
        self.table.column("Hasil Ekstraksi", width=250, stretch=tk.YES)  # Lebar menyesuaikan isi teks

        self.table.heading("Nomor", text="Nomor")
        self.table.heading("Nama File", text="Nama File")
        self.table.heading("Lokasi File", text="Lokasi File")
        self.table.heading("Tanggal Input", text="Tanggal Input")  # Urutan heading diubah
        self.table.heading("Hasil Ekstraksi", text="Hasil Ekstraksi")

        self.table.bind('<<TreeviewSelect>>', self.on_row_select)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.table.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

    # Preview Section
        preview_frame = tk.Frame(main_frame, bg=bg_main)
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(1, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        left_preview = tk.LabelFrame(preview_frame, text="Pratinjau Gambar", padx=5, pady=5, bg=bg_section)
        left_preview.grid(row=0, column=0, sticky="nsew", padx=5)

        right_preview = tk.LabelFrame(preview_frame, text="Hasil Ekstraksi Teks", padx=5, pady=5, bg=bg_section)
        right_preview.grid(row=0, column=1, sticky="nsew", padx=5)

        img_canvas = tk.Canvas(left_preview, bg="#f0f0f0")
        img_scroll_y = ttk.Scrollbar(left_preview, orient="vertical", command=img_canvas.yview)
        img_scroll_x = ttk.Scrollbar(left_preview, orient="horizontal", command=img_canvas.xview)
        img_canvas.configure(yscrollcommand=img_scroll_y.set, xscrollcommand=img_scroll_x.set)

        img_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        img_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Container frame di dalam canvas
        self.img_container = tk.Frame(img_canvas, bg="#f8f8f8")
        canvas_window = img_canvas.create_window((0, 0), window=self.img_container, anchor="nw")

        self.img_label = tk.Label(self.img_container, bg="#f8f8f8")
        self.img_label.pack(padx=10, pady=10)

    # Fungsi konfigurasi canvas seperti di add_page
        def configure_canvas(event):
            img_canvas.configure(scrollregion=img_canvas.bbox("all"))
            img_canvas.itemconfig(canvas_window, width=event.width)

        img_canvas.bind("<Configure>", configure_canvas)
        self.img_container.bind("<Configure>", lambda e: img_canvas.configure(scrollregion=img_canvas.bbox("all")))

    # Text Preview
        text_scroll = ttk.Scrollbar(right_preview, orient="vertical")
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_preview = tk.Text(right_preview, width=40, height=8, wrap=tk.WORD, 
                           yscrollcommand=text_scroll.set, state='disabled',
                           font=('Courier New', 10), padx=10, pady=10)
        self.text_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        text_scroll.config(command=self.text_preview.yview)

    # Buttons Section
        btn_frame = tk.Frame(main_frame, bg=bg_main)
        btn_frame.grid(row=3, column=0, sticky="ew", pady=10)

        tk.Button(btn_frame, text="Tambah Data", width=15, bg=btn_color, fg=btn_fg, command=self.create_add_page).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Ubah Data", width=15, bg=btn_color, fg=btn_fg, command=self.prepare_edit_page).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Hapus Data", width=15, bg=btn_color, fg=btn_fg, command=self.prepare_delete_page).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Keluar", width=15, bg="#dc3545", fg=btn_fg, command=self.root.quit).pack(side=tk.LEFT, padx=5)

        self.load_data_to_table()

    # Tambahkan metode untuk menampilkan gambar yang dipilih
    def on_row_select(self, event):
        selected_items = self.table.selection()
        if selected_items:
        # Dapatkan data yang dipilih
            item = self.table.item(selected_items[0])
            values = item['values']
        
        # Dapatkan ID data yang dipilih
            data_id = values[0]
            image_path = values[3]  # Lokasi file
        
            try:
            # Ambil hasil ekstraksi lengkap dari database berdasarkan ID
                conn = sqlite3.connect('../data/ekstraksi.db')
                cursor = conn.cursor()
                cursor.execute("SELECT hasil_ekstraksi FROM data_ekstraksi WHERE id=?", (data_id,))
                hasil_lengkap = cursor.fetchone()[0]
                conn.close()
            
            # Membuka gambar
                img = Image.open(image_path)
            
            # Menyesuaikan ukuran dengan mempertahankan rasio aspek
                width, height = img.size
                new_width = 300
                new_height = int(height * (new_width / width))
            
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Konversi ke format yang dapat ditampilkan Tkinter
                photo = ImageTk.PhotoImage(resized_img)
            
            # Simpan referensi agar tidak di-garbage collect
                self.photo = photo
            
            # Tampilkan di label
                self.img_label.config(image=photo)
            
            # Tampilkan teks hasil ekstraksi lengkap dari database
                self.text_preview.config(state='normal')  # Aktifkan sementara untuk edit
                self.text_preview.delete(1.0, tk.END)
                self.text_preview.insert(tk.END, hasil_lengkap)  # Hasil ekstraksi lengkap
                self.text_preview.config(state='disabled')  # Nonaktifkan kembali
            
            except Exception as e:
                self.text_preview.config(state='normal')
                self.text_preview.delete(1.0, tk.END)
                self.text_preview.insert(tk.END, "Gagal memuat pratinjau")
                self.text_preview.config(state='disabled')
                messagebox.showerror("Error", f"Gagal memuat gambar: {str(e)}")

    # POLIMORFISME: Method load_data_to_table memiliki perilaku berbeda berdasarkan tipe query
    def load_data_to_table(self, query=None):
        """Enkapsulasi proses loading data"""
        for row in self.table.get_children():
            self.table.delete(row)
            
        conn = sqlite3.connect('../data/ekstraksi.db')
        cursor = conn.cursor()
        
        # POLIMORFISME: Perilaku berbeda berdasarkan tipe query
        if query:
            if query.isdigit():
                cursor.execute("SELECT * FROM data_ekstraksi WHERE id=?", (query,))
            else:
                cursor.execute("SELECT * FROM data_ekstraksi WHERE nama_file LIKE ?", (f'%{query}%',))
        else:
            cursor.execute("SELECT * FROM data_ekstraksi")
        
        rows = cursor.fetchall()
        for index, row in enumerate(rows, start=1):
            # Ambil hanya baris pertama dari hasil ekstraksi
            hasil_ekstraksi = row[3].split('\n')[0] if row[3] and '\n' in row[3] else row[3]
            
            # Masukkan ke tabel dengan hasil ekstraksi yang sudah difilter
            self.table.insert("", "end", values=(row[0], index, row[1], row[2], row[4], hasil_ekstraksi))
        conn.close()

    def search_data(self, event=None):
        query = self.search_entry.get().strip()

    # Cek jika kolom pencarian kosong
        if not query or query == "Tulis lalu Enter untuk mencari":
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, "Tulis lalu Enter untuk mencari")
            self.load_data_to_table()  # Mengambil semua data saat pencarian kosong
            return

        conn = sqlite3.connect('../data/ekstraksi.db')
        cursor = conn.cursor()

    # Cek apakah query berupa angka (ID) atau nama file
        if query.isdigit():
            cursor.execute("SELECT * FROM data_ekstraksi WHERE id=?", (query,))
        else:
            cursor.execute("SELECT * FROM data_ekstraksi WHERE nama_file LIKE ?", (f'%{query}%',))

        rows = cursor.fetchall()
        conn.close()

    # Clear table first
        for row in self.table.get_children():
            self.table.delete(row)

    # Cek jika ada data yang ditemukan
        if rows:
            for index, row in enumerate(rows, start=1):
            # Ambil hanya baris pertama dari hasil ekstraksi
                hasil_ekstraksi = row[3].split('\n')[0] if row[3] and '\n' in row[3] else row[3]
            
            # Masukkan ke tabel dengan hasil ekstraksi yang sudah difilter
                self.table.insert("", "end", values=(row[0], index, row[1], row[2], row[4], hasil_ekstraksi))

        # Update notifikasi
            messagebox.showinfo("Sukses", f"Data dengan query '{query}' ditemukan")
        
        # Tampilkan preview gambar & teks untuk hasil pertama
            self.show_preview(rows[0])  # Menampilkan pratinjau dari hasil pertama pencarian
        else:
            messagebox.showwarning("Tidak ditemukan", f"'{query}' tidak ditemukan.")
            self.img_label.config(image='')  # Hapus pratinjau gambar
            self.text_preview.config(state='normal')
            self.text_preview.delete(1.0, tk.END)
            self.text_preview.config(state='disabled')

    def show_preview(self, result):
        """Menampilkan preview gambar dan teks berdasarkan hasil pencarian"""
        try:
            img = Image.open(result[2])  # Ambil path gambar dari data
            width, height = img.size
            new_width = 300
            new_height = int(height * (new_width / width))
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized_img)
            self.photo = photo  # Simpan referensi gambar

            self.img_label.config(image=photo)

        # Tampilkan hasil ekstraksi dalam preview
            self.text_preview.config(state='normal')
            self.text_preview.delete(1.0, tk.END)
            self.text_preview.insert(tk.END, result[3])  # Menampilkan teks ekstraksi
            self.text_preview.config(state='disabled')
        except Exception as e:
            self.img_label.config(image='')  # Hapus gambar jika gagal
            self.text_preview.config(state='normal')
            self.text_preview.delete(1.0, tk.END)
            self.text_preview.insert(tk.END, "Gagal menampilkan pratinjau.")
            self.text_preview.config(state='disabled')

    # ABSTRAKSI: Membuat halaman tambah data
    def create_add_page(self):
        self.clear_window()

        self.root.title("Tambah Data Baru - Aplikasi Ekstraksi Teks dari Citra")

    # Main container
        add_frame = tk.Frame(self.root, bg="#f5f5f5")
        add_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Judul
        tk.Label(add_frame, text="Tambah Data Baru", font=('Arial', 14, 'bold'), 
                 bg="#f5f5f5", fg="#333333").grid(row=0, column=0, columnspan=3, pady=10, sticky='w')

    # File Input dengan frame sendiri
        file_frame = tk.Frame(add_frame, bg="#f5f5f5")
        file_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=10)

        tk.Label(file_frame, text="File Gambar:", bg="#f5f5f5", fg="#333333").pack(side=tk.LEFT, padx=5)
        self.add_file_entry = tk.Entry(file_frame, width=50)
        self.add_file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
        browse_btn = tk.Button(file_frame, text="Buka File", 
                               bg="#2196F3", fg="white",
                               activebackground="#0b7dda",
                               command=lambda: self.open_file(self.add_file_entry))
        browse_btn.pack(side=tk.LEFT, padx=5)

    # Preview Section dalam LabelFrame
        preview_container = tk.Frame(add_frame, bg="#f5f5f5")
        preview_container.grid(row=2, column=0, columnspan=3, sticky='nsew', pady=10)
        add_frame.grid_columnconfigure(0, weight=1)
        add_frame.grid_rowconfigure(2, weight=1)

    # Image Preview Frame (kiri) dengan scrollbar
        img_frame = tk.LabelFrame(preview_container, text="Pratinjau Gambar", 
                                bg="#ffffff", fg="#333333",
                                font=('Arial', 9, 'bold'),
                                padx=10, pady=10,
                                relief=tk.GROOVE, borderwidth=2)
        img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

    # Canvas dan scrollbar untuk gambar
        img_canvas = tk.Canvas(img_frame, bg="#f8f8f8")
        img_scroll_y = ttk.Scrollbar(img_frame, orient="vertical", command=img_canvas.yview)
        img_scroll_x = ttk.Scrollbar(img_frame, orient="horizontal", command=img_canvas.xview)
    
        img_canvas.configure(yscrollcommand=img_scroll_y.set, xscrollcommand=img_scroll_x.set)

        img_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        img_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Frame untuk konten gambar di dalam canvas
        self.add_img_container = tk.Frame(img_canvas, bg="#f8f8f8")
        canvas_window = img_canvas.create_window((0, 0), window=self.add_img_container, anchor="nw")
    
    # Label untuk gambar di dalam container
        self.add_img_label = tk.Label(self.add_img_container, bg="#f8f8f8")
        self.add_img_label.pack(padx=10, pady=10)
    
    # Fungsi untuk mengatur canvas saat ukuran berubah
        def configure_canvas(event):
        # Update scrollregion saat ukuran container berubah
            img_canvas.configure(scrollregion=img_canvas.bbox("all"))
        
        # Sesuaikan lebar frame container dengan lebar canvas
            img_canvas.itemconfig(canvas_window, width=event.width)
    
    # Binding event untuk update canvas
        img_canvas.bind("<Configure>", configure_canvas)
        self.add_img_container.bind("<Configure>", lambda e: img_canvas.configure(scrollregion=img_canvas.bbox("all")))

    # Text Preview Frame (kanan)
        text_frame = tk.LabelFrame(preview_container, text="Hasil Ekstraksi Teks", 
                                bg="#f0f7ff", fg="#0066cc",
                                font=('Arial', 9, 'bold'),
                                padx=10, pady=10,
                                relief=tk.RIDGE, borderwidth=2)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    # Text area untuk menampilkan hasil ekstraksi (read-only)
        self.add_text_preview = tk.Text(text_frame, width=40, height=15, 
                                    bg="white", fg="#333333", state='disabled',
                                    font=('Courier New', 10), padx=10, pady=10)
        self.add_text_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Tombol di frame terpisah
        button_frame = tk.Frame(add_frame, bg="#f5f5f5")
        button_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky='e')
    
        clear_btn = tk.Button(button_frame, text="Batal", width=15,
                            bg="#f44336", fg="white",
                            activebackground="#d32f2f",
                            command=self.clear_add_form)
        clear_btn.pack(side=tk.LEFT, padx=5)
    
        save_btn = tk.Button(button_frame, text="Simpan", width=15,
                            bg="#4CAF50", fg="white",
                            activebackground="#45a049",
                            command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(button_frame, text="Kembali", width=15,
                            bg="#2196F3", fg="white",
                            activebackground="#0b7dda",
                            command=self.create_main_page)
        back_btn.pack(side=tk.LEFT, padx=5)

    # Terapkan efek hover jika metode apply_hover_effect sudah ada
        if hasattr(self, 'apply_hover_effect'):
            self.apply_hover_effect(back_btn, "#2196F3", "#0b7dda")
            self.apply_hover_effect(clear_btn, "#f44336", "#d32f2f")
            self.apply_hover_effect(save_btn, "#4CAF50", "#45a049")
            self.apply_hover_effect(browse_btn, "#2196F3", "#0b7dda")
    
    def clear_add_form(self):
        """Membersihkan form tambah data"""
        self.add_file_entry.delete(0, tk.END)
        self.add_img_label.config(image='')
        self.add_text_preview.config(state='normal')
        self.add_text_preview.delete(1.0, tk.END)
        self.add_text_preview.config(state='disabled')
        self.current_img_ref = None  # Hapus referensi gambar

    def open_file(self, entry_widget):
        """Buka dialog file untuk memilih gambar"""
        file_path = filedialog.askopenfilename(
            title="Pilih File Gambar",
            filetypes=[
                ("File Gambar", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("Semua File", "*.*")
            ]
        )
    
        if file_path:
        # Update entry dengan path file baru
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
        
        # Tampilkan preview gambar
            self.show_image_preview(file_path)
        
        # Ekstrak teks dari gambar
            self.extract_text_from_image(file_path)


    def open_file_edit(self, entry_widget):
        file_path = filedialog.askopenfilename(
            title="Pilih File Gambar",
            filetypes=[
                ("File Gambar", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                ("Semua File", "*.*")
            ]
        )
    
        if file_path:
        # Update entry dengan path file baru
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
        
        # Update komponen lainnya
            file_name = os.path.basename(file_path)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update Entry widgets di halaman edit
            self.edit_nama_file.delete(0, tk.END)
            self.edit_nama_file.insert(0, file_name)
        
            self.edit_lokasi_file.delete(0, tk.END)
            self.edit_lokasi_file.insert(0, file_path)
        
            self.edit_tanggal_input.delete(0, tk.END)
            self.edit_tanggal_input.insert(0, current_time)
        
        # Tampilkan preview dan ekstrak teks
            self.show_image_preview_edit(file_path)
            self.extract_text_edit(file_path)

    def show_image_preview_edit(self, file_path):
        """Menampilkan preview gambar pada halaman edit"""
        try:
        # Cek apakah file ada
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File tidak ditemukan: {file_path}")
                return
        
        # Buka dan resize gambar untuk preview
            original_img = Image.open(file_path)
        
        # Tentukan ukuran maksimum untuk preview (width, height)
            max_width = 400
            max_height = 500
        
        # Hitung rasio aspek untuk mempertahankan proporsi
            width, height = original_img.size
            aspect_ratio = width / height
        
        # Atur ukuran baru dengan mempertahankan rasio aspek
            if width > height:
                new_width = min(width, max_width)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(height, max_height)
                new_width = int(new_height * aspect_ratio)
        
        # Resize gambar
            resized_img = original_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Konversi ke format Tkinter
            tk_img = ImageTk.PhotoImage(resized_img)
        
        # Simpan referensi ke gambar di variabel khusus edit (mencegah garbage collection)
            self.edit_img_ref = tk_img  # Perubahan di sini
        
        # Update label
            self.edit_img_label.config(image=tk_img)
        
        except Exception as e:
            messagebox.showerror("Error", f"Tidak dapat menampilkan gambar: {str(e)}")

    def extract_text_edit(self, image_path):
        try:
            text = pytesseract.image_to_string(Image.open(image_path)).strip()

            self.edit_text_preview.delete(1.0, tk.END)
            self.edit_text_preview.insert(tk.END, text)

            if not text:
                messagebox.showwarning("Peringatan", "Gambar tidak mengandung teks yang dapat dikenali")
            else:
                messagebox.showinfo("Berhasil", "Teks berhasil diekstraksi dari gambar")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengekstrak teks: {str(e)}")


    def show_image_preview(self, file_path):
        """Menampilkan preview gambar dengan ukuran asli (dengan scrolling jika perlu)"""
        try:
        # Cek apakah file ada
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File tidak ditemukan: {file_path}")
                return
            
        # Buka gambar
            original_img = Image.open(file_path)
        
        # Mendapatkan ukuran asli gambar
            width, height = original_img.size
        
        # Batasi ukuran maksimum lebar untuk preview (sesuai dengan ukuran canvas)
            max_width = 400  # Ukuran maksimum yang ingin ditampilkan
        
        # Jika lebar gambar lebih dari ukuran maksimum, resize dengan mempertahankan aspek ratio
            if width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)
                resized_img = original_img.resize((new_width, new_height), Image.LANCZOS)
            else:
                # Gunakan ukuran asli jika gambar tidak terlalu lebar
                resized_img = original_img
            
        # Konversi ke format Tkinter
            tk_img = ImageTk.PhotoImage(resized_img)
        
        # Simpan referensi ke gambar (mencegah garbage collection)
            self.current_img_ref = tk_img
        
        # Update label gambar
            self.add_img_label.config(image=tk_img)
        
        except Exception as e:
            messagebox.showerror("Error", f"Tidak dapat menampilkan gambar: {str(e)}")

    # ENKAPSULASI: Method untuk ekstraksi teks
    def extract_text_from_image(self, file_path):
        """Abstraksi proses ekstraksi teks"""
        try:
            extracted_text = pytesseract.image_to_string(Image.open(file_path), lang='ind')
            self.add_text_preview.config(state='normal')
            self.add_text_preview.delete(1.0, tk.END)
            self.add_text_preview.insert(tk.END, extracted_text)
            messagebox.showinfo("Berhasil", "Teks berhasil diekstrak dari gambar.")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengekstrak teks: {str(e)}")

    # INHERITANCE: Menggunakan komposisi dengan inner class DatabaseManager
    class DatabaseManager:  # Contoh inner class untuk enkapsulasi database
        # ENKAPSULASI: Variabel internal dan metode database
        def __init__(self, db_path):
            self.conn = sqlite3.connect(db_path)
        
        def execute_query(self, query, params=()):
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor

    def save_data(self):
        """Menyimpan data baru ke database"""
        try:
        # Ambil data dari form
            file_path = self.add_file_entry.get()
        
            if not file_path:
                messagebox.showerror("Error", "Silakan pilih file gambar terlebih dahulu!")
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File tidak ditemukan: {file_path}")
                return
            
        # Ambil nama file dari path
            file_name = os.path.basename(file_path)
        
        # Ambil teks hasil ekstraksi
            extracted_text = self.add_text_preview.get("1.0", tk.END).strip()
        
        # Tanggal saat ini
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Simpan ke database
            conn = sqlite3.connect('../data/ekstraksi.db')
            cursor = conn.cursor()
        
            cursor.execute("""
                INSERT INTO data_ekstraksi (nama_file, lokasi_file, hasil_ekstraksi, tanggal_input)
                VALUES (?, ?, ?, ?)
            """, (file_name, file_path, extracted_text, current_date))
        
            conn.commit()
            conn.close()
        
            messagebox.showinfo("Sukses", "Data berhasil disimpan!")
        
        # Bersihkan form
            self.clear_add_form()
        
        # Kembali ke halaman utama
            self.create_main_page()
        
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan data: {str(e)}")

    # Halaman Edit Data
    def prepare_edit_page(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih data yang akan diubah")
            return
    
    # Ambil nomor urut dari kolom kedua tabel
        selected_item = self.table.item(selected[0])
        self.current_edit_nomor = selected_item['values'][1]  # [0]=id, [1]=nomor
        self.current_edit_id = selected_item['values'][0]     # ID database
        self.create_edit_page()

    def create_edit_page(self): 
        self.clear_window()
        self.root.title("Ubah Data - Aplikasi Ekstraksi Teks dari Citra")

    # Main container
        edit_frame = tk.Frame(self.root, bg="#f5f5f5")
        edit_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Judul
        header_frame = tk.Frame(edit_frame, bg="#f5f5f5")
        header_frame.grid(row=0, column=0, columnspan=3, pady=10, sticky='ew')
        
        # Judul di tengah
        tk.Label(header_frame, text="Ubah Data", font=('Arial', 14, 'bold'), 
                 bg="#f5f5f5", fg="#333333").pack(side=tk.LEFT, padx=10)

    # Ambil data
        conn = sqlite3.connect('../data/ekstraksi.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_ekstraksi WHERE id=?", (self.current_edit_id,))
        data = cursor.fetchone()
        conn.close()
        
        # Simpan data asli untuk fungsi batal
        self.original_data = data

    # File input
        file_frame = tk.Frame(edit_frame, bg="#f5f5f5")
        file_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=10)

        tk.Label(file_frame, text="File Gambar:", bg="#f5f5f5", fg="#333333").pack(side=tk.LEFT, padx=5)
        self.edit_file_entry = tk.Entry(file_frame, width=50)
        self.edit_file_entry.insert(0, data[2])
        self.edit_file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = tk.Button(file_frame, text="Buka File", 
                               bg="#2196F3", fg="white", activebackground="#0b7dda",
                               command=lambda: self.open_file_edit(self.edit_file_entry))
        browse_btn.pack(side=tk.LEFT, padx=5)

    # Preview
        preview_container = tk.Frame(edit_frame, bg="#f5f5f5")
        preview_container.grid(row=2, column=0, columnspan=3, sticky='nsew', pady=10)
        edit_frame.grid_columnconfigure(0, weight=1)
        edit_frame.grid_rowconfigure(2, weight=1)

    # Gambar
        img_frame = tk.LabelFrame(preview_container, text="Pratinjau Gambar", 
                                  bg="#ffffff", fg="#333333", font=('Arial', 9, 'bold'),
                                  padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
        img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        img_canvas = tk.Canvas(img_frame, bg="#f8f8f8")
        img_scroll_y = ttk.Scrollbar(img_frame, orient="vertical", command=img_canvas.yview)
        img_scroll_x = ttk.Scrollbar(img_frame, orient="horizontal", command=img_canvas.xview)

        img_canvas.configure(yscrollcommand=img_scroll_y.set, xscrollcommand=img_scroll_x.set)
        img_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        img_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.edit_img_container = tk.Frame(img_canvas, bg="#f8f8f8")
        canvas_window = img_canvas.create_window((0, 0), window=self.edit_img_container, anchor="nw")

        self.edit_img_label = tk.Label(self.edit_img_container, bg="#f8f8f8")
        self.edit_img_label.pack(padx=10, pady=10)

        def configure_canvas(event):
            img_canvas.configure(scrollregion=img_canvas.bbox("all"))
            img_canvas.itemconfig(canvas_window, width=event.width)

        img_canvas.bind("<Configure>", configure_canvas)
        self.edit_img_container.bind("<Configure>", lambda e: img_canvas.configure(scrollregion=img_canvas.bbox("all")))

    # Teks
        text_frame = tk.LabelFrame(preview_container, text="Hasil Ekstraksi Teks", 
                                   bg="#f0f7ff", fg="#0066cc", font=('Arial', 9, 'bold'),
                                   padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        self.edit_text_preview = tk.Text(text_frame, width=40, height=15,
                                         bg="white", fg="#333333",
                                         font=('Courier New', 10), padx=10, pady=10)
        self.edit_text_preview.insert(tk.END, data[3])
        self.edit_text_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Detail data
        data_frame = tk.LabelFrame(edit_frame, text="Detail Data", bg="#f5f5f5",
                                   padx=10, pady=10)
        data_frame.grid(row=3, column=0, columnspan=3, sticky='nsew', pady=10)
        data_frame.grid_columnconfigure(1, weight=1)

        # Ubah Label menjadi Entry untuk field yang dapat diedit
        tk.Label(data_frame, text="Nomor:", font=('Arial', 9, 'bold'),
                 bg="#f5f5f5", fg="#333333").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        tk.Label(data_frame, text=str(self.current_edit_nomor), bg="#f5f5f5", fg="#333333").grid(row=0, column=1, sticky='w', pady=5)

        tk.Label(data_frame, text="Nama File:", font=('Arial', 9, 'bold'),
                 bg="#f5f5f5", fg="#333333").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.edit_nama_file = tk.Entry(data_frame, width=40, bg="white")
        self.edit_nama_file.insert(0, data[1])
        self.edit_nama_file.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        tk.Label(data_frame, text="Lokasi File:", font=('Arial', 9, 'bold'),
                 bg="#f5f5f5", fg="#333333").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.edit_lokasi_file = tk.Entry(data_frame, width=40, bg="white")
        self.edit_lokasi_file.insert(0, data[2])
        self.edit_lokasi_file.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        tk.Label(data_frame, text="Tanggal Input:", font=('Arial', 9, 'bold'),
                 bg="#f5f5f5", fg="#333333").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.edit_tanggal_input = tk.Entry(data_frame, width=40, bg="white")
        self.edit_tanggal_input.insert(0, data[4])
        self.edit_tanggal_input.grid(row=3, column=1, sticky='w', padx=5, pady=5)

    # Tombol
        button_frame = tk.Frame(edit_frame, bg="#f5f5f5")
        button_frame.grid(row=4, column=0, columnspan=3, pady=15, sticky='e')

        save_btn = tk.Button(button_frame, text="Simpan Perubahan", width=15,
                             bg="#4CAF50", fg="white", activebackground="#45a049",
                             command=self.update_data)
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(button_frame, text="Batal", width=15,
                               bg="#f44336", fg="white", activebackground="#d32f2f",
                               command=self.reset_form)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(button_frame, text="Kembali", width=15,
                            bg="#2196F3", fg="white",
                            activebackground="#0b7dda",
                            command=self.create_main_page)
        back_btn.pack(side=tk.LEFT, padx=5)

    # Efek hover
        if hasattr(self, 'apply_hover_effect'):
            self.apply_hover_effect(save_btn, "#4CAF50", "#45a049")
            self.apply_hover_effect(cancel_btn, "#f44336", "#d32f2f")
            self.apply_hover_effect(browse_btn, "#2196F3", "#0b7dda")
            self.apply_hover_effect(back_btn, "#607D8B", "#455A64")

    # Tampilkan gambar
        self.show_image_preview_edit(data[2])

    def reset_form(self):
        """Mengembalikan form ke data asli sebelum diedit"""
        if hasattr(self, 'original_data'):
        # Kembalikan nilai-nilai ke data asli
            self.edit_nama_file.delete(0, tk.END)
            self.edit_nama_file.insert(0, self.original_data[1])
        
            self.edit_lokasi_file.delete(0, tk.END)
            self.edit_lokasi_file.insert(0, self.original_data[2])
        
            self.edit_file_entry.delete(0, tk.END)
            self.edit_file_entry.insert(0, self.original_data[2])
        
            self.edit_tanggal_input.delete(0, tk.END)
            self.edit_tanggal_input.insert(0, self.original_data[4])
        
        # Kembalikan hasil ekstraksi
            self.edit_text_preview.delete(1.0, tk.END)
            self.edit_text_preview.insert(tk.END, self.original_data[3])
        
        # Tampilkan ulang gambar
            self.show_image_preview_edit(self.original_data[2])
        
            messagebox.showinfo("Reset Berhasil", "Data telah dikembalikan ke semula")

    def update_data(self):
        try:
        # Ambil nilai dari form
            file_path = self.edit_file_entry.get()
            nama_file = self.edit_nama_file.get()  # Ambil dari field nama file yang dapat diedit
            lokasi_file = self.edit_lokasi_file.get()  # Ambil dari field lokasi file yang dapat diedit
            tanggal_input = self.edit_tanggal_input.get()  # Ambil dari field tanggal yang dapat diedit
            text_content = self.edit_text_preview.get("1.0", tk.END).strip()
        
        # Gunakan tanggal input yang dimasukkan user, jika kosong gunakan waktu saat ini
            if not tanggal_input:
                tanggal_input = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Validasi
            if not file_path or not lokasi_file:
                messagebox.showerror("Error", "Lokasi file tidak boleh kosong!")
                return
        
        # Jika nama file kosong, gunakan nama file dari path
            if not nama_file:
                nama_file = os.path.basename(file_path)
        
        # Cek apakah file ada di lokasi_file (yang bisa saja diubah oleh user)
            if not os.path.exists(lokasi_file):
                response = messagebox.askquestion("File Tidak Ditemukan", 
                    f"File tidak ditemukan di lokasi: {lokasi_file}\nApakah Anda tetap ingin menyimpan?")
                if response != 'yes':
                    return
        
        # Update database
            conn = sqlite3.connect('../data/ekstraksi.db')
            cursor = conn.cursor()
    
            cursor.execute("""
                UPDATE data_ekstraksi 
                SET nama_file=?, lokasi_file=?, hasil_ekstraksi=?, tanggal_input=?
                WHERE id=?
            """, (
                nama_file,  # Gunakan nilai dari field nama file
                lokasi_file,  # Gunakan nilai dari field lokasi file
                text_content,
                tanggal_input,  # Gunakan nilai dari field tanggal input
                self.current_edit_id
            ))
    
            conn.commit()
            conn.close()
    
            messagebox.showinfo("Sukses", "Data berhasil diperbarui!")
            self.create_main_page()
    
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memperbarui data: {str(e)}")
            print(f"Error update data: {str(e)}")  # Log error untuk debugging

    # Halaman Hapus Data
    def prepare_delete_page(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih data yang akan dihapus")
            return
    
    # Dapatkan nomor urut dari kolom kedua tabel
        selected_item = self.table.item(selected[0])
        self.current_delete_id = selected_item['values'][0]     # ID database
        self.current_delete_nomor = selected_item['values'][1]  # Nomor urut tabel
        self.create_delete_page()

    def create_delete_page(self):
        self.clear_window()
        self.root.title("Hapus Data - Aplikasi Ekstraksi Teks dari Citra")

    # Main container dengan grid configuration
        delete_frame = tk.Frame(self.root, bg="#f5f5f5")
        delete_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    
    # Configure grid weights untuk responsif
        delete_frame.grid_rowconfigure(2, weight=1)  # Row preview container
        delete_frame.grid_columnconfigure(0, weight=1)

    # Judul
        header_frame = tk.Frame(delete_frame, bg="#f5f5f5")
        header_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky='ew')
    
        tk.Label(header_frame, text="Hapus Data", font=('Arial', 14, 'bold'), bg="#f5f5f5", fg="#333333").pack(side=tk.LEFT, padx=10)

    # Ambil data
        conn = sqlite3.connect('../data/ekstraksi.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_ekstraksi WHERE id=?", (self.current_delete_id,))
        data = cursor.fetchone()
        conn.close()

    # Preview Container
        preview_container = tk.Frame(delete_frame, bg="#f5f5f5")
        preview_container.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=10)
    
    # Configure grid untuk responsif - pastikan kedua kolom memiliki bobot yang sama
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        preview_container.grid_columnconfigure(1, weight=1)

    # Frame Gambar dengan scrollbar (50% lebar)
        img_frame = tk.LabelFrame(preview_container, text="Pratinjau Gambar", bg="#ffffff", fg="#333333", font=('Arial', 9, 'bold'),padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
        img_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        img_frame.grid_propagate(False)
    
    # Perbaikan scrollbar gambar
        img_canvas = tk.Canvas(img_frame, bg="#f8f8f8", highlightthickness=0)
        img_scroll_y = ttk.Scrollbar(img_frame, orient="vertical", command=img_canvas.yview)
        img_scroll_x = ttk.Scrollbar(img_frame, orient="horizontal", command=img_canvas.xview)
        img_canvas.configure(yscrollcommand=img_scroll_y.set, xscrollcommand=img_scroll_x.set)
    
    # Ubah urutan packing untuk memastikan scrollbar berfungsi
        img_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        img_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.delete_img_container = tk.Frame(img_canvas, bg="#f8f8f8")
        img_canvas.create_window((0, 0), window=self.delete_img_container, anchor="nw")

        self.delete_img_label = tk.Label(self.delete_img_container, bg="#f8f8f8")
        self.delete_img_label.pack(padx=10, pady=10)

    # Pastikan container mengupdate ukurannya untuk scrollbar
        def on_frame_configure(event):
            img_canvas.configure(scrollregion=img_canvas.bbox("all"))
    
        self.delete_img_container.bind("<Configure>", on_frame_configure)

        def configure_canvas(event):
        # Update ukuran container dan gambar
            img_canvas.configure(scrollregion=img_canvas.bbox("all"))

        img_canvas.bind("<Configure>", configure_canvas)

    # Frame Teks (50% lebar)
        text_frame = tk.LabelFrame(preview_container, text="Hasil Ekstraksi Teks", bg="#f0f7ff", fg="#0066cc", font=('Arial', 9, 'bold'),padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
        text_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        text_frame.grid_propagate(False)
    
        self.delete_text_preview = tk.Text(text_frame, wrap=tk.WORD, bg="white", fg="#333333", state="disabled", font=('Courier New', 10))
        scrollbar = ttk.Scrollbar(text_frame, command=self.delete_text_preview.yview)
        self.delete_text_preview.configure(yscrollcommand=scrollbar.set)
    
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.delete_text_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Isi teks
        self.delete_text_preview.config(state="normal")
        self.delete_text_preview.insert(tk.END, data[3])
        self.delete_text_preview.config(state="disabled")

    # Set ukuran yang sama untuk kedua frame preview
        frame_width = 400
        frame_height = 400
        img_frame.config(width=frame_width, height=frame_height)
        text_frame.config(width=frame_width, height=frame_height)

    # Detail Data Frame
        data_frame = tk.LabelFrame(delete_frame, text="Detail Data", bg="#f5f5f5",padx=10, pady=10)
        data_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
    
    # Grid configuration untuk responsif
        data_frame.grid_columnconfigure(1, weight=1)
        for i in range(4):
            data_frame.grid_rowconfigure(i, weight=1)

    # Informasi Data
        labels = [
            ("Nomor:", str(self.current_delete_nomor)),
            ("Nama File:", data[1]),
            ("Lokasi File:", data[2]),
            ("Tanggal Input:", data[4])
        ]
    
        for idx, (label_text, value) in enumerate(labels):
            tk.Label(data_frame, text=label_text, font=('Arial', 9, 'bold'),bg="#f5f5f5", fg="#333333").grid(row=idx, column=0, sticky='e', padx=5, pady=2)
            tk.Label(data_frame, text=value, bg="#f5f5f5", fg="#333333",wraplength=400, justify=tk.LEFT).grid(row=idx, column=1, sticky='w', padx=5, pady=2)

    # Letakkan tombol di tengah bawah halaman
        button_frame = tk.Frame(delete_frame, bg="#f5f5f5")
        button_frame.grid(row=4, column=0, columnspan=2, pady=15, sticky='ew')
    
    # Frame dalam untuk memusatkan tombol
        center_button_frame = tk.Frame(button_frame, bg="#f5f5f5")
        center_button_frame.pack(side=tk.TOP, anchor=tk.CENTER)

    # Tombol Hapus Data
        delete_button = tk.Button(
            center_button_frame, 
            text="Hapus Data", 
            bg="#ff4d4d", 
            fg="white",
            font=('Arial', 10, 'bold'), 
            padx=15, 
            pady=8,
            command=lambda: self.confirm_delete_data(self.current_delete_id)
            )
        delete_button.pack(side=tk.LEFT, padx=5)

    # Tombol Batal
        cancel_button = tk.Button(
            center_button_frame, 
            text="Batal", 
            bg="#4CAF50", 
            fg="White",
            font=('Arial', 10), 
            padx=15, 
            pady=8,
            command=self.create_main_page
            )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    # Tampilkan gambar awal
        self.show_image_preview_delete(data[2], max_size=(frame_width, frame_height))

    def show_image_preview_delete(self, image_path, max_size=(400,400)):
        try:
            img = Image.open(image_path)
            width, height = img.size
    
            # Hitung rasio untuk resize
            ratio = min(max_size[0]/width, max_size[1]/height)
            new_size = (int(width*ratio), int(height*ratio))
    
            resized_img = img.resize(new_size, Image.LANCZOS)
            self.delete_img_preview = ImageTk.PhotoImage(resized_img)
            self.delete_img_label.config(image=self.delete_img_preview)
            
            # Update scrollregion setelah menampilkan gambar
            if hasattr(self, 'delete_img_container'):
                self.delete_img_container.update_idletasks()
                if hasattr(self.delete_img_container.master, 'configure'):
                    self.delete_img_container.master.configure(scrollregion=self.delete_img_container.master.bbox("all"))
                
        except Exception as e:
            self.delete_img_label.config(text=f"Gagal memuat gambar: {str(e)}", fg="red")

    def confirm_delete_data(self, data_id):
        # Tampilkan dialog konfirmasi
        confirm = messagebox.askyesno("Konfirmasi Hapus", 
                                    "Apakah Anda yakin ingin menghapus data ini?")
        if confirm:
            try:
                # Hapus data dari database
                conn = sqlite3.connect('../data/ekstraksi.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM data_ekstraksi WHERE id=?", (data_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sukses", "Data berhasil dihapus!")
                self.create_main_page()  # Kembali ke halaman utama
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menghapus data: {str(e)}")

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Sesuaikan path Anda
    root = tk.Tk()
    app = ImageTextExtractorApp(root)
    root.mainloop()