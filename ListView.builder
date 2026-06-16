import 'package:http/http.dart' as http;
import 'dart:convert';

// Функция получения должников с нашего Python-сервера
Future<List<dynamic>> fetchDebtors() async {
  final response = await http.get(Uri.parse('http://твой_IP_компьютера:8000/customers/debtors'));

  if (response.statusCode == 200) {
    return jsonDecode(response.body); // Получаем готовый массив должников
  } else {
    throw Exception('Не удалось загрузить список должников');
  }
}
