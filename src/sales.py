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
# Добавить в конец файла src/sales.py

def mark_order_as_ready(invoice_number):
    """
    Переводит заказ в статус 'ready'. 
    Это останавливает счетчик дедлайна, и пуш-уведомления перестают приходить.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'ready' 
            WHERE invoice_number = ? AND order_status = 'pending'
        ''', (invoice_number,))
        
        if cursor.rowcount == 0:
            return "Заказ не найден или уже готов/выдан."
            
        conn.commit()
        return f"Накладная {invoice_number} успешно переведена в статус ГОТОВО."
    except Exception as e:
        return f"Ошибка базы данных: {e}"
    finally:
        conn.close()
# Добавить в самый конец файла src/sales.py

def get_invoice_print_text(invoice_number):
    """
    Формирует красивый текстовый вид накладной для печати на принтере.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Получаем общие данные заказа и имя клиента
    cursor.execute('''
        SELECT o.id, o.date_created, o.deadline, o.total_cost, o.order_status, c.name, c.phone
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.invoice_number = ?
    ''', (invoice_number,))
    
    order = cursor.fetchone()
    if not order:
        conn.close()
        return "Накладная не найдена."
        
    order_id, date_created, deadline, total_cost, status, cust_name, cust_phone = order
    
    # 2. Получаем все позиции внутри этого заказа
    cursor.execute('''
        SELECT p.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    
    items = cursor.fetchall()
    conn.close()
    
    # 3. Собираем текстовый шаблон накладной (чек)
    lines = []
    lines.append("=========================================")
    lines.append("           MUSTAFAYEV FACTORY            ")
    lines.append("             Распильный цех              ")
    lines.append("=========================================")
    lines.append(f"НАКЛАДНАЯ: {invoice_number}")
    lines.append(f"Дата создания: {date_created}")
    lines.append(f"Обещанный срок: {deadline}")
    lines.append("-----------------------------------------")
    lines.append(f"Клиент: {cust_name}")
    lines.append(f"Телефон: {cust_phone}")
    lines.append("-----------------------------------------")
    lines.append("Наименование          Кол-во     Сумма  ")
    lines.append("-----------------------------------------")
    
    for name, qty, price in items:
        item_total = qty * price
        # Ограничиваем длину названия для красивого выравнивания в чеке
        short_name = name[:20].ljust(20)
        lines.append(f"{short_name}  {qty:<6}  {item_total:<10.0f}")
        
    lines.append("-----------------------------------------")
    lines.append(f"ИТОГО К ОПЛАТЕ: {total_cost:.0f} сум")
    lines.append(f"Статус заказа: {status.upper()}")
    lines.append("=========================================")
    lines.append("       Спасибо за заказ! Проверяйте      ")
    lines.append("      комплектацию деталей на месте.     ")
    lines.append("=========================================\n")
    
    return "\n".join(lines)
