import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

# LINEの設定
CHANNEL_ACCESS_TOKEN = 'D5pJAQ9Pl4NdkxDMWqxbwObAUb+5NYWhL5O7Oa55kwhT9T+LbALnsPm/pjOilNfaMKbxUIqFTvUVcOErWP4eW5dfIGJEIy7096RkS7UevyrWMG/elcbx9aExpYRfu9TOHC8lXBNxwl6LjIpaXfDx9AdB04t89/1O/w1cDnyilFU='
GROUP_ID = 'Cea87ddf0ee7f9aef0d1fdfba87b4f2bb'

# LINE Bot APIクライアントの初期化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# テストメッセージの送信
try:
    message = "これはテストメッセージです。送信時刻: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line_bot_api.push_message(
        GROUP_ID,
        messages=[TextSendMessage(text=message)]
    )
    print("メッセージの送信に成功しました")
except LineBotApiError as e:
    print(f"エラーが発生しました: {e}")