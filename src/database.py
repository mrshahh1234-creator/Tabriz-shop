import sqlite3

def init_furniture_db():
    conn = sqlite3.connect('data/shop.db')
    cursor = conn.cursor()

    # 1. Категории (Плитные материалы, Фурнитура, Услуги распила)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL -- 'sheet' (листы), 'edge' (кромка), 'item' (штучный), 'service' (услуга)
        )
    ''')

    # 2. Материалы и Товары цеха
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,          -- Например: ЛДСП Белый Альпийский 16мм
            thickness INTEGER DEFAULT 0,  -- Толщина в мм (для фильтрации плит)
            price_sale REAL NOT NULL,    -- Цена продажи (за лист/метр/штуку)
            stock_qty REAL DEFAULT 0,     -- Свободный остаток на складе
            reserved_qty REAL DEFAULT 0,  -- Забронировано под заказы (занятый товар)
            sales_count REAL DEFAULT 0,   -- Сколько продано/распилено (для Хита продаж)
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')

    # 3. База клиентов (Мастера / Мебельщики)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,          -- ФИО или Название компании
            phone TEXT UNIQUE NOT NULL,
            debt_amount REAL DEFAULT 0.0 -- Текущий долг клиента (если минус - он должен нам)
        )
    ''')

    # 4. Заказы / Продажи (ОБНОВЛЕННАЯ СТРУКТУРА)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,     -- Индивидуальный номер накладной (строка по очереди)
            customer_id INTEGER,
            date_created TEXT DEFAULT CURRENT_TIMESTAMP,
            deadline TEXT NOT NULL,                  -- Обещанный срок (Формат: YYYY-MM-DD HH:MM:SS)
            total_cost REAL NOT NULL,
            order_status TEXT DEFAULT 'pending',     -- 'pending' (в очереди/распиле), 'ready' (готово), 'completed' (выдан)
            payment_status TEXT DEFAULT 'unpaid',    -- 'unpaid', 'paid', 'debt' (в долг)
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    # 5. Детализация заказа (что именно пилим или продаем в этом заказе)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity REAL NOT NULL, -- Количество (листов, метров или штук услуг)
            price REAL NOT NULL,    -- Цена на момент продажи
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных распильного цеха успешно настроена!")

if __name__ == "__main__":
    init_furniture_db()
