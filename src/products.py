import sqlite3

DB_PATH = 'data/shop.db'

def add_category(name, cat_type):
    """
    Добавление категории.
    cat_type может быть: 'sheet' (плиты), 'edge' (кромка), 'item' (фурнитура), 'service' (услуги)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, cat_type))
        conn.commit()
        return f"Категория '{name}' успешно добавлена."
    except sqlite3.IntegrityError:
        return f"Категория '{name}' уже существует."
    finally:
        conn.close()


def add_product(category_id, name, thickness=0, price_sale=0.0, stock_qty=0.0):
    """
    Добавление нового материала или услуги на склад.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (category_id, name, thickness, price_sale, stock_qty)
            VALUES (?, ?, ?, ?, ?)
        ''', (category_id, name, thickness, price_sale, stock_qty))
        conn.commit()
        return f"Материал/услуга '{name}' успешно добавлен(а) на склад."
    except Exception as e:
        return f"Ошибка при добавлении: {e}"
    finally:
        conn.close()


def search_products(search_query=None, thickness=None, category_id=None):
    """
    Умный поиск по складу цеха.
    Можно искать по названию, фильтровать по толщине плиты или по категории.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Базовый SQL-запрос с объединением таблиц, чтобы видеть название категории
    query = '''
        SELECT p.id, c.name, p.name, p.thickness, p.price_sale, p.stock_qty, p.reserved_qty 
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []
    
    # Фильтр по тексту (название декора, бренда и т.д.)
    if search_query:
        query += " AND p.name LIKE ?"
        params.append(f"%{search_query}%")
        
    # Фильтр по толщине (актуально для ЛДСП/МДФ)
    if thickness:
        query += " AND p.thickness = ?"
        params.append(thickness)
        
    # Фильтр по конкретной категории
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
        
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return results


def get_top_sellers(limit=5):
    """
    Хит продаж: выводит топ материалов, которых было продано/распилено больше всего.
    Использует поле sales_count, которое обновляется при выдаче заказов.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.sales_count, p.stock_qty
        FROM products p
        WHERE p.sales_count > 0
        ORDER BY p.sales_count DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    return results
