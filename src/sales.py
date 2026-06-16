import sqlite3
from datetime import datetime

DB_PATH = 'data/shop.db'

def create_order(customer_id, items):
    """
    Шаг 1: Создание заказа и БРОНИРОВАНИЕ материалов (Занятый товар).
    items - список словарей: [{'product_id': 1, 'qty': 5, 'price': 2500}]
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Считаем общую стоимость заказа
        total_cost = sum(item['qty'] * item['price'] for item in items)
        
        # Проверяем, хватает ли свободного материала на складе для брони
        for item in items:
            cursor.execute("SELECT name, stock_qty FROM products WHERE id = ?", (item['product_id'],))
            prod = cursor.fetchone()
            if not prod:
                return f"Товар с ID {item['product_id']} не найден."
            
            name, stock_qty = prod
            if stock_qty < item['qty']:
                return f"Недостаточно материала '{name}' на складе! Доступно: {stock_qty}, требуется: {item['qty']}."

        # Создаем заказ со статусом 'pending' (в очереди / забронирован)
        cursor.execute('''
            INSERT INTO orders (customer_id, total_cost, order_status, payment_status)
            VALUES (?, ?, 'pending', 'unpaid')
        ''', (customer_id, total_cost))
        
        order_id = cursor.lastrowid

        # Добавляем позиции в заказ и перемещаем их в "reserved_qty" (занято)
        for item in items:
            # Записываем в детали заказа
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['qty'], item['price']))
            
            # Переносим из свободного остатка в бронь
            cursor.execute('''
                UPDATE products 
                SET stock_qty = stock_qty - ?, 
                    reserved_qty = reserved_qty + ? 
                WHERE id = ?
            ''', (item['qty'], item['qty'], item['product_id']))

        conn.commit()
        return f"Заказ №{order_id} успешно создан. Материалы заняты (забронированы)."
    
    except Exception as e:
        conn.rollback()
        return f"Ошибка при создании заказа: {e}"
    finally:
        conn.close()


def complete_and_pay_order(order_id, payment_type, amount_paid=0.0):
    """
    Шаг 2: Выдача заказа и оплата (Продажа / Продажа в долг).
    payment_type может быть: 'cash' (наличные/карта), 'debt' (в долг)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем данные о заказе
        cursor.execute("SELECT customer_id, total_cost, order_status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return "Заказ не найден."
        
        customer_id, total_cost, current_status = order
        
        if current_status == 'completed':
            return "Этот заказ уже был выдан и оплачен."

        # Получаем все товары в этом заказе, чтобы списать их из брони
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
        items = cursor.fetchall()

        # Окончательно списываем из брони и добавляем в счетчик продаж (для Хита продаж)
        for prod_id, qty in items:
            cursor.execute('''
                UPDATE products 
                SET reserved_qty = reserved_qty - ?,
                    sales_count = sales_count + ?
                WHERE id = ?
            ''', (qty, qty, prod_id))

        # Логика оплаты и ДОЛГА
        if payment_type == 'debt':
            # Если в долг — вся сумма заказа записывается в минус клиенту
            cursor.execute('''
                UPDATE customers 
                SET debt_amount = debt_amount + ? 
                WHERE id = ?
            ''', (total_cost, customer_id))
            pay_status = 'debt'
        else:
            # Обычная оплата
            pay_status = 'paid'

        # Обновляем статус заказа на "Выдан/Завершен"
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'completed', payment_status = ? 
            WHERE id = ?
        ''', (pay_status, order_id))

        conn.commit()
        return f"Заказ №{order_id} успешно выдан. Склад и баланс клиента обновлены."
    
    except Exception as e:
        conn.rollback()
        return f"Ошибка при завершении заказа: {e}"
    finally:
        conn.close()


def process_return(order_id):
    """
    Шаг 3: Возврат товара.
    Возвращает материалы на склад и корректирует долг клиента, если заказ был в долг.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT customer_id, total_cost, order_status, payment_status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return "Заказ не найден."
        
        customer_id, total_cost, order_status, payment_status = order
        
        if order_status == 'returned':
            return "Этот заказ уже был возвращен."
        if order_status != 'completed':
            return "Нельзя сделать возврат невыданного заказа. Его можно просто отменить."

        # Получаем товары для возврата на склад
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
        items = cursor.fetchall()

        # Возвращаем товар на свободный склад и вычитаем из статистики продаж
        for prod_id, qty in items:
            cursor.execute('''
                UPDATE products 
                SET stock_qty = stock_qty + ?,
                    sales_count = sales_count - ?
                WHERE id = ?
            ''', (qty, qty, prod_id))

        # Если заказ был оформлен в долг, списываем этот долг с клиента
        if payment_status == 'debt':
            cursor.execute('''
                UPDATE customers 
                SET debt_amount = debt_amount - ? 
                WHERE id = ?
            ''', (total_cost, customer_id))

        # Меняем статус заказа на "Возврат"
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'returned' 
            WHERE id = ?
        ''', (order_id,))

        conn.commit()
        return f"Возврат по заказу №{order_id} успешно оформлен. Материалы вернулись на склад."
    
    except Exception as e:
        conn.rollback()
        return f"Ошибка при оформлении возврата: {e}"
    finally:
        conn.close()
