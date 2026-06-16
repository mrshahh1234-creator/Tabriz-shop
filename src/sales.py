import sqlite3
from datetime import datetime

DB_PATH = 'data/shop.db'

def generate_invoice_number():
    """
    Автоматически создает уникальный номер накладной для очереди.
    Формат: R-ДеньМесяц-ЧасМинутаСекунда (например, R-1606-203545)
    """
    now = datetime.now()
    return f"R-{now.strftime('%d%m-%H%M%S')}"


def create_order(customer_id, items, deadline_str):
    """
    Создание заказа, генерация накладной и БРОНИРОВАНИЕ материалов.
    deadline_str должен приходить с телефона в формате: 'YYYY-MM-DD HH:MM:SS'
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Считаем общую стоимость заказа
        total_cost = sum(item['qty'] * item['price'] for item in items)
        
        # 2. Генерируем индивидуальный номер накладной по очереди
        invoice_number = generate_invoice_number()
        
        # 3. Проверяем остатки на складе перед бронированием
        for item in items:
            cursor.execute("SELECT name, stock_qty FROM products WHERE id = ?", (item['product_id'],))
            prod = cursor.fetchone()
            if not prod:
                return f"Товар с ID {item['product_id']} не найден."
            
            name, stock_qty = prod
            if stock_qty < item['qty']:
                return f"Недостаточно материала '{name}'! Доступно: {stock_qty}, нужно: {item['qty']}."

        # 4. Вставляем заказ в таблицу orders с накладной и дедлайном
        cursor.execute('''
            INSERT INTO orders (invoice_number, customer_id, deadline, total_cost, order_status, payment_status)
            VALUES (?, ?, ?, ?, 'pending', 'unpaid')
        ''', (invoice_number, customer_id, deadline_str, total_cost))
        
        order_id = cursor.lastrowid

        # 5. Переносим материалы в reserved_qty (занято под этот заказ)
        for item in items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['qty'], item['price']))
            
            cursor.execute('''
                UPDATE products 
                SET stock_qty = stock_qty - ?, 
                    reserved_qty = reserved_qty + ? 
                WHERE id = ?
            ''', (item['qty'], item['qty'], item['product_id']))

        conn.commit()
        return f"Заказ успешно создан! Накладная: {invoice_number}. Срок: {deadline_str}."
    
    except Exception as e:
        conn.rollback()
        return f"Ошибка при создании заказа: {e}"
    finally:
        conn.close()


def get_overdue_orders():
    """
    Проверка просрочки. Возвращает список всех накладных, 
    которые еще в очереди ('pending'), но их обещанный срок уже прошел.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем текущее время сервера в нужном формате
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        SELECT o.invoice_number, c.name, o.deadline, o.total_cost
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.order_status = 'pending' AND o.deadline < ?
        ORDER BY o.deadline ASC
    ''', (current_time,))
    
    overdue = cursor.fetchall()
    conn.close()
    
    # Возвращаем красивый список словарей для API
    return [
        {
            "invoice": row[0],
            "customer_name": row[1],
            "deadline": row[2],
            "amount": row[3]
        } for row in overdue
    ]
