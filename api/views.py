from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import json
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError
import fitz  # PyMuPDF
from PIL import Image
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage
import traceback
import io

# LINE API設定
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
GROUP_ID = os.getenv('LINE_GROUP_ID')
BASE_URL = os.getenv('BASE_URL')

# LINE Bot API クライアントの初期化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_line_message(request):
    try:
        print("Request received")
        print(f"Files: {request.FILES}")
        print(f"POST data: {request.POST}")

        # pdf_imagesディレクトリのパスを作成
        pdf_images_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_images')
        print(f"PDF images directory: {pdf_images_dir}")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(pdf_images_dir, exist_ok=True)

        message = request.POST.get('message', '')

        # メッセージがある場合は送信
        if message:
            try:
                print(f"Sending message: {message}")
                line_bot_api.push_message(
                    GROUP_ID,
                    messages=[TextSendMessage(text=message)]
                )
                print("Message sent successfully")
            except LineBotApiError as e:
                print(f"Error sending message: {e}")
                raise

        file = request.FILES.get('file')
        if file:
            try:
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                    for chunk in file.chunks():
                        temp_pdf.write(chunk)
                    temp_pdf_path = temp_pdf.name

                print(f"PDF saved to: {temp_pdf_path}")

                # PDFを開く
                pdf_document = fitz.open(temp_pdf_path)
                
                # 各ページを処理
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    
                    # 高品質な画像として取得
                    zoom = 2  # 画質を上げるために2倍に
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False) # type: ignore
                    
                    # PILイメージに変換
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) # type: ignore
                    
                    # 画像ファイル名を設定
                    image_filename = f'pdf_image_{page_num}.jpg'
                    preview_filename = f'pdf_image_{page_num}_preview.jpg'
                    
                    # 画像パスを設定
                    image_path = os.path.join('pdf_images', image_filename)
                    preview_path = os.path.join('pdf_images', preview_filename)

                    # オリジナル画像を保存
                    with default_storage.open(image_path, 'wb') as f:
                        img.save(f, 'JPEG', quality=85, optimize=True)
                    print(f"Saved original image: {image_path}")

                    # プレビュー画像を作成して保存
                    preview = img.copy()
                    preview.thumbnail((240, 240), Image.Resampling.LANCZOS)
                    with default_storage.open(preview_path, 'wb') as f:
                        preview.save(f, 'JPEG', quality=70, optimize=True)
                    print(f"Saved preview image: {preview_path}")

                    # URLを生成
                    base_url = BASE_URL or "https://example.com"
                    original_url = f"{base_url}/media/{image_path}"
                    preview_url = f"{base_url}/media/{preview_path}"

                    print(f"Original URL: {original_url}")
                    print(f"Preview URL: {preview_url}")

                    # LINEに画像を送信
                    try:
                        line_bot_api.push_message(
                            GROUP_ID,
                            messages=[ImageSendMessage(
                                original_content_url=original_url,
                                preview_image_url=preview_url
                            )]
                        )
                        print("Image sent successfully")
                    except LineBotApiError as e:
                        print(f"Error sending image: {e}")
                        raise

                # PDFドキュメントを閉じる
                pdf_document.close()

            finally:
                # 一時ファイルの削除
                if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
                    print("Temporary PDF file deleted")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        print(f"Error in send_line_message: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)