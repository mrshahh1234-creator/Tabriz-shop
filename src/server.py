from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import products
import customers
import sales

app = FastAPI(title="Mustafayev Factory API", description="API для управления распильным цехом")

# --- Схемы данных (какие данные сервер ожидает получить от телефона) ---
class ItemInOrder(BaseModel):
    product_id: int
    qty: float
    price: float

class OrderCreateSchema(BaseModel):
    customer_id: int
    items: List[ItemInOrder]
    deadline: str  # <--- ДОБАВИТЬ ЭТУ СТРОКУ (Формат: YYYY-MM-DD HH:MM:SS)

class OrderPaySchema(BaseModel):
    order_id: int
    payment_type: str  # 'cash' или 'debt'

# --- 1. Эндпоинты для товаров и поиска ---
@app.get("/products/search")
def search_materials(q: str = None, thickness: int = None, category_id: int = None):
    """Поиск материалов на складе через телефон"""
    results = products.search_products(search_query=q, thickness=thickness, category_id=category_id)
    # Форматируем в удобный для Flutter JSON-список
    return [
        {
            "id": r[0], "category": r[1], "name": r[2], 
            "thickness": r[3], "price": r[4], "stock": r[5], "reserved": r[6]
        } for r in results
    ]

@app.get("/products/top-sellers")
def get_hits():
    """Получить хит продаж в приложении"""
    hits = products.get_top_sellers()
    return [{"id": h[0], "name": h[1], "sales_count": h[2], "stock": h[3]} for h in hits]


# --- 2. Эндпоинты для клиентов и долгов ---
@app.get("/customers/debtors")
def get_debtors():
    """Показать список всех должников на экране телефона"""
    debtors = customers.get_debtors_list()
    return [{"id=d": d[0], "name": d[1], "phone": d[2], "debt": d[3]} for d in debtors]

@app.get("/customers/{customer_id}/balance")
def get_balance(customer_id: int):
    """Проверить баланс конкретного мебельщика"""
    return {"status": customers.get_customer_balance(customer_id)}


# --- 3. Эндпоинты для продаж, брони и возвратов ---
@app.post("/orders/create")
def create_new_order(order_data: OrderCreateSchema):
    """Создать заказ и занять товар (Бронь под раскрой)"""
    # Превращаем данные из формата мобилки в обычный список словарей для нашего sales.py
    items_list = [{"product_id": i.product_id, "qty": i.qty, "price": i.price} for i in order_data.items]
    result = sales.create_order_with_deadline(
    customer_id=order_data.customer_id, 
    items=items_list, 
    deadline_str=order_data.deadline  # <--- ПЕРЕДАЕМ ДЕДЛАЙН В НАШУ НОВУЮ ФУНКЦИЮ
    
    if "Ошибка" in result or "Недостаточно" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}

@app.post("/orders/pay")
def pay_order(pay_data: OrderPaySchema):
    """Выдать заказ и оформить продажу (в том числе в долг)"""
    result = sales.complete_and_pay_order(pay_data.order_id, pay_data.payment_type)
    if "Ошибка" in result or "не найден" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}

@app.post("/orders/{order_id}/return")
def return_order(order_id: int):
    """Оформить возврат через приложение"""
    result = sales.process_return(order_id)
    if "Ошибка" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}
    # --- ДОБАВИТЬ В САМЫЙ КОНЕЦ ФАЙЛА SERVER.PY ---

@app.get("/orders/check-overdue")
def check_overdue_orders():
    """
    Эндпоинт-будильник. Телефон будет запрашивать его раз в минуту, 
    чтобы выдать пуш-уведомление при срыве срока.
    """
    overdue_orders = sales.get_overdue_orders()
    return {
        "overdue_count": len(overdue_orders), 
        "orders": overdue_orders
    }
# Добавить в самый конец файла src/server.py

@app.post("/orders/{invoice_number}/ready")
def set_order_ready(invoice_number: str):
    """Вызывается при нажатии кнопки 'Готово' на планшете в цеху"""
    result = sales.mark_order_as_ready(invoice_number)
    if "Ошибка" in result or "не найден" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"status": "success", "message": result}
# Добавить в самый конец файла src/server.py

@app.get("/orders/{invoice_number}/print")
def get_print_invoice(invoice_number: str):
    """Возвращает чистый отформатированный текст накладной для отправки на принтер"""
    text = sales.get_invoice_print_text(invoice_number)
    if text == "Накладная не найдена.":
        raise HTTPException(status_code=404, detail=text)
    return {"invoice_text": text}
    // Функция внутри Flutter для отправки накладной на печать/просмотр
Future<void> printInvoice(String invoiceNumber) async {
  try {
    final response = await _dio.get('$baseUrl/orders/$invoiceNumber/print');
    String invoiceText = response.data['invoice_text'];

    // Показываем превью накладной прямо на экране телефона перед печатью
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Печать накладной'),
        content: SingleChildScrollView(
          child: Text(
            invoiceText, 
            style: const TextStyle(fontFamily: 'Courier', fontSize: 12), // Моноширинный шрифт для ровных колонок
          ),
        ),
        actions: [
          TextButton(
            child: const Text('Закрыть'),
            onPressed: () => Navigator.pop(context),
          ),
          ElevatedButton(
            child: const Text('Отправить на принтер'),
            onPressed: () {
              // Здесь вызывается системная печать Flutter (пакет 'printing')
            },
          ),
        ],
      ),
    );
  } catch (e) {
    print('Ошибка печати: $e');
  }
}
