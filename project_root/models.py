from extensions import db
from datetime import datetime

class TestSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    period = db.Column(db.Integer, nullable=False)
    classroom = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"TestSchedule('{self.subject}', '{self.date}', '{self.period}')"

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Semester('{self.name}', '{self.start_date}')"

# --- ▼▼▼ ここから下が変更箇所 ▼▼▼ ---

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # nullable=True に変更し、名前を任意入力にする
    name = db.Column(db.String(100), nullable=True)
    date = db.Column(db.Date, nullable=False)
    # 連休の終了日を保存するカラムを追加（単日の場合はNULL）
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Holiday('{self.name}', '{self.date}')"