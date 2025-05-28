from flask import Flask, render_template, request, url_for, redirect
from pathlib import Path
import qrcode
from utils.iniparser import IniParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
import imgkit
import pathlib
import traceback
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload folder setup
UPLOAD_FOLDER = './uploads'
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
        return render_template('index.html')

@app.route('/lmt/', methods=['GET', 'POST'])
def lmt():
        if request.method == 'POST':
            try:
                fp = pathlib.Path(__file__).parent.resolve()
                barcode = request.form['barcode']
                sku = process_bar_code_sku(barcode)

                mapper = IniParser()
                mapper.read('./lmt.ini')
                mapper_obj = mapper.as_dict()
                product_type = mapper_obj['LMTType'][sku]
                product_sku = mapper_obj['LMTSKU'][sku]
                product_name = mapper_obj['LMTProductName'][sku]

                serialno = process_bar_code_serialno(barcode, product_type)

                generate_qr_code(product_sku, f'./static/sku/{product_sku}.png')
                generate_qr_code(serialno, f'./static/serialno/{serialno}.png')
                sku_url = f'{fp}/static/sku/{product_sku}.png'
                serialno_url = f'{fp}/static/serialno/{serialno}.png'

                backend = 'pyusb'
                model = 'QL-800'
                printer = 'usb://0x04f9:0x209b'

                qlr = BrotherQLRaster(model)
                qlr.exception_on_warning = True

                template_string = render_template(
                    'lmtresults.html',
                    product_name=product_name,
                    product_sku=product_sku,
                    serialno=serialno,
                    sku_url=sku_url,
                    serialno_url=serialno_url
                )

                label_path = f'./static/label/{barcode}.png'
                imgkit.from_string(template_string, label_path, options={
                    "enable-local-file-access": "",
                    "crop-h": "696",
                    "crop-w": "271"
                })

                instructions = convert(
                    qlr=qlr,
                    images=[label_path],
                    label='62x29',
                    rotate='90',
                    threshold=70.0,
                    dither=False,
                    compress=False,
                    red=False,
                    dpi_600=False,
                    hq=True,
                    cut=True
                )

                send(
                    instructions=instructions,
                    printer_identifier=printer,
                    backend_identifier=backend,
                    blocking=True
                )
                return render_template('index.html')

            except Exception:
                ex = traceback.format_exc()
                return render_template('lmterror.html', error_message=ex)

        return render_template('index.html')

@app.route('/lmtpreview/', methods=['POST'])
def lmtpreview():
        if request.method == 'POST':
            try:
                barcode = request.form['barcode']
                sku = process_bar_code_sku(barcode)

                mapper = IniParser()
                mapper.read('./lmt.ini')
                mapper_obj = mapper.as_dict()
                product_type = mapper_obj['LMTType'][sku]
                product_sku = mapper_obj['LMTSKU'][sku]
                product_name = mapper_obj['LMTProductName'][sku]

                serialno = process_bar_code_serialno(barcode, product_type)

                generate_qr_code(product_sku, f'./static/sku/{product_sku}.png')
                generate_qr_code(serialno, f'./static/serialno/{serialno}.png')
                sku_url = url_for('static', filename=f'sku/{product_sku}.png')
                serialno_url = url_for('static', filename=f'serialno/{serialno}.png')

                return render_template(
                    'lmtresults.html',
                    product_name=product_name,
                    product_sku=product_sku,
                    serialno=serialno,
                    sku_url=sku_url,
                    serialno_url=serialno_url
                )

            except Exception:
                ex = traceback.format_exc()
                return render_template('lmterror.html', error_message=ex)

        return render_template('index.html')

@app.route('/lmtclear/', methods=['POST'])
def lmtclear():
        sku_folder = Path('./static/sku/')
        for file in sku_folder.glob('*'):
            if file.is_file() and file.name != '.gitkeep':
                file.unlink()

        serialno_folder = Path('./static/serialno/')
        for file in serialno_folder.glob('*'):
            if file.is_file() and file.name != '.gitkeep':
                file.unlink()

        return redirect('/lmt')

@app.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
        if request.method == 'POST':
            try:
                existing_file = request.files['existing']
                new_file = request.files['new']

                if not existing_file or not new_file:
                    return "Both files are required.", 400

                existing_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(existing_file.filename)
                new_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(new_file.filename)
                existing_file.save(existing_path)
                new_file.save(new_path)

                df_existing = pd.read_excel(existing_path)
                df_new = pd.read_excel(new_path)

                combined_df = pd.concat([df_existing, df_new], ignore_index=True)
                combined_df.drop_duplicates(inplace=True)

                output_path = Path(app.config['UPLOAD_FOLDER']) / 'combined_result.xlsx'
                combined_df.to_excel(output_path, index=False)

                return f'Files merged successfully. Saved as {output_path.name}', 200

            except Exception:
                ex = traceback.format_exc()
                return render_template('lmterror.html', error_message=ex)

        return render_template('index.html')

def process_bar_code_serialno(data, product_type):
        if product_type == 'PRISMA':
            return data[-8:]
        elif product_type == 'NASALMASK':
            return data[-6:]

def process_bar_code_sku(data):
        return data[2:16]

def generate_qr_code(data, output_path):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(output_path)
        return img

if __name__ == '__main__':
        app.run(debug=True)
