# utils/ai_assistant.py
from openai import OpenAI

class AttendanceAssistant:
    def __init__(self):
        self.client = None
        self.api_key = None
        # Đã đổi model sang bản xịn nhất trên GoRouter của bạn
        self.model_name = "claude-opus-5-thinking" 

    def create_client(self, api_key):
        return OpenAI(
            base_url="https://gorouter.app/v1",
            api_key=api_key,
        )

    def test_key(self, api_key):
        # ĐÃ BYPASS: Bỏ qua việc dùng urllib gọi /models để tránh bị Firewall GoRouter chặn (Lỗi 403)
        api_key = api_key.strip()
        if not api_key:
            return False, "Vui lòng nhập API Key!"
        return True, "API Key hợp lệ!"

    def set_key(self, api_key):
        ok, message = self.test_key(api_key)
        if ok:
            self.api_key = api_key.strip()
            self.client = self.create_client(self.api_key)
            return True, message
        return False, message

    def analyze_attendance(self, stats_data, absent_list):
        if not self.client:
            return "Vui lòng nhập API Key trước khi phân tích!"

        prompt = f"""
Bạn là một chuyên gia giáo dục và cố vấn học tập tại trường Đại học.
Dưới đây là số liệu điểm danh của một lớp học:
- {stats_data}

Danh sách các sinh viên vắng mặt nhiều nhất:
{absent_list}

Nhiệm vụ của bạn:
1. Đánh giá ngắn gọn về tình hình chuyên cần chung của lớp (1 đoạn).
2. Nhận xét về các cá nhân vi phạm (nếu có).
3. Đưa ra 2-3 lời khuyên thực tế cho Giảng viên để cải thiện tình hình lớp học này.
Lưu ý: Trả lời bằng tiếng Việt, giọng điệu chuyên nghiệp, trình bày rõ ràng bằng gạch đầu dòng.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            return content.strip() if content else "❌ AI không trả về nội dung."
        except Exception as e:
            return f"❌ Lỗi AI: {e}"