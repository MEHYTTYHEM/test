from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail
from datetime import datetime, timedelta, date
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
from dotenv import load_dotenv
from config import Config
from extensions import db

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


from models import TestSchedule, Semester, Holiday
from forms import TestScheduleForm, SearchForm, SemesterForm, HolidayForm

genai.configure(api_key=app.config['GEMINI_API_KEY'])
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')

PERIOD_DISPLAY_NAMES = {1: "1限目", 2: "2限目", 3: "3限目", 4: "4限目", 5: "5限目", 6: "6限目"}


# --- ▼▼▼ ここからが追加箇所 ▼▼▼ ---
@app.context_processor
def inject_next_test_countdown():
    """
    すべてのテンプレートに、次のテストまでの日数を渡すための関数
    """
    today = date.today()
    # 今日以降のテストを日付の昇順で取得
    next_test = TestSchedule.query.filter(TestSchedule.date >= today).order_by(TestSchedule.date.asc()).first()

    days_to_next_test = None
    if next_test:
        # 日数差を計算
        delta = next_test.date - today
        days_to_next_test = delta.days

    return dict(days_to_next_test=days_to_next_test)


# --- ▲▲▲ ここまでが追加箇所 ▲▲▲ ---


@app.before_request
def create_tables():
    db.create_all()


# (以降の /calendar や /option などのルートは変更ありません)
def get_holiday_dates_set(holidays):
    holiday_dates = set()
    for holiday in holidays:
        current_date = holiday.date
        end = holiday.end_date or holiday.date
        while current_date <= end:
            holiday_dates.add(current_date)
            current_date += timedelta(days=1)
    return holiday_dates


def calculate_class_schedule(semesters, holiday_dates):
    events = []
    weekday_map = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金"}
    semester_colors = ['#add8e6', '#90ee90', '#f0e68c', '#dda0dd']
    for i, semester in enumerate(semesters):
        weekday_counts = {wd: 0 for wd in range(5)}
        current_date = semester.start_date
        while any(count < 15 for count in weekday_counts.values()):
            weekday = current_date.weekday()
            if weekday < 5 and current_date not in holiday_dates and weekday_counts[weekday] < 15:
                weekday_counts[weekday] += 1
                events.append({
                    'title': f"{semester.name}: {weekday_map[weekday]}曜 {weekday_counts[weekday]}週目",
                    'start': current_date.isoformat(),
                    'allDay': True,
                    'color': semester_colors[i % len(semester_colors)]
                })
            current_date += timedelta(days=1)
            if current_date > semester.start_date + timedelta(days=365 * 10):
                break
    return events


@app.route('/')
@app.route('/calendar')
def calendar():
    test_schedules = TestSchedule.query.all()
    semesters = Semester.query.order_by(Semester.start_date).all()
    holidays = Holiday.query.all()
    events = []
    for test in test_schedules:
        events.append({
            'title': f"テスト: {test.subject} ({PERIOD_DISPLAY_NAMES.get(test.period, '')}, {test.classroom}教室)",
            'start': test.date.isoformat(),
            'color': '#ff6347',
            'allDay': True
        })
    for holiday in holidays:
        end_date = holiday.end_date or holiday.date
        events.append({
            'title': holiday.name or "休日",
            'start': holiday.date.isoformat(),
            'end': (end_date + timedelta(days=1)).isoformat(),
            'color': '#f08080',
            'display': 'background'
        })
    holiday_dates_set = get_holiday_dates_set(holidays)
    class_events = calculate_class_schedule(semesters, holiday_dates_set)
    events.extend(class_events)
    return render_template('calendar.html', events=json.dumps(events))


@app.route('/option', methods=['GET', 'POST'])
def option():
    form = TestScheduleForm()
    if form.validate_on_submit():
        new_test = TestSchedule(subject=form.subject.data, date=form.date.data, period=int(form.period.data),
                                classroom=form.classroom.data)
        db.session.add(new_test)
        db.session.commit()
        flash('テスト予定が登録されました！')
        return redirect(url_for('option'))
    schedules = TestSchedule.query.order_by(TestSchedule.date, TestSchedule.period).all()
    return render_template('option.html', form=form, test_schedules=schedules)


@app.route('/option/edit/<int:test_id>', methods=['GET', 'POST'])
def edit_option(test_id):
    test_to_edit = TestSchedule.query.get_or_404(test_id)
    form = TestScheduleForm(obj=test_to_edit)
    if form.validate_on_submit():
        test_to_edit.subject = form.subject.data
        test_to_edit.date = form.date.data
        test_to_edit.period = int(form.period.data)
        test_to_edit.classroom = form.classroom.data
        db.session.commit()
        flash('テスト予定が更新されました！')
        return redirect(url_for('option'))
    return render_template('option.html', form=form, editing_id=test_id,
                           test_schedules=TestSchedule.query.order_by(TestSchedule.date, TestSchedule.period).all())


@app.route('/option/delete/<int:test_id>', methods=['POST'])
def delete_option(test_id):
    test_to_delete = TestSchedule.query.get_or_404(test_id)
    db.session.delete(test_to_delete)
    db.session.commit()
    flash('テスト予定が削除されました！')
    return redirect(url_for('option'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    result_text = None
    if form.validate_on_submit():
        url = form.url.data
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator='\n', strip=True)
            prompt = f"""
            以下のシラバステキストから、必要な情報を抽出してください。
            ---[シラバステキスト]---
            {page_text[:8000]}
            ---[ここまで]---
            ---[抽出指示]---
            上記のテキストから、以下の項目を抽出してください。
            - 授業名
            - 中間テスト(またはそれに類する理解度確認)が行われる授業週
            - 期末テスト(またはそれに類する理解度確認)が行われる授業週
            - 曜日時限
            情報が見つからなかった項目は「不明」と記載してください。
            """
            gemini_response = GEMINI_MODEL.generate_content(prompt)
            result_text = gemini_response.text
        except requests.exceptions.RequestException as e:
            flash(f"URLの読み込みに失敗しました。URLが正しいか、Webサイトがアクセス可能か確認してください。エラー: {e}")
        except Exception as e:
            flash(f"AIによる抽出中に予期せぬエラーが発生しました: {e}")
    return render_template('search.html', form=form, result=result_text)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    semester_form = SemesterForm(prefix='semester')
    holiday_form = HolidayForm(prefix='holiday')
    if semester_form.validate_on_submit() and semester_form.submit.data:
        new_semester = Semester(name=semester_form.name.data, start_date=semester_form.start_date.data)
        db.session.add(new_semester)
        db.session.commit()
        flash(f'セメスター「{new_semester.name}」が登録されました！')
        return redirect(url_for('settings'))
    if holiday_form.validate_on_submit() and holiday_form.submit.data:
        new_holiday = Holiday(
            name=holiday_form.name.data or None,
            date=holiday_form.date.data,
            end_date=holiday_form.end_date.data
        )
        db.session.add(new_holiday)
        db.session.commit()
        flash(f'休日が登録されました！')
        return redirect(url_for('settings'))
    semesters = Semester.query.order_by(Semester.start_date).all()
    holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template('settings.html', semester_form=semester_form, holiday_form=holiday_form, semesters=semesters,
                           holidays=holidays)


@app.route('/settings/semester/delete/<int:semester_id>', methods=['POST'])
def delete_semester(semester_id):
    semester_to_delete = Semester.query.get_or_404(semester_id)
    db.session.delete(semester_to_delete)
    db.session.commit()
    flash('セメスターが削除されました。')
    return redirect(url_for('settings'))


@app.route('/settings/holiday/delete/<int:holiday_id>', methods=['POST'])
def delete_holiday(holiday_id):
    holiday_to_delete = Holiday.query.get_or_404(holiday_id)
    db.session.delete(holiday_to_delete)
    db.session.commit()
    flash('休日が削除されました。')
    return redirect(url_for('settings'))


if __name__ == '__main__':
    app.run(debug=True)