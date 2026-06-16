import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

class WorkshopScreen extends StatefulWidget {
  const WorkshopScreen({Key? key}) : super(key: key);

  @override
  _WorkshopScreenState createState() => _WorkshopScreenState();
}

class _WorkshopScreenState extends State<WorkshopScreen> {
  final Dio _dio = Dio();
  final String baseUrl = 'http://твой_IP_компьютера:8000';
  List<dynamic> _activeOrders = [];

  @override
  void initState() {
    super.initState();
    _loadQueue(); // Загружаем очередь при старте
  }

  // Получаем список текущих заказов в очереди
  Future<void> _loadQueue() async {
    try {
      final response = await _dio.get('$baseUrl/orders/check-overdue');
      setState(() {
        _activeOrders = response.data['orders'];
      });
    } catch (e) {
      print("Ошибка загрузки очереди: $e");
    }
  }

  // Кнопка "Готово" отправляет запрос на сервер
  Future<void> _completeOrder(String invoice) async {
    try {
      final response = await _dio.post('$baseUrl/orders/$invoice/ready');
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Накладная $invoice готова!'), backgroundColor: Colors.green),
        );
        _loadQueue(); // Обновляем список, заказ исчезнет из очереди активных
      }
    } catch (e) {
      print("Ошибка изменения статуса: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Монитор распиловщика (Очередь)'),
        backgroundColor: Colors.grey[900], // Строгий темный цвет для цеха
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadQueue),
        ],
      ),
      body: _activeOrders.isEmpty
          ? const Center(child: Text('Все заказы распилены! Очередь пуста.', style: TextStyle(fontSize: 18)))
          : ListView.builder(
              itemCount: _activeOrders.length,
              itemBuilder: (context, index) {
                final order = _activeOrders[index];
                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.between,
                      children: [
                        // Информация о заказе
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Накладная: ${order['invoice']}',
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 5),
                            Text('Мастер: ${order['customer_name']}', style: const TextStyle(fontSize: 16)),
                            Text('Срок до: ${order['deadline']}', style: const TextStyle(color: Colors.red)),
                          ],
                        ),
                        // Большая удобная кнопка для мастера
                        ElevatedButton.icon(
                          icon: const Icon(Icons.check_circle, color: Colors.white),
                          label: const Text('ГОТОВО', style: TextStyle(fontSize: 16, color: Colors.white)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green[700],
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                          ),
                          onPressed: () => _completeOrder(order['invoice']),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
