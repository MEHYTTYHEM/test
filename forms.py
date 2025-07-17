from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, URLField, SelectField
# Optionalバリデータをインポート
from wtforms.validators import DataRequired, URL, Optional, ValidationError

class TestScheduleForm(FlaskForm):
    subject = StringField('授業名', validators=[DataRequired()])
    date = DateField('日付', format='%Y-%m-%d', validators=[DataRequired()])
    period = SelectField('時限', choices=[(str(i), f'{i}') for i in range(1, 7)], validators=[DataRequired()])
    classroom = StringField('教室', validators=[DataRequired()])
    submit = SubmitField('テスト予定を登録')

class SearchForm(FlaskForm):
    url = URLField('シラバスのURL', validators=[DataRequired(), URL()])
    submit = SubmitField('AIでテスト日程を抽出')

class SemesterForm(FlaskForm):
    name = StringField('セメスター名 (例: 前期)', validators=[DataRequired()])
    start_date = DateField('開始日', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('セメスターを登録')


# --- ▼▼▼ ここから下が変更箇所 ▼▼▼ ---

class HolidayForm(FlaskForm):
    # DataRequiredを削除し、Optionalに変更
    name = StringField('休日名 (任意)', validators=[Optional()])
    date = DateField('開始日', format='%Y-%m-%d', validators=[DataRequired()])
    # 連休用の終了日フィールドを追加
    end_date = DateField('終了日 (任意)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('休日を登録')

    # 終了日が開始日より後になっているか検証するカスタムバリデータ
    def validate_end_date(self, field):
        if self.date.data and field.data:
            if field.data < self.date.data:
                raise ValidationError('終了日は開始日より後に設定してください。')