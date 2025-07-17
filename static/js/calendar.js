document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    if (calendarEl) {
        var events = JSON.parse(calendarEl.dataset.events); // Pythonから渡されたイベントデータ

        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'ja', // 日本語化
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: events,
            eventClick: function(info) {
                // イベントクリック時の処理 (例: 詳細表示)
                alert('イベント: ' + info.event.title + '\n日付: ' + info.event.start.toLocaleDateString() + '\n詳細: ' + info.event.extendedProps.description);
            }
        });
        calendar.render();
    }
});