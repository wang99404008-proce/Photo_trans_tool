import ttkbootstrap as tb
from ttkbootstrap.constants import *

from tkinter import filedialog
from tkinter import messagebox
from tkinter import StringVar

from PIL import Image
from PIL import ImageOps

import pillow_heif

import os
import io
import json
import threading
import subprocess

# 啟用 HEIC 支援
pillow_heif.register_heif_opener()


# ==================================
# 全域變數
# ==================================

APP_NAME = "Image Converter Pro V4"

SETTINGS_FILE = "settings.json"

SUPPORTED_INPUTS = (
    ".heic",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".gif"
)

folder_path = ""
output_folder_path = ""

stop_requested = False

# ==================================
# 轉檔統計
# ==================================

total_original_size = 0
total_output_size = 0

# ==================================
# 設定檔
# ==================================

DEFAULT_SETTINGS = {

    "output_format": "JPG",

    "quality": "95",

    "size_limit": "保持原圖大小"

}


# ==================================
# 載入設定
# ==================================

def load_settings():

    if not os.path.exists(
        SETTINGS_FILE
    ):

        return DEFAULT_SETTINGS

    try:

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return DEFAULT_SETTINGS


# ==================================
# 儲存設定
# ==================================

def save_settings():

    settings = {

        "output_format":
            format_var.get(),

        "quality":
            quality_var.get(),

        "size_limit":
            size_var.get()

    }

    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            settings,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==================================
# 選擇來源資料夾
# ==================================

def choose_folder():

    global folder_path

    folder_path = filedialog.askdirectory()

    if not folder_path:
        return

    count = 0

    for file in os.listdir(
        folder_path
    ):

        if file.lower().endswith(
            SUPPORTED_INPUTS
        ):

            count += 1

    source_label.config(

        text=(
            f"來源資料夾：\n"
            f"{folder_path}\n\n"
            f"找到 {count} 張圖片"
        )

    )


# ==================================
# 選擇輸出資料夾
# ==================================

def choose_output_folder():

    global output_folder_path

    output_folder_path = (
        filedialog.askdirectory()
    )

    if not output_folder_path:
        return

    output_label.config(

        text=(
            "輸出資料夾：\n"
            f"{output_folder_path}"
        )

    )


# ==================================
# 開啟輸出資料夾 (已修正為 Windows 專用)
# ==================================

def open_output_folder():

    if not output_folder_path:
        return

    try:
        # Windows 專用指令：使用 explorer 開啟資料夾
        os.startfile(output_folder_path)
    except:
        try:
            subprocess.run(["explorer", output_folder_path])
        except:
            pass


# ==================================
# 指定大小儲存
# ==================================

def save_with_size_limit(
    image,
    output_path,
    target_mb,
    fmt="JPEG"
):

    target_bytes = (
        target_mb
        * 1024
        * 1024
    )

    quality = 95

    while quality >= 20:

        buffer = io.BytesIO()

        if fmt in (
            "JPEG",
            "WEBP"
        ):

            image.save(
                buffer,
                format=fmt,
                quality=quality
            )

        else:

            image.save(
                buffer,
                format=fmt
            )

        current_size = len(
            buffer.getvalue()
        )

        if current_size <= target_bytes:

            with open(
                output_path,
                "wb"
            ) as f:

                f.write(
                    buffer.getvalue()
                )

            return

        quality -= 5

    image.save(
        output_path,
        fmt
    )


# ==================================
# 載入設定
# ==================================

settings = load_settings()


# ==================================
# 主視窗
# ==================================

window = tb.Window(

    title=APP_NAME,

    themename="darkly",

    size=(900, 750)

)

window.resizable(
    True,
    True
)

title_label = tb.Label(

    window,

    text=APP_NAME,

    font=(
        "Arial",
        24,
        "bold"
    )

)

title_label.pack(
    pady=20
)

folder_btn = tb.Button(

    window,

    text="選擇來源資料夾",

    bootstyle="primary",

    command=choose_folder

)

folder_btn.pack(
    pady=10
)

source_label = tb.Label(

    window,

    text="尚未選擇來源資料夾"

)

source_label.pack(
    pady=10
)


output_btn = tb.Button(

    window,

    text="選擇輸出資料夾",

    bootstyle="info",

    command=choose_output_folder

)

output_btn.pack(
    pady=10
)

output_label = tb.Label(

    window,

    text="尚未選擇輸出資料夾"

)

output_label.pack(
    pady=10
)

format_var = StringVar()

format_var.set(
    settings["output_format"]
)

tb.Label(

    window,

    text="輸出格式"

).pack()

format_menu = tb.Combobox(

    window,

    textvariable=format_var,

    values=[
        "JPG",
        "PNG",
        "WEBP",
        "BMP",
        "TIFF"
    ],

    state="readonly",

    width=20

)

format_menu.pack(
    pady=10
)


quality_var = StringVar()

quality_var.set(
    settings["quality"]
)

tb.Label(

    window,

    text="圖片品質"

).pack()

quality_menu = tb.Combobox(

    window,

    textvariable=quality_var,

    values=[
        "100",
        "95",
        "90",
        "80",
        "70"
    ],

    state="readonly",

    width=20

)

quality_menu.pack(
    pady=10
)

size_var = StringVar()

size_var.set(
    settings["size_limit"]
)

tb.Label(

    window,

    text="輸出大小"

).pack()

size_menu = tb.Combobox(

    window,

    textvariable=size_var,

    values=[

        "保持原圖大小",

        "2 MB",

        "3 MB",

        "5 MB",

        "10 MB"

    ],

    state="readonly",

    width=20

)

size_menu.pack(
    pady=10
)

# ==================================
# 停止轉換
# ==================================

def stop_conversion():

    global stop_requested

    stop_requested = True

# ==================================
# 執行轉檔 (已修正縮排)
# ==================================

def convert_images():

    global stop_requested
    global total_original_size
    global total_output_size

    stop_requested = False

    total_original_size = 0
    total_output_size = 0

    if not folder_path:

        messagebox.showwarning(
            "提醒",
            "請選擇來源資料夾"
        )

        return

    if not output_folder_path:

        messagebox.showwarning(
            "提醒",
            "請選擇輸出資料夾"
        )

        return

    save_settings()

    files = [

        f

        for f in os.listdir(
            folder_path
        )

        if f.lower().endswith(
            SUPPORTED_INPUTS
        )

    ]

    total_files = len(
        files
    )

    if total_files == 0:

        messagebox.showwarning(
            "提醒",
            "找不到可轉換圖片"
        )

        return

    success = 0

    failed = []

    output_format = (
        format_var.get()
    )

    for index, file in enumerate(
        files
    ):

        if stop_requested:

            break

        try:

            source_file = os.path.join(
                folder_path,
                file
            )

            output_extension = (
                output_format.lower()
            )

            if output_extension == "jpg":
                output_extension = "jpg"

            output_file = os.path.join(
                output_folder_path,
                os.path.splitext(file)[0]
                + "."
                + output_extension
            )

            status_label.config(
                text=f"正在轉換：{file}"
            )

            window.update_idletasks()

            image = Image.open(
                source_file
            )

            image = ImageOps.exif_transpose(
                image
            )

            if output_format in (
                "JPG",
                "WEBP"
            ):

                image = image.convert(
                    "RGB"
                )

            original_size = os.path.getsize(
                source_file
            )

            selected_size = (
                size_var.get()
            )

            fmt = (
                "JPEG"
                if output_format == "JPG"
                else output_format
            )

            if selected_size == "保持原圖大小":

                if fmt in (
                    "JPEG",
                    "WEBP"
                ):

                    image.save(
                        output_file,
                        fmt,
                        quality=int(
                            quality_var.get()
                        )
                    )

                else:

                    image.save(
                        output_file,
                        fmt
                    )

            else:

                target_mb = int(
                    selected_size.split()[0]
                )

                save_with_size_limit(
                    image,
                    output_file,
                    target_mb,
                    fmt
                )

            output_size = os.path.getsize(
                output_file
            )

            total_original_size += (
                original_size
            )

            total_output_size += (
                output_size
            )

            success += 1

        except Exception as e:

            failed.append(
                file
            )

            print(
                file,
                e
            )

        progress["value"] = (
            (index + 1)
            / total_files
        ) * 100

        window.update_idletasks()

    show_result(
        success,
        failed
    )

# ==================================
# 顯示結果
# ==================================

def show_result(
    success,
    failed
):

    status_label.config(
        text="轉換完成"
    )

    original_mb = (
        total_original_size
        / 1024
        / 1024
    )

    output_mb = (
        total_output_size
        / 1024
        / 1024
    )

    if original_mb > 0:

        saving_rate = (
            (
                original_mb
                - output_mb
            )
            /
            original_mb
        ) * 100

    else:

        saving_rate = 0

    messagebox.showinfo(

        "完成",

        (
            f"成功：{success} 張\n"
            f"失敗：{len(failed)} 張\n\n"
            f"原始大小：{original_mb:.2f} MB\n"
            f"輸出大小：{output_mb:.2f} MB\n"
            f"節省：{saving_rate:.1f}%"
        )

    )

# ==================================
# 背景執行
# ==================================

def start_conversion():

    threading.Thread(

        target=convert_images,

        daemon=True

    ).start()

status_label = tb.Label(

    window,

    text="待命中"

)

status_label.pack(
    pady=10
)

progress = tb.Progressbar(

    window,

    length=700,

    mode="determinate",

    bootstyle="success-striped"

)

progress.pack(
    pady=15
)

start_btn = tb.Button(

    window,

    text="開始轉換",

    bootstyle="success",

    command=start_conversion

)

start_btn.pack(
    pady=10
)

stop_btn = tb.Button(

    window,

    text="停止轉換",

    bootstyle="danger",

    command=stop_conversion

)

stop_btn.pack(
    pady=10
)

# 增加按鈕可以呼叫 open_output_folder (選填，可讓使用者在介面上按)
open_btn = tb.Button(
    window,
    text="開啟輸出資料夾",
    bootstyle="secondary",
    command=open_output_folder
)
open_btn.pack(pady=5)

window.mainloop()
