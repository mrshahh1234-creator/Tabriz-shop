import sqlite3

DB_PATH = 'data/shop.db'

def add_customer(name, phone):
    """
    Регистрация нового клиента (мастера или мебельного цеха).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO customers (name, phone)
            VALUES (?, ?)
        ''', (name, phone))
        conn.commit()
        return f"Клиент '{name}' успешно зарегистрирован."
    except sqlite3.IntegrityError:
        return f"Клиент с номером телефона {phone} уже существует в базе."
    except Exception as e:
        return f"Ошибка при добавлении клиента: {e}"
    finally:
        conn.close()


def get_customer_balance(customer_id):
    """
    Проверить текущий баланс долга конкретного клиента.
    Если значение > 0 — клиент должен цеху.
    Если значение < 0 — у клиента переплата (аванс).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, phone, debt_amount FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    
    if customer:
        name, phone, debt = customer
        if debt > 0:
            return f"Клиент: {name} ({phone}). Долг перед цехом: {debt} сум."
        elif debt < 0:
            return f"Клиент: {name} ({phone}). На счету аванс: {abs(debt)} сум."
        else:
            return f"Клиент: {name} ({phone}). Задолженностей нет."
    return "Клиент не найден."


def get_debtors_list():
    """
    Вывести список всех мебельщиков, у которых есть активный долг перед цехом.
    Сортирует список от самых больших долгов к меньшим.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Выбираем только тех, у кого долг больше нуля
    cursor.execute('''
        SELECT id, name, phone, debt_amount 
        FROM customers 
        WHERE debt_amount > 0 
        ORDER BY debt_amount DESC
    ''')
    
    debtors = cursor.fetchall()
    conn.close()
    return debtors


def pay_off_debt(customer_id, amount):
    """
    Внесение оплаты в счет погашения долга.
    Когда мастер приносит деньги за прошлые заказы.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Уменьшаем сумму долга клиента
        cursor.execute('''
            UPDATE customers 
            SET debt_amount = debt_amount - ? 
            WHERE id = ?
        ''', (amount, customer_id))
        
        conn.commit()
        
        # Получаем обновленный баланс для подтверждения
        cursor.execute("SELECT name, debt_amount FROM customers WHERE id = ?", (customer_id,))
        name, current_debt = cursor.fetchone()
        
        return f"Оплата {amount} сум принята от {name}. Текущий остаток долга: {current_debt} сум."
    except Exception as e:
        return f"Ошибка при проведении оплаты: {e}"
    finally:
        conn.close()
