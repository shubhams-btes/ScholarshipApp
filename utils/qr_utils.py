import qrcode

from io import BytesIO

from email.mime.image import MIMEImage

from email.utils import make_msgid


def generate_qr_attachment(
    data,
    filename="qr_code.png",
    domain="182.76.176.205:5142",
    box_size=8,
    border=2,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
):
    """
    Generate a QR code and prepare it as an inline email attachment.

    Returns:
        tuple:
            qr_cid (str)
            qr_attachment (MIMEImage)
    """

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )

    qr.add_data(data)

    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = BytesIO()

    img.save(buffer, format="PNG")

    buffer.seek(0)

    qr_cid = make_msgid(domain=domain)[1:-1]

    qr_attachment = MIMEImage(buffer.read())

    qr_attachment.add_header(
        "Content-ID",
        f"<{qr_cid}>"
    )

    qr_attachment.add_header(
        "Content-Disposition",
        "inline",
        filename=filename
    )

    return qr_cid, qr_attachment