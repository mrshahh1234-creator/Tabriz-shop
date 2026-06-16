import 'package:flutter/material.dart';
import '../services/api_service.dart';

class OrderScreen extends StatefulWidget {
  const OrderScreen({Key? key}) : super(key: key);

  @override
  _OrderScreenState createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  final ApiService _apiService = ApiService();
  
  // В реальном приложении эти данные будут выбираться из списков
  int _selectedCustomerId = 1; // ID выбранного мебельщика
  List<Map<String, dynamic>> _cartItems = []; // Наша корзина раскроя

  void _addToCart(int productId, String name, double qty, double price) {
    setState(() {
      _cartItems.add({
        'product_id': productId,
        'name': name,
        'qty': qty,
        'price': price,
      });
    });
  }

  void _submitOrder() async {
    if (_cartItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Корзина пуста! Добавьте материалы.')),
      );
      return;
    }

    // Форматируем данные под требования нашего Python-API
    List<Map<String, dynamic>> itemsToSend = _cartItems.map((item) => {
      'product_id': item['product_id'],
      'qty': item['qty'],
      'price': item['price'],
    }).toList();

    bool success = await _apiService.createOrder(_selectedCustomerId, itemsToSend);

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Заказ создан! Материалы успешно забронированы.')),
      );
      setState(() {
        _cartItems.clear(); // Очищаем корзину после успеха
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ошибка! Проверьте остатки на складе.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    double totalAmount = _cartItems.fold(0, (sum, item) => sum + (item['qty'] * item['price']));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Новый заказ / Раскрой'),
        backgroundColor: Colors.brown[800],
      ),
      body: Column(
        children: [
          // Симуляция выбора клиента и быстрого добавления
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: ElevatedButton.icon(
              icon: const Icon(Icons.add_box),
              label: const Text('Демо-добавление: ЛДСП Белый (5 листов)'),
              onPressed: () => _addToCart(1, 'ЛДСП Белый 16мм', 5, 250000),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.grey[300], foregroundColor: Colors.black),
            ),
          ),
          
          const Divider(),
          const Text('СОСТАВ ЗАКАЗА:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          
          Expanded(
            child: _cartItems.isEmpty
                ? const Center(child: Text('Добавьте материалы или услуги в заказ'))
                : ListView.builder(
                    itemCount: _cartItems.length,
                    itemBuilder: (context, index) {
                      final item = _cartItems[index];
                      return ListTile(
                        leading: const Icon(Icons.layers, color: Colors.brown),
                        title: Text(item['name']),
                        subtitle: Text('${item['qty']} шт/метр х ${item['price']} сум'),
                        trailing: Text('${item['qty'] * item['price']} сум', style: const TextStyle(fontWeight: FontWeight.bold)),
                      );
                    },
                  ),
          ),
          
          // НИЖНЯЯ ПАНЕЛЬ С ИТОГОМ
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Colors.white, boxShadow: [BoxShadow(color: Colors.grey[300]!, blurRadius: 10)]),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.between,
                  children: [
                    const Text('Итого к оплате/брони:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    Text('$totalAmount сум', style: const TextStyle(fontSize: 18, color: Colors.green, fontWeight: FontWeight.bold)),
                  ],
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _submitOrder,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.brown[700]),
                    child: const Text('ЗАФИКСИРОВАТЬ И ЗАНЯТЬ ТОВАР', style: TextStyle(fontSize: 16, color: Colors.white)),
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}
