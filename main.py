# main.py - To'liq eslatma+reja+xarajat ilovasi

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
import sqlite3
from datetime import datetime, timedelta

# Chiroyli ranglar
Window.clearcolor = (0.95, 0.95, 0.97, 1)  # Ochiq kulrang


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('my_life.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Kunlik reja
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                date TEXT NOT NULL,
                completed INTEGER DEFAULT 0
            )
        ''')

        # Xarajatlar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                amount REAL NOT NULL,
                description TEXT,
                category TEXT,
                date TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_task(self, task, date):
        self.cursor.execute('INSERT INTO tasks (task, date) VALUES (?, ?)', (task, date))
        self.conn.commit()

    def get_tasks(self, date):
        self.cursor.execute('SELECT id, task, completed FROM tasks WHERE date = ?', (date,))
        return self.cursor.fetchall()

    def toggle_task(self, task_id, completed):
        self.cursor.execute('UPDATE tasks SET completed = ? WHERE id = ?', (completed, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

    def add_expense(self, amount, description, category, date):
        self.cursor.execute('INSERT INTO expenses (amount, description, category, date) VALUES (?, ?, ?, ?)',
                            (amount, description, category, date))
        self.conn.commit()

    def get_expenses(self, period='all'):
        today = datetime.now().strftime('%Y-%m-%d')
        if period == 'day':
            self.cursor.execute('SELECT amount, description, category FROM expenses WHERE date = ?', (today,))
        elif period == 'week':
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            self.cursor.execute('SELECT amount, description, category FROM expenses WHERE date >= ?', (week_ago,))
        elif period == 'month':
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            self.cursor.execute('SELECT amount, description, category FROM expenses WHERE date >= ?', (month_ago,))
        else:
            self.cursor.execute('SELECT amount, description, category FROM expenses')

        expenses = self.cursor.fetchall()
        total = sum(e[0] for e in expenses)
        return expenses, total


class TaskWidget(BoxLayout):
    def __init__(self, task_id, task_text, completed, callback, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.callback = callback
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.spacing = 10
        self.padding = [10, 5]

        # Chiroyli fon
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Checkbox
        self.check = CheckBox(active=bool(completed), size_hint_x=0.1)
        self.check.bind(active=self.on_check)
        self.add_widget(self.check)

        # Task matni
        self.label = Label(text=task_text, size_hint_x=0.8, halign='left')
        if completed:
            self.label.color = (0.5, 0.5, 0.5, 1)
        self.add_widget(self.label)

        # Delete tugmasi
        del_btn = Button(text='🗑', size_hint_x=0.1, background_color=(0.9, 0.2, 0.2, 1))
        del_btn.bind(on_press=self.delete_task)
        self.add_widget(del_btn)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_check(self, checkbox, value):
        self.callback(self.task_id, 1 if value else 0)
        self.label.color = (0.5, 0.5, 0.5, 1) if value else (0, 0, 0, 1)

    def delete_task(self, instance):
        self.callback(self.task_id, 'delete')


class MyApp(App):
    def build(self):
        self.db = Database()

        # Asosiy panel
        self.tabs = TabbedPanel()
        self.tabs.default_tab_text = '📋 Kunlik Reja'

        # 1-Tab: Kunlik reja
        self.tasks_tab = TabbedPanelItem(text='📋 Reja')
        self.setup_tasks_tab()
        self.tabs.add_widget(self.tasks_tab)

        # 2-Tab: Xarajatlar
        self.expenses_tab = TabbedPanelItem(text='💰 Xarajatlar')
        self.setup_expenses_tab()
        self.tabs.add_widget(self.expenses_tab)

        # 3-Tab: Statistika
        self.stats_tab = TabbedPanelItem(text='📊 Statistika')
        self.setup_stats_tab()
        self.tabs.add_widget(self.stats_tab)

        return self.tabs

    def setup_tasks_tab(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Sana tanlash
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        date_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        prev_btn = Button(text='◀', size_hint_x=0.2)
        prev_btn.bind(on_press=self.prev_day)
        self.date_label = Label(text=self.selected_date, size_hint_x=0.6)
        next_btn = Button(text='▶', size_hint_x=0.2)
        next_btn.bind(on_press=self.next_day)
        date_layout.add_widget(prev_btn)
        date_layout.add_widget(self.date_label)
        date_layout.add_widget(next_btn)
        layout.add_widget(date_layout)

        # Yangi vazifa qo'shish
        add_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        self.new_task_input = TextInput(hint_text='Yangi vazifa...', multiline=False)
        add_btn = Button(text='➕ Qo\'shish', size_hint_x=0.3)
        add_btn.bind(on_press=self.add_task)
        add_layout.add_widget(self.new_task_input)
        add_layout.add_widget(add_btn)
        layout.add_widget(add_layout)

        # Vazifalar ro'yxati
        self.tasks_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.tasks_container)
        layout.add_widget(scroll)

        self.tasks_tab.add_widget(layout)
        self.load_tasks()

    def setup_expenses_tab(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Xarajat qo'shish
        add_expense_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.3)

        self.amount_input = TextInput(hint_text='💰 Summa', multiline=False)
        self.desc_input = TextInput(hint_text='📝 Nima?', multiline=False)
        self.cat_input = TextInput(hint_text='🏷 Kategoriya (ovqat, transport...)', multiline=False)

        add_expense_layout.add_widget(self.amount_input)
        add_expense_layout.add_widget(self.desc_input)
        add_expense_layout.add_widget(self.cat_input)

        add_btn = Button(text='💸 Qo\'shish', size_hint_y=None, height=50)
        add_btn.bind(on_press=self.add_expense)
        add_expense_layout.add_widget(add_btn)

        layout.add_widget(add_expense_layout)

        # Jami ko'rsatkich
        self.total_label = Label(text='Jami: 0 so\'m', size_hint_y=0.1, font_size=20)
        layout.add_widget(self.total_label)

        # Oxirgi xarajatlar
        self.expenses_list = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.expenses_list.bind(minimum_height=self.expenses_list.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.expenses_list)
        layout.add_widget(scroll)

        self.expenses_tab.add_widget(layout)
        self.load_expenses()

    def setup_stats_tab(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Statistika tugmalari
        btn_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        day_btn = Button(text='Bugun')
        week_btn = Button(text='Hafta')
        month_btn = Button(text='Oy')
        all_btn = Button(text='Hammasi')

        day_btn.bind(on_press=lambda x: self.show_stats('day'))
        week_btn.bind(on_press=lambda x: self.show_stats('week'))
        month_btn.bind(on_press=lambda x: self.show_stats('month'))
        all_btn.bind(on_press=lambda x: self.show_stats('all'))

        btn_layout.add_widget(day_btn)
        btn_layout.add_widget(week_btn)
        btn_layout.add_widget(month_btn)
        btn_layout.add_widget(all_btn)
        layout.add_widget(btn_layout)

        # Natijalar
        self.stats_text = Label(text='', size_hint_y=0.85, font_size=16, halign='left', valign='top')
        self.stats_text.bind(size=self.stats_text.setter('text_size'))
        layout.add_widget(self.stats_text)

        self.stats_tab.add_widget(layout)
        self.show_stats('all')

    def load_tasks(self):
        self.tasks_container.clear_widgets()
        tasks = self.db.get_tasks(self.selected_date)
        for task in tasks:
            widget = TaskWidget(task[0], task[1], task[2], self.task_callback)
            self.tasks_container.add_widget(widget)

    def add_task(self, instance):
        task_text = self.new_task_input.text.strip()
        if task_text:
            self.db.add_task(task_text, self.selected_date)
            self.new_task_input.text = ''
            self.load_tasks()

    def task_callback(self, task_id, value):
        if value == 'delete':
            self.db.delete_task(task_id)
        else:
            self.db.toggle_task(task_id, value)
        self.load_tasks()

    def prev_day(self, instance):
        date = datetime.strptime(self.selected_date, '%Y-%m-%d') - timedelta(days=1)
        self.selected_date = date.strftime('%Y-%m-%d')
        self.date_label.text = self.selected_date
        self.load_tasks()

    def next_day(self, instance):
        date = datetime.strptime(self.selected_date, '%Y-%m-%d') + timedelta(days=1)
        self.selected_date = date.strftime('%Y-%m-%d')
        self.date_label.text = self.selected_date
        self.load_tasks()

    def add_expense(self, instance):
        try:
            amount = float(self.amount_input.text)
            desc = self.desc_input.text
            cat = self.cat_input.text if self.cat_input.text else 'boshqa'
            date = datetime.now().strftime('%Y-%m-%d')
            self.db.add_expense(amount, desc, cat, date)
            self.amount_input.text = ''
            self.desc_input.text = ''
            self.cat_input.text = ''
            self.load_expenses()
        except:
            popup = Popup(title='Xato', content=Label(text='Summani to\'g\'ri kiriting!'), size_hint=(0.8, 0.3))
            popup.open()

    def load_expenses(self):
        self.expenses_list.clear_widgets()
        expenses, total = self.db.get_expenses()
        self.total_label.text = f'💰 Jami: {total:,.0f} so\'m'

        for exp in expenses[-10:]:  # Oxirgi 10 tasi
            item = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            with item.canvas.before:
                Color(1, 1, 1, 1)
                rect = RoundedRectangle(pos=item.pos, size=item.size)
            item.bind(pos=lambda i, r=rect: setattr(r, 'pos', i.pos),
                      size=lambda i, r=rect: setattr(r, 'size', i.size))

            item.add_widget(Label(text=f"{exp[2]}: {exp[1]}", size_hint_x=0.6, halign='left'))
            item.add_widget(Label(text=f"{exp[0]:,.0f} so'm", size_hint_x=0.4, color=(0.2, 0.7, 0.2, 1)))
            self.expenses_list.add_widget(item)

    def show_stats(self, period):
        expenses, total = self.db.get_expenses(period)

        # Kategoriya bo'yicha
        categories = {}
        for exp in expenses:
            cat = exp[2]
            categories[cat] = categories.get(cat, 0) + exp[0]

        # Kunlik reja statistikasi
        today = datetime.now().strftime('%Y-%m-%d')
        tasks = self.db.get_tasks(today)
        completed = sum(1 for t in tasks if t[2] == 1)

        stat_text = f"""
[color=FF6B6B]{'=' * 40}[/color]
📊  {period.upper()} STATISTIKA
[color=FF6B6B]{'=' * 40}[/color]

💸  XARAJATLAR:
    Jami: {total:,.0f} so'm
    O'rtacha: {(total / 7 if period == 'week' else total / 30 if period == 'month' else total / 30):,.0f} so'm/kun

📋  VAZIFALAR (Bugun):
    Bajarildi: {completed}/{len(tasks)}
    Foiz: {(completed / len(tasks) * 100 if tasks else 0):.0f}%

🏷  KATEGORIYALAR:
"""
        for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            stat_text += f"\n    • {cat}: {amount:,.0f} so'm"

        if not categories:
            stat_text += "\n    Hozircha ma'lumot yo'q"

        self.stats_text.text = stat_text
        self.stats_text.markup = True


if __name__ == '__main__':
    MyApp().run()