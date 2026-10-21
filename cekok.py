import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
import qrcode


class LabelResiApp:

  def __init__(self, root):
    self.root = root
    self.root.title("CEKOK - Cetak Kode Kirim")
    self.root.geometry("1000x700")
    self.root.minsize(890, 580)

    # Inisialisasi path dasar
    self.base_dir = os.path.dirname(os.path.abspath(__file__))

    # Load icon window jika ada file icon.png di dalam folder logo/
    try:
      icon_path = os.path.join(self.base_dir, "logo", "icon.png")
      if os.path.exists(icon_path):
        img_icon = Image.open(icon_path)
        self.app_icon = ImageTk.PhotoImage(img_icon)
        self.root.iconphoto(True, self.app_icon)
    except Exception as e:
      print(f"Gagal memuat ikon jendela: {e}")

    # Folder logo
    self.mp_dir = os.path.join(self.base_dir, "logo", "marketplace")
    self.kurir_dir = os.path.join(self.base_dir, "logo", "kurir")
    os.makedirs(self.mp_dir, exist_ok=True)
    os.makedirs(self.kurir_dir, exist_ok=True)

    self.mp_map = {}
    self.kurir_map = {}

    self.printer_name = "Printer58"
    self.preview_photo = None

    # Frame Utama
    main_frame = tk.Frame(root, padx=14, pady=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    main_frame.columnconfigure(0, weight=0, minsize=460)
    main_frame.columnconfigure(1, weight=1, minsize=380)
    main_frame.rowconfigure(0, weight=1)

    # =========================================================================
    # KOLOM KIRI: KONTROL INPUT
    # =========================================================================
    left_panel = tk.Frame(main_frame)
    left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

    # 1. Input Kode / Nomor Resi
    tk.Label(
        left_panel,
        text="Nomor Kode / Resi Pengiriman :",
        font=("Sans", 11, "bold"),
    ).pack(anchor="w")

    frame_input = tk.Frame(left_panel)
    frame_input.pack(fill=tk.X, pady=(2, 6))

    self.entry_resi = tk.Entry(frame_input, font=("Monospace", 13, "bold"))
    self.entry_resi.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
    self.entry_resi.insert(0, "TJX-88291039482")

    btn_paste = tk.Button(
        frame_input,
        text="📋 Paste",
        bg="#e0e8f0",
        font=("Sans", 11, "bold"),
        padx=8,
        command=self.paste_replace_clipboard,
    )
    btn_paste.pack(side=tk.LEFT, padx=(8, 0), ipady=2)

    self.entry_resi.bind("<Control-v>", self.on_ctrl_v_replace)
    self.entry_resi.bind("<Control-V>", self.on_ctrl_v_replace)
    self.entry_resi.bind("<<Paste>>", self.on_ctrl_v_replace)
    self.entry_resi.bind(
        "<FocusIn>", lambda e: self.entry_resi.select_range(0, tk.END)
    )
    self.entry_resi.bind("<KeyRelease>", lambda e: self.update_preview())

    # 1B. Input Kode Pickup (Opsional, Maks 15 Karakter)
    tk.Label(
        left_panel,
        text="Kode Pickup (Opsional, maks 15 karakter):",
        font=("Sans", 11, "bold"),
    ).pack(anchor="w", pady=(4, 0))

    frame_pickup = tk.Frame(left_panel)
    frame_pickup.pack(fill=tk.X, pady=(2, 10))

    # Validasi pembatasan maks 15 karakter
    vcmd_pickup = (self.root.register(lambda P: len(P) <= 15), "%P")

    self.entry_pickup = tk.Entry(
        frame_pickup,
        font=("Monospace", 11, "bold"),
        width=16,
        validate="key",
        validatecommand=vcmd_pickup,
    )
    self.entry_pickup.pack(side=tk.LEFT, ipady=3)
    self.entry_pickup.bind("<KeyRelease>", lambda e: self.update_preview())

    btn_paste_pickup = tk.Button(
        frame_pickup,
        text="📋 Paste",
        bg="#e0e8f0",
        font=("Sans", 11, "bold"),
        padx=8,
        command=self.paste_pickup,
    )
    btn_paste_pickup.pack(side=tk.LEFT, padx=(6, 4), ipady=1)

    btn_clear_pickup = tk.Button(
        frame_pickup,
        text="✖ Kosongkan",
        bg="#f5e0e0",
        font=("Sans", 11, "bold"),
        padx=8,
        command=self.clear_pickup,
    )
    btn_clear_pickup.pack(side=tk.LEFT, padx=(2, 0), ipady=1)

    # 2. Pengaturan Tipe & Ukuran
    frame_cfg = tk.LabelFrame(
        left_panel,
        text=" Pengaturan Dimensi & Teks (Area Cetak Maks 48mm) ",
        font=("Sans", 11),
        padx=10,
        pady=6,
    )
    frame_cfg.pack(fill=tk.X, pady=(0, 10))
    frame_cfg.columnconfigure(1, weight=1)

    tk.Label(frame_cfg, text="Tipe Kode:", font=("Sans", 11)).grid(
        row=0, column=0, sticky="w", pady=4
    )
    self.code_type_var = tk.StringVar(value="Barcode (Code128)")
    cb_type = tk.OptionMenu(
        frame_cfg,
        self.code_type_var,
        "Barcode (Code128)",
        "QR Code",
        "QR Code & Barcode (Keduanya)",
        command=lambda _: self.update_preview(),
    )
    cb_type.grid(row=0, column=1, sticky="w", padx=8, pady=4)

    tk.Label(frame_cfg, text="Lebar Cetak di Kertas:", font=("Sans", 11)).grid(
        row=1, column=0, sticky="w", pady=4
    )
    self.cross_width_mm = tk.IntVar(value=45)
    scale_w = tk.Scale(
        frame_cfg,
        from_=30,
        to=47,
        orient=tk.HORIZONTAL,
        variable=self.cross_width_mm,
        label="mm (Min 30mm - Maks 47mm)",
        length=250,
        command=lambda _: self.update_preview(),
    )
    scale_w.grid(row=1, column=1, sticky="ew", padx=8, pady=2)

    tk.Label(frame_cfg, text="Panjang Barcode (Vertikal):", font=("Sans", 11)).grid(
        row=2, column=0, sticky="w", pady=4
    )
    self.scroll_length_mm = tk.IntVar(value=60)
    scale_l = tk.Scale(
        frame_cfg,
        from_=45,
        to=115,
        orient=tk.HORIZONTAL,
        variable=self.scroll_length_mm,
        label="mm (Rentang Garis Barcode)",
        length=250,
        command=lambda _: self.update_preview(),
    )
    scale_l.grid(row=2, column=1, sticky="ew", padx=8, pady=2)

    tk.Label(frame_cfg, text="Ukuran Teks Kode Resi:", font=("Sans", 11)).grid(
        row=3, column=0, sticky="w", pady=4
    )
    self.font_size_var = tk.IntVar(value=40)
    scale_f = tk.Scale(
        frame_cfg,
        from_=20,
        to=72,
        orient=tk.HORIZONTAL,
        variable=self.font_size_var,
        label="pt (Otomatis menyesuaikan jika kepanjangan)",
        length=250,
        command=lambda _: self.update_preview(),
    )
    scale_f.grid(row=3, column=1, sticky="ew", padx=8, pady=2)

    # 3. Dropdown Logo Marketplace & Kurir
    frame_logos = tk.LabelFrame(
        left_panel,
        text=" Pilih Logo (Dari Folder logo/marketplace & logo/kurir) ",
        font=("Sans", 11),
        padx=10,
        pady=6,
    )
    frame_logos.pack(fill=tk.X, pady=(0, 4))
    frame_logos.columnconfigure(1, weight=1)

    tk.Label(
        frame_logos, text="Marketplace:", font=("Sans", 11, "bold")
    ).grid(row=0, column=0, sticky="w", padx=4, pady=5)
    self.mp_var = tk.StringVar()
    self.cb_mp = ttk.Combobox(
        frame_logos, textvariable=self.mp_var, state="readonly", width=24
    )
    self.cb_mp.grid(row=0, column=1, sticky="ew", padx=6, pady=5)
    self.cb_mp.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

    tk.Label(
        frame_logos, text="Kurir & Layanan:", font=("Sans", 11, "bold")
    ).grid(row=1, column=0, sticky="w", padx=4, pady=5)
    self.kurir_var = tk.StringVar()
    self.cb_kurir = ttk.Combobox(
        frame_logos, textvariable=self.kurir_var, state="readonly", width=24
    )
    self.cb_kurir.grid(row=1, column=1, sticky="ew", padx=6, pady=5)
    self.cb_kurir.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

    btn_refresh = tk.Button(
        frame_logos,
        text="🔄 Muat Ulang\nFolder Logo",
        font=("Sans", 11),
        padx=6,
        command=self.scan_logo_folders,
    )
    btn_refresh.grid(row=0, column=2, rowspan=2, padx=(6, 2), pady=4, sticky="ns")

    self.print_kurir_text_var = tk.BooleanVar(value=False)
    chk_kurir_txt = tk.Checkbutton(
        frame_logos,
        text="Cetak teks nama/jenis layanan kurir (misal: JNE Reguler) di bawah logo",
        font=("Sans", 11),
        variable=self.print_kurir_text_var,
        command=self.update_preview,
    )
    chk_kurir_txt.grid(
        row=2, column=0, columnspan=3, sticky="w", padx=2, pady=(4, 2)
    )

    # =========================================================================
    # KOLOM KANAN: LIVE PREVIEW KERTAS 58MM
    # =========================================================================
    frame_prev = tk.LabelFrame(
        main_frame,
        text=" Live Preview Kertas 58mm (Arah Gulungan Atas-Bawah) ",
        font=("Sans", 11),
        padx=8,
        pady=8,
    )
    frame_prev.grid(row=0, column=1, sticky="nsew")

    self.canvas_preview = tk.Canvas(
        frame_prev, bg="#d9d9d9", highlightthickness=0
    )
    self.canvas_preview.pack(fill=tk.BOTH, expand=True)
    self.canvas_preview.bind("<Configure>", lambda e: self.update_preview())

    # =========================================================================
    # BAGIAN BAWAH: TOMBOL CETAK & FOOTER
    # =========================================================================
    self.btn_print = tk.Button(
        main_frame,
        text="CETAK LABEL PENGIRIMAN",
        bg="#b1c900",
        fg="black",
        font=("Sans", 12, "bold"),
        height=2,
        command=self.print_label,
    )
    self.btn_print.grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(10, 4)
    )

    lbl_footer = tk.Label(
        main_frame,
        text="© 2026 CEKOK v1.2",
        font=("Sans", 11),
        fg="#333333",
    )
    lbl_footer.grid(row=2, column=0, columnspan=2, pady=(2, 0))

    self.scan_logo_folders()

  @staticmethod
  def format_kurir_name(filename):
    stem = os.path.splitext(filename)[0].strip()
    if "-" in stem:
      parts = stem.split("-", 1)
      kurir = parts[0].strip().upper()
      layanan = parts[1].replace("-", " ").replace("_", " ").strip().title()
      return f"{kurir} {layanan}"
    return stem.replace("_", " ").upper()

  @staticmethod
  def format_mp_name(filename):
    stem = os.path.splitext(filename)[0].strip()
    return stem.replace("-", " ").replace("_", " ").title()

  def scan_logo_folders(self):
    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")

    self.mp_map = {"-- Tanpa Logo --": None}
    if os.path.exists(self.mp_dir):
      for fname in sorted(os.listdir(self.mp_dir)):
        if fname.lower().endswith(valid_exts):
          label = self.format_mp_name(fname)
          self.mp_map[label] = os.path.join(self.mp_dir, fname)

    mp_keys = list(self.mp_map.keys())
    self.cb_mp["values"] = mp_keys
    if self.mp_var.get() not in self.mp_map:
      self.mp_var.set(mp_keys[1] if len(mp_keys) > 1 else mp_keys[0])

    self.kurir_map = {"-- Tanpa Logo --": None}
    if os.path.exists(self.kurir_dir):
      for fname in sorted(os.listdir(self.kurir_dir)):
        if fname.lower().endswith(valid_exts):
          label = self.format_kurir_name(fname)
          self.kurir_map[label] = os.path.join(self.kurir_dir, fname)

    kurir_keys = list(self.kurir_map.keys())
    self.cb_kurir["values"] = kurir_keys
    if self.kurir_var.get() not in self.kurir_map:
      self.kurir_var.set(
          kurir_keys[1] if len(kurir_keys) > 1 else kurir_keys[0]
      )

    self.update_preview()

  def paste_replace_clipboard(self):
    try:
      clip_text = self.root.clipboard_get().strip()
      clip_text = " ".join(clip_text.splitlines()).strip()
      if clip_text:
        self.entry_resi.delete(0, tk.END)
        self.entry_resi.insert(0, clip_text)
        self.entry_resi.select_range(0, tk.END)
        self.update_preview()
    except tk.TclError:
      messagebox.showwarning(
          "Clipboard Kosong", "Tidak ada teks di dalam clipboard untuk ditempel."
      )

  def on_ctrl_v_replace(self, event=None):
    self.paste_replace_clipboard()
    return "break"

  def paste_pickup(self):
    """Menempel isi clipboard ke field kode pickup dengan batas maksimal 15 karakter."""
    try:
      clip_text = self.root.clipboard_get().strip()
      clip_text = " ".join(clip_text.splitlines()).strip()[:15]
      if clip_text:
        self.entry_pickup.delete(0, tk.END)
        self.entry_pickup.insert(0, clip_text)
        self.update_preview()
    except tk.TclError:
      pass

  def clear_pickup(self):
    """Mengosongkan field kode pickup."""
    self.entry_pickup.delete(0, tk.END)
    self.update_preview()

  def _load_clean_image(self, path):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, im).convert("L")
    inv = ImageOps.invert(comp)
    inv = inv.point(lambda x: 0 if x < 20 else 255)
    bbox = inv.getbbox()
    if bbox:
      comp = comp.crop(bbox)
    return comp

  def _get_fitted_font(self, text, max_width_px, preferred_size, min_size=12):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    valid_path = next((p for p in font_paths if os.path.exists(p)), None)
    if not valid_path:
      return ImageFont.load_default()

    dummy_draw = ImageDraw.Draw(Image.new("L", (10, 10)))
    sz = preferred_size
    while sz >= min_size:
      f = ImageFont.truetype(valid_path, sz)
      bbox = dummy_draw.textbbox((0, 0), text, font=f)
      tw = bbox[2] - bbox[0]
      if tw <= max_width_px - 8:
        return f
      sz -= 2
    return ImageFont.truetype(valid_path, min_size)

  def _make_barcode_block(
      self,
      resi_text,
      target_cross_dots,
      target_scroll_dots,
      pref_font_size,
      dummy_draw,
  ):
    CODE128 = barcode.get_barcode_class("code128")
    bc_obj = CODE128(resi_text, writer=ImageWriter())
    raw_bc = bc_obj.render(
        writer_options={
            "write_text": False,
            "module_width": 0.4,
            "module_height": 20.0,
            "quiet_zone": 0.0,
        }
    ).convert("L")

    inv_bc = ImageOps.invert(raw_bc)
    bbox_bc = inv_bc.getbbox()
    if bbox_bc:
      raw_bc = raw_bc.crop(bbox_bc)

    font_bold = self._get_fitted_font(
        resi_text, target_scroll_dots, pref_font_size
    )
    tb = dummy_draw.textbbox((0, 0), resi_text, font=font_bold)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    text_area_h = th + 18
    bc_bar_h = max(120, target_cross_dots - text_area_h)

    quiet_zone_px = 26
    bc_bar_w = max(200, target_scroll_dots - (quiet_zone_px * 2))
    bc_resized = raw_bc.resize(
        (bc_bar_w, bc_bar_h), Image.Resampling.NEAREST
    )

    horiz_block = Image.new(
        "L", (target_scroll_dots, bc_bar_h + text_area_h), 255
    )
    horiz_block.paste(bc_resized, (quiet_zone_px, 0))

    draw_h = ImageDraw.Draw(horiz_block)
    tx = (target_scroll_dots - tw) // 2
    ty = bc_bar_h + 8 - tb[1]
    draw_h.text((tx, ty), resi_text, fill=0, font=font_bold)

    return horiz_block.rotate(90, expand=True)

  def _make_qrcode_block(
      self,
      resi_text,
      target_cross_dots,
      pref_font_size,
      paper_width,
      dummy_draw,
  ):
    qr = qrcode.QRCode(version=None, box_size=10, border=1)
    qr.add_data(resi_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert(
        "L"
    )

    qr_size = min(paper_width, target_cross_dots)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    font_bold = self._get_fitted_font(resi_text, paper_width, pref_font_size)
    tb = dummy_draw.textbbox((0, 0), resi_text, font=font_bold)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    text_area_h = th + 16
    block_w = max(qr_size, tw + 12)
    code_block = Image.new("L", (block_w, qr_size + text_area_h), 255)

    code_block.paste(qr_img, ((block_w - qr_size) // 2, 0))
    draw_q = ImageDraw.Draw(code_block)
    tx = (block_w - tw) // 2
    ty = qr_size + 6 - tb[1]
    draw_q.text((tx, ty), resi_text, fill=0, font=font_bold)
    return code_block

  def build_label_image(self):
    resi_text = self.entry_resi.get().strip() or "SAMPLE-123456"
    pickup_code = self.entry_pickup.get().strip()
    code_type = self.code_type_var.get()

    PAPER_WIDTH = 384
    target_cross_dots = int(self.cross_width_mm.get() * 8)
    target_scroll_dots = int(self.scroll_length_mm.get() * 8)
    pref_font_size = int(self.font_size_var.get())

    dummy_draw = ImageDraw.Draw(Image.new("L", (10, 10)))

    # --- 1. BLOK KODE PENGIRIMAN ---
    if code_type == "Barcode (Code128)":
      code_block_final = self._make_barcode_block(
          resi_text,
          target_cross_dots,
          target_scroll_dots,
          pref_font_size,
          dummy_draw,
      )
    elif code_type == "QR Code":
      code_block_final = self._make_qrcode_block(
          resi_text, target_cross_dots, pref_font_size, PAPER_WIDTH, dummy_draw
      )
    else:
      qr_block = self._make_qrcode_block(
          resi_text, target_cross_dots, pref_font_size, PAPER_WIDTH, dummy_draw
      )
      bc_block = self._make_barcode_block(
          resi_text,
          target_cross_dots,
          target_scroll_dots,
          pref_font_size,
          dummy_draw,
      )

      sep_h = 10
      comb_w = max(qr_block.width, bc_block.width)
      comb_h = qr_block.height + sep_h + bc_block.height

      combined_code = Image.new("L", (comb_w, comb_h), 255)
      combined_code.paste(qr_block, ((comb_w - qr_block.width) // 2, 0))

      d_comb = ImageDraw.Draw(combined_code)
      d_comb.line(
          [
              (10, qr_block.height + (sep_h // 2)),
              (comb_w - 10, qr_block.height + (sep_h // 2)),
          ],
          fill=0,
          width=1,
      )

      combined_code.paste(
          bc_block, ((comb_w - bc_block.width) // 2, qr_block.height + sep_h)
      )
      code_block_final = combined_code

    # --- 1B. BLOK KODE PICKUP (JIKA DIISI) ---
    pickup_img = None
    if pickup_code:
      pickup_str = f"PICKUP: {pickup_code}"
      f_pickup = self._get_fitted_font(
          pickup_str, PAPER_WIDTH - 36, preferred_size=26, min_size=14
      )
      ptb = dummy_draw.textbbox((0, 0), pickup_str, font=f_pickup)
      ptw, pth = ptb[2] - ptb[0], ptb[3] - ptb[1]

      pad_x = 12
      pad_y = 6
      box_w = ptw + (pad_x * 2)
      box_h = pth + (pad_y * 2)

      pickup_img = Image.new("L", (box_w, box_h), 255)
      d_p = ImageDraw.Draw(pickup_img)
      # Kotak bingkai rapi dengan ketebalan 2px
      d_p.rectangle([(0, 0), (box_w - 1, box_h - 1)], outline=0, width=2)
      d_p.text((pad_x, pad_y - ptb[1]), pickup_str, fill=0, font=f_pickup)

    # --- 2. LOGO SEBARIS ---
    mp_label = self.mp_var.get()
    kurir_label = self.kurir_var.get()
    mp_path = self.mp_map.get(mp_label)
    kurir_path = self.kurir_map.get(kurir_label)

    selected_items = []
    if mp_path and os.path.exists(mp_path):
      selected_items.append(("mp", mp_label, mp_path))
    if kurir_path and os.path.exists(kurir_path):
      selected_items.append(("kurir", kurir_label, kurir_path))

    logo_row_img = None
    if selected_items:
      max_logo_h = 80
      gap = 20
      max_col_w = (
          (PAPER_WIDTH - gap - 12) // 2
          if len(selected_items) == 2
          else (PAPER_WIDTH - 16)
      )

      rendered_cols = []
      for item_type, label_text, path in selected_items:
        try:
          lg = self._load_clean_image(path)
        except Exception:
          continue

        ratio = min(max_col_w / lg.width, max_logo_h / lg.height)
        nw = max(1, int(lg.width * ratio))
        nh = max(1, int(lg.height * ratio))
        lg_resized = lg.resize((nw, nh), Image.Resampling.LANCZOS)

        if item_type == "kurir" and self.print_kurir_text_var.get():
          f_kurir = self._get_fitted_font(
              label_text, max_col_w, preferred_size=20, min_size=12
          )
          ktb = dummy_draw.textbbox((0, 0), label_text, font=f_kurir)
          ktw, kth = ktb[2] - ktb[0], ktb[3] - ktb[1]

          col_w = max(nw, ktw + 6)
          col_h = nh + 6 + kth + 4
          col_img = Image.new("L", (col_w, col_h), 255)
          col_img.paste(lg_resized, ((col_w - nw) // 2, 0))

          d_col = ImageDraw.Draw(col_img)
          d_col.text(
              ((col_w - ktw) // 2, nh + 4 - ktb[1]),
              label_text,
              fill=0,
              font=f_kurir,
          )
          rendered_cols.append(col_img)
        else:
          rendered_cols.append(lg_resized)

      if rendered_cols:
        total_lw = sum(c.width for c in rendered_cols) + gap * (
            len(rendered_cols) - 1
        )
        max_lh = max(c.height for c in rendered_cols)
        logo_row_img = Image.new("L", (total_lw, max_lh), 255)

        cur_x = 0
        for c in rendered_cols:
          y_off = (max_lh - c.height) // 2
          logo_row_img.paste(c, (cur_x, y_off))
          cur_x += c.width + gap

    # --- 3. GABUNGKAN KE KANVAS UTAMA 58MM (384 DOTS) ---
    top_pad = 10
    mid_pad = 22 if logo_row_img else 8
    bot_pad = 12

    cb_w, cb_h = code_block_final.size
    pickup_h = pickup_img.height if pickup_img else 0
    pickup_pad = 12 if pickup_img else 0
    logo_h = logo_row_img.height if logo_row_img else 0

    total_height = (
        top_pad + cb_h + pickup_pad + pickup_h + mid_pad + logo_h + bot_pad
    )
    canvas = Image.new("L", (PAPER_WIDTH, total_height), 255)

    pos_x_code = (PAPER_WIDTH - cb_w) // 2
    canvas.paste(code_block_final, (pos_x_code, top_pad))

    cur_y = top_pad + cb_h

    # Tempel Kode Pickup jika ada
    if pickup_img:
      cur_y += pickup_pad
      pos_x_pickup = (PAPER_WIDTH - pickup_img.width) // 2
      canvas.paste(pickup_img, (pos_x_pickup, cur_y))
      cur_y += pickup_h

    # Tempel Garis dan Logo
    if logo_row_img:
      sep_y = cur_y + (mid_pad // 2)
      draw_c = ImageDraw.Draw(canvas)
      draw_c.line([(16, sep_y), (PAPER_WIDTH - 16, sep_y)], fill=0, width=2)

      pos_x_logo = (PAPER_WIDTH - logo_row_img.width) // 2
      pos_y_logo = cur_y + mid_pad
      canvas.paste(logo_row_img, (pos_x_logo, pos_y_logo))

    return canvas.point(lambda x: 0 if x < 150 else 255, "1")

  def update_preview(self):
    try:
      img = self.build_label_image().convert("RGB")
      cw = self.canvas_preview.winfo_width()
      ch = self.canvas_preview.winfo_height()
      if cw < 50:
        cw = 400
      if ch < 50:
        ch = 440

      max_w = cw - 24
      max_h = ch - 16
      ratio = min(max_w / img.width, max_h / img.height, 0.85)
      disp_w = max(1, int(img.width * ratio))
      disp_h = max(1, int(img.height * ratio))

      img_disp = img.resize((disp_w, disp_h), Image.Resampling.NEAREST)

      self.preview_photo = ImageTk.PhotoImage(img_disp)
      self.canvas_preview.delete("all")
      self.canvas_preview.create_image(
          14, (ch - disp_h) // 2, anchor="nw", image=self.preview_photo
      )
    except Exception:
      pass

  def print_label(self):
    if not self.entry_resi.get().strip():
      messagebox.showwarning(
          "Peringatan", "Nomor kode pengiriman tidak boleh kosong!"
      )
      return

    try:
      final_img = self.build_label_image()
      raw_file = "/tmp/print_label_58mm.bin"

      with open(raw_file, "wb") as f:
        f.write(b"\x1b\x40")  # ESC @
        f.write(b"\x1b\x61\x01")  # ESC a 1

        width_bytes = (final_img.width + 7) // 8
        height_dots = final_img.height

        f.write(b"\x1d\x76\x30\x00")
        f.write(width_bytes.to_bytes(2, byteorder="little"))
        f.write(height_dots.to_bytes(2, byteorder="little"))

        for y in range(height_dots):
          row_bytes = bytearray()
          for x_byte in range(width_bytes):
            byte_val = 0
            for bit in range(8):
              x = x_byte * 8 + bit
              if x < final_img.width:
                if final_img.getpixel((x, y)) == 0:
                  byte_val |= 1 << (7 - bit)
            row_bytes.append(byte_val)
          f.write(row_bytes)

        f.write(b"\n\n\n")

      subprocess.run(
          ["lp", "-d", self.printer_name, "-o", "raw", raw_file], check=True
      )
    except Exception as e:
      messagebox.showerror("Error", f"Gagal mencetak label:\n{str(e)}")


if __name__ == "__main__":
  root = tk.Tk()
  app = LabelResiApp(root)
  root.mainloop()
