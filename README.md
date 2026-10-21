# Cekok (Cetak Kode Kirim)

Cekok adalah aplikasi Linux desktop sederhana untuk mencetak resi pengiriman dari marketplace atau toko online, yang berbasis Python dan Tcl/Tk.

Barcode/QR code sengaja dibuat besar supaya bisa dicetak oleh printer thermal murah meriah dan tetap terbaca oleh berbagai scanner/reader.

![Screenshot](screenshot.png)

## Latar Belakang

Aplikasi ini dibuat untuk membuat resi pengiriman dengan printer thermal murah sejuta umat berukuran 58mm. Dilatarbelakangi karena terlanjur salah beli printer 58mm sedangkan untuk mencetak resi dari marketplace dibutuhkan printer ukuran A6 (10cm) atau 80mm. Dari pada tidak terpakai, akhirnya dimanfaatkan saja.

## Fitur

- Mencetak label pengiriman/resi pada kertas thermal printer lebar 58mm.
- Menampilkan kode pengiriman/resi/AWB berupa barcode dan/atau QR code.
- Menampilkan (atau tidak) logo marketplace atau toko sendiri (dengan domain sendiri) dan logo kurir.

## Persyaratan _(Requirement)_

### 1. Printer Thermal

Aplikasi ini membutuhkan komputer/laptop Linux anda sudah berhasil terhubung dengan printer thermal, baik melalui bluetooth atau USB. Silakan mengacu pada dokumentasi printer yang miliki.

Penulis menggunakan printer seharga 200 ribuan yang terdeteksi sebagai `Printer58` (RPP02N) dengan koneksi bluetooth menggunakan driver dari `https://www.rongtatech.com/download/`.

Jika ternyata printer pada komputer anda berbeda sesuaikan dan edit pada baris 41 file `cekok.py` pada bagian:

```python
    self.printer_name = "Printer58"
```

Ganti `Printer58` sesuai dengan nama printer anda.

### 2. Ketergantungan Paket (_Dependencies_)

#### Paket Software:

**Sistem:**

1. python3
2. python3-pip 
3. python3-tk
4. cups
5. bluez-cups

**Modul Python:**

1. pillow
2. python-barcode
3. qrcode

**Font Sistem:**

Skrip ini memindai path font bawaan Linux (`/usr/share/fonts/truetype/...`). Pastikan paket font dasar sudah terpasang di komputer anda. Di distro berbasis Debian/Fedora/Arch, paket font tersebut biasanya bernama `ttf-dejavu` atau `dejavu-fonts-common`.

#### Instalasi:

* Debian / Ubuntu / Devuan / Mint / MX Linux dan distro berbasis DEB lain:

    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-tk cups bluez-cups fonts-dejavu-core -y
    pip install --break-system-packages pillow python-barcode qrcode
    ```

- Red Hat / Fedora / RHEL / AlmaLinux / Rocky Linux dan distro berbasis RPM lain:

    ```bash
    sudo dnf install python3 python3-pip python3-tkinter cups bluez dejavu-sans-fonts -y
    pip install pillow python-barcode qrcode
    ```
- Arch Linux / Manjaro / EndeavourOS dan distro berbasis AUR lain:

    ```bash
    sudo pacman -Sy python python-pip tk cups bluez ttf-dejavu
    pip install pillow python-barcode qrcode
    ```
## Cara Menjalankan

Skrip ini bisa langsung dijalankan lewat python dengan menjalankan perintah pada CLI:

```bash
python3 /lokasi/ke/cekok.py
```

Dan seharusnya sudah muncul jendela seperti pada gambar tangkapan layar di atas.
