from flask import Flask, render_template, request, url_for
from pathlib import Path
import qrcode
from utils.iniparser import IniParser
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
import imgkit
import pathlib
import traceback


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/lmt/', methods = ['GET', 'POST'])
def lmt():
    if request.method == 'POST':
        try:
            fp = pathlib.Path(__file__).parent.resolve()
            # 04050384268646
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
            # sku_url = url_for('static', filename=f'sku/{product_sku}.png')
            sku_url = f'{fp}/static/sku/{product_sku}.png'
            # serialno_url = url_for('static', filename=f'serialno/{serialno}.png')
            serialno_url = f'{fp}/static/serialno/{serialno}.png'

            backend = 'pyusb'
            model = 'QL-800'
            printer = 'usb://0x04f9:0x209b'

            qlr = BrotherQLRaster(model)
            qlr.exception_on_warning = True

            template_string = render_template('lmtresults.html', product_name=product_name, product_sku=product_sku, serialno=serialno, sku_url=sku_url, serialno_url=serialno_url)
            # print(tester)
            label_path = f'./static/label/{barcode}.png'
            imgkit.from_string(template_string, label_path, options={"enable-local-file-access": "", "crop-h": "696", "crop-w":"271"})

            instructions = convert(
                qlr=qlr,
                images = [label_path],
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

            send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)
            return render_template('lmtform.html')
        except Exception:
            ex = traceback.format_exc()
            return render_template('lmterror.html', error_message=ex)
    return render_template('lmtform.html')

@app.route('/lmtclear/', methods = ['POST'])
def lmtclear():
    if request.method == 'POST':
        sku_folder = Path('./static/sku/')
        for file in sku_folder.glob('*'):
            if file.is_file():
                file.unlink()

        serialno_folder = Path('./static/serialno/')
        for file in serialno_folder.glob('*'):
            if file.is_file():
                file.unlink()

    return render_template('lmtform.html')


def process_bar_code_serialno(data, product_type):
    if product_type == 'PRISMA':
        serialno = data[-8:]
    elif product_type == 'NASALMASK':
        serialno = data[-6:]
    return serialno

def process_bar_code_sku(data):
    sku = data[2:16]
    return sku
    # if product_type == 'PRISMA':
    #     sku = data[2:16]
    #     serialno = data[-8:]
    # elif product_type == 'NASALMASK':
    #     sku = data[2:16]
    #     serialno = data[-6:]
    # return [sku, serialno]

def generate_qr_code(data, output_path):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(output_path)
    return img